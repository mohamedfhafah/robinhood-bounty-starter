#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import autogen

from context_loader import build_manager_message, load_agents_md_excerpt, load_campaign_context
from team_builder import (
    build_commander_proxy,
    build_exec_agent,
    build_llm_config,
    build_orchestrator_and_specialists,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run manager-driven AG2 team aligned with AGENTS.md")
    parser.add_argument(
        "--campaign",
        default="../output/campaign_20260217_205128",
        help="Path to campaign output directory",
    )
    parser.add_argument(
        "--agents-md",
        default="../../AGENTS.md",
        help="Path to AGENTS.md",
    )
    parser.add_argument(
        "--task",
        default="Analyze current evidence and provide next steps.",
        help="User request sent to the orchestrator",
    )
    parser.add_argument(
        "--max-round",
        type=int,
        default=10,
        help="Maximum group chat rounds",
    )
    parser.add_argument(
        "--speaker-selection",
        choices=["auto", "round_robin", "random", "manual"],
        default="auto",
        help="Group chat speaker selection strategy",
    )
    parser.add_argument(
        "--out",
        default="./runs/latest_transcript.json",
        help="Output transcript JSON file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print assembled context and team config without model calls",
    )
    parser.add_argument(
        "--env-file",
        default="",
        help="Optional .env file to load before building model config",
    )
    parser.add_argument(
        "--allow-exec",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Allow ExecAgent to execute code blocks in local workspace",
    )
    return parser.parse_args()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        raise FileNotFoundError(f".env file not found: {env_path}")

    for raw_line in env_path.read_text(errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        os.environ[key] = value


def _normalize_content(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if isinstance(item, dict):
                if "text" in item:
                    chunks.append(str(item["text"]))
                elif "content" in item:
                    chunks.append(str(item["content"]))
                else:
                    chunks.append(json.dumps(item, ensure_ascii=False))
            else:
                chunks.append(str(item))
        return "\n".join(chunks)
    return str(content)


def _strip_terminate(text: str) -> str:
    cleaned = text.strip()
    token = "TERMINATE"
    if cleaned.endswith(token):
        cleaned = cleaned[: -len(token)].rstrip()
    return cleaned


def _extract_final_text(messages: list[dict[str, Any]]) -> str:
    for msg in reversed(messages):
        name = str(msg.get("name", "")).strip()
        content = _normalize_content(msg.get("content"))
        if name == "Orchestrator" and content.strip():
            return _strip_terminate(content)

    # Fallback: if Orchestrator is blank, return the latest useful specialist output.
    for msg in reversed(messages):
        name = str(msg.get("name", "")).strip()
        if name in {"", "UserCommander"}:
            continue
        content = _normalize_content(msg.get("content"))
        if content.strip():
            return _strip_terminate(content)

    return ""


def _build_allowed_transitions(agents: list[Any], allow_exec: bool) -> dict[Any, list[Any]]:
    by_name = {a.name: a for a in agents}
    orchestrator = by_name.get("Orchestrator")
    if orchestrator is None:
        return {}

    specialist_names = [n for n in by_name.keys() if n not in {"Orchestrator", "ExecAgent"}]
    specialist_agents = [by_name[n] for n in specialist_names]

    transitions: dict[Any, list[Any]] = {
        orchestrator: specialist_agents.copy(),
    }

    if allow_exec and "ExecAgent" in by_name:
        exec_agent = by_name["ExecAgent"]
        transitions[orchestrator].append(exec_agent)
        transitions[exec_agent] = [orchestrator]

    for specialist in specialist_agents:
        transitions[specialist] = [orchestrator]

    return transitions


def _looks_like_local_ops_task(task: str) -> bool:
    t = task.lower()
    hints = [
        "open ",
        "launch ",
        "intellij",
        "vscode",
        "application",
        "app ",
        "finder",
        "terminal",
        "desktop",
        "local machine",
    ]
    return any(h in t for h in hints)


def main() -> int:
    args = parse_args()

    script_dir = Path(__file__).resolve().parent
    campaign_dir = (script_dir / args.campaign).resolve()
    agents_md_path = (script_dir / args.agents_md).resolve()
    out_path = (script_dir / args.out).resolve()

    if args.env_file:
        env_path = Path(args.env_file).expanduser()
        if str(env_path).startswith("@"):
            env_path = Path(str(env_path)[1:]).expanduser()
        if not env_path.is_absolute():
            env_path = (script_dir / env_path).resolve()
        load_env_file(env_path)

    campaign_context = load_campaign_context(campaign_dir)
    agents_excerpt = load_agents_md_excerpt(agents_md_path)
    initial_message = build_manager_message(args.task, campaign_context, agents_excerpt)

    if args.dry_run:
        local_ops_mode = _looks_like_local_ops_task(args.task)
        preview = {
            "campaign_dir": str(campaign_dir),
            "agents_md": str(agents_md_path),
            "task": args.task,
            "allow_exec": args.allow_exec,
            "local_ops_mode": local_ops_mode,
            "speaker_selection": args.speaker_selection,
            "max_round": args.max_round,
            "initial_message_preview": initial_message[:3500],
        }
        print(json.dumps(preview, indent=2))
        return 0

    llm_config = build_llm_config()
    orchestrator, specialists = build_orchestrator_and_specialists(llm_config)
    commander = build_commander_proxy()

    local_ops_mode = _looks_like_local_ops_task(args.task)
    if local_ops_mode:
        agents = [orchestrator]
    else:
        agents = [orchestrator, *specialists]

    if args.allow_exec:
        agents.append(build_exec_agent(str(script_dir)))

    transitions = _build_allowed_transitions(agents, args.allow_exec)

    effective_speaker_selection = args.speaker_selection
    effective_max_round = args.max_round
    if local_ops_mode:
        # Avoid extra selector-model calls and keep local ops short/direct.
        if effective_speaker_selection == "auto":
            effective_speaker_selection = "round_robin"
        effective_max_round = min(effective_max_round, 4)

    groupchat = autogen.GroupChat(
        agents=agents,
        messages=[],
        max_round=effective_max_round,
        func_call_filter=False,
        speaker_selection_method=effective_speaker_selection,
        allowed_or_disallowed_speaker_transitions=transitions,
        speaker_transitions_type="allowed",
    )
    manager = autogen.GroupChatManager(
        groupchat=groupchat,
        llm_config=llm_config,
        is_termination_msg=lambda msg: (
            str(msg.get("name", "")).strip() == "Orchestrator"
            and "TERMINATE" in str(msg.get("content", ""))
        ),
    )

    commander.initiate_chat(manager, message=initial_message)

    final_text = _extract_final_text(groupchat.messages)
    ensure_parent(out_path)
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "campaign_dir": str(campaign_dir),
        "agents_md": str(agents_md_path),
        "task": args.task,
        "max_round": effective_max_round,
        "speaker_selection": effective_speaker_selection,
        "allow_exec": args.allow_exec,
        "final_text": final_text,
        "messages": groupchat.messages,
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    if final_text:
        print(final_text)
    print(f"[+] wrote transcript: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
