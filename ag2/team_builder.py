from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from prompts import ORCHESTRATOR, SPECIALISTS

if TYPE_CHECKING:
    import autogen


def _load_autogen() -> Any:
    try:
        import autogen
    except ImportError as exc:
        raise RuntimeError(
            "AG2 runtime dependency missing. Install it with "
            "`python3 -m pip install -r ag2/requirements.txt`."
        ) from exc
    return autogen


def build_llm_config() -> dict[str, Any]:
    timeout = int(os.getenv("AG2_TIMEOUT", "120").strip() or "120")
    temperature = float(os.getenv("AG2_TEMPERATURE", "0").strip() or "0")

    config = _build_openai_or_google_config()

    llm_config: dict[str, Any] = {
        "config_list": [config],
        "temperature": temperature,
        "timeout": timeout,
    }
    return llm_config


def _build_openai_or_google_config() -> dict[str, Any]:
    # OpenAI-compatible mode (default if OPENAI_API_KEY is present).
    openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if openai_api_key:
        model = os.getenv("AG2_MODEL", "gpt-4.1-mini").strip() or "gpt-4.1-mini"
        base_url = os.getenv("OPENAI_BASE_URL", "").strip()
        config: dict[str, Any] = {"model": model, "api_key": openai_api_key}
        if base_url:
            config["base_url"] = base_url
        return config

    # Google Gemini/Vertex mode (aligned with user's ag2_google_setup).
    model = os.getenv("GOOGLE_GEMINI_MODEL", "").strip() or os.getenv("AG2_MODEL", "").strip() or "gemini-2.5-pro"
    google_api_key = os.getenv("GOOGLE_GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()
    google_project = os.getenv("GOOGLE_CLOUD_PROJECT", "").strip()
    google_location = os.getenv("GOOGLE_CLOUD_LOCATION", "").strip() or "us-central1"
    google_sa_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()

    if google_api_key and google_project:
        raise RuntimeError(
            "Both Google API-key mode and Vertex mode are set. Keep only one auth mode."
        )

    if google_api_key:
        return {
            "api_type": "google",
            "model": model,
            "api_key": google_api_key,
            "response_validation": False,
        }

    if google_project:
        cfg: dict[str, Any] = {
            "api_type": "google",
            "model": model,
            "project_id": google_project,
            "location": google_location,
            "response_validation": False,
        }
        if google_sa_path:
            cfg["google_application_credentials"] = google_sa_path
        return cfg

    raise RuntimeError(
        "No model auth found. Set OPENAI_API_KEY for OpenAI mode, or "
        "GOOGLE_GEMINI_API_KEY/GOOGLE_API_KEY (Gemini API-key mode), or "
        "GOOGLE_CLOUD_PROJECT (+ optional GOOGLE_APPLICATION_CREDENTIALS) for Vertex mode."
    )


def build_orchestrator_and_specialists(llm_config: dict[str, Any]) -> tuple[Any, list[Any]]:
    autogen = _load_autogen()
    orchestrator = autogen.AssistantAgent(
        name=ORCHESTRATOR.name,
        system_message=ORCHESTRATOR.system_message,
        llm_config=llm_config,
    )
    specialists: list[autogen.AssistantAgent] = []
    for p in SPECIALISTS:
        specialists.append(
            autogen.AssistantAgent(
                name=p.name,
                system_message=p.system_message,
                llm_config=llm_config,
            )
        )
    return orchestrator, specialists


def build_commander_proxy() -> Any:
    autogen = _load_autogen()
    return autogen.UserProxyAgent(
        name="UserCommander",
        is_termination_msg=lambda msg: (
            str(msg.get("name", "")).strip() == "Orchestrator"
            and "TERMINATE" in str(msg.get("content", ""))
        ),
        human_input_mode="NEVER",
        code_execution_config=False,
        llm_config=False,
    )


def build_exec_agent(work_dir: str) -> Any:
    autogen = _load_autogen()
    return autogen.UserProxyAgent(
        name="ExecAgent",
        human_input_mode="NEVER",
        llm_config=False,
        # This allows specialists/orchestrator to run shell/python snippets.
        code_execution_config={
            "work_dir": work_dir,
            "use_docker": False,
        },
        system_message=(
            "Execute received code blocks and return stdout/stderr. "
            "Do not add analysis."
        ),
    )
