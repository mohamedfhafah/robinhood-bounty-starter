#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, flash, redirect, render_template, request, url_for


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CAMPAIGN = str((BASE_DIR / "../output/campaign_20260217_205128").resolve())
DEFAULT_AGENTS_MD = str((BASE_DIR / "../../AGENTS.md").resolve())
DEFAULT_ENV_FILE = os.getenv("AG2_WEB_CHAT_ENV_FILE", "")
DEFAULT_MAX_ROUND = 8
DEFAULT_RUN_TIMEOUT = 480
MAX_LIVE_LOG_LINES = 800
AGENT_ORDER = [
    "Orchestrator",
    "ScopeGuardian",
    "ReconAgent",
    "VulnResearchAgent",
    "ExploitationAgent",
    "ReportingAgent",
    "IntelligenceAgent",
    "ExecAgent",
]
AGENT_LABELS = {
    "Orchestrator": "Manager",
    "ScopeGuardian": "ScopeGuardian",
    "ReconAgent": "ReconAgent",
    "VulnResearchAgent": "VulnResearchAgent",
    "ExploitationAgent": "ExploitationAgent",
    "ReportingAgent": "ReportingAgent",
    "IntelligenceAgent": "IntelligenceAgent",
    "ExecAgent": "ExecAgent",
}
SPEAKER_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_]*) \(to chat_manager\):")

app = Flask(
    __name__,
    template_folder=str((BASE_DIR / "templates").resolve()),
)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me-in-production")

_LOCK = threading.Lock()
_STATE: dict[str, Any] = {
    "history": [],
    "last_run": None,
    "running": False,
    "job": None,
    "live_log": [],
    "active_agent": None,
    "agent_statuses": {name: "idle" for name in AGENT_ORDER},
    "run_pid": None,
    "run_started": None,
    "settings": {
        "campaign": DEFAULT_CAMPAIGN,
        "agents_md": DEFAULT_AGENTS_MD,
        "env_file": DEFAULT_ENV_FILE,
        "max_round": DEFAULT_MAX_ROUND,
        "run_timeout": DEFAULT_RUN_TIMEOUT,
        "speaker_selection": "auto",
        "allow_exec": True,
    },
}


def _now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _init_agent_statuses_locked(allow_exec: bool) -> None:
    statuses: dict[str, str] = {}
    for agent in AGENT_ORDER:
        if agent == "ExecAgent" and not allow_exec:
            statuses[agent] = "disabled"
        else:
            statuses[agent] = "idle"
    _STATE["agent_statuses"] = statuses
    _STATE["active_agent"] = None


def _set_agent_active_locked(agent: str) -> None:
    statuses: dict[str, str] = _STATE.get("agent_statuses", {})
    if agent not in statuses:
        return
    if statuses.get(agent) == "disabled":
        return

    prev = _STATE.get("active_agent")
    if isinstance(prev, str) and prev in statuses and prev != agent and statuses.get(prev) == "active":
        statuses[prev] = "done"

    statuses[agent] = "active"
    _STATE["active_agent"] = agent


def _set_active_done_locked() -> None:
    statuses: dict[str, str] = _STATE.get("agent_statuses", {})
    active = _STATE.get("active_agent")
    if isinstance(active, str) and active in statuses and statuses.get(active) == "active":
        statuses[active] = "done"
    _STATE["active_agent"] = None


def _set_active_error_locked() -> None:
    statuses: dict[str, str] = _STATE.get("agent_statuses", {})
    active = _STATE.get("active_agent")
    if isinstance(active, str) and active in statuses and statuses.get(active) != "disabled":
        statuses[active] = "error"
    _STATE["active_agent"] = None


def _update_agent_state_from_log_locked(line: str) -> None:
    s = line.strip()
    if not s:
        return

    if "Next speaker:" in s:
        agent = s.split("Next speaker:", 1)[1].strip()
        if agent in AGENT_ORDER:
            _set_agent_active_locked(agent)
        return

    m = SPEAKER_RE.match(s)
    if m:
        agent = m.group(1).strip()
        if agent in AGENT_ORDER:
            _set_agent_active_locked(agent)
        return

    if "TERMINATING RUN" in s:
        _set_active_done_locked()


def _agent_items_for_view(settings: dict[str, Any], running: bool) -> list[dict[str, str]]:
    allow_exec = bool(settings.get("allow_exec", True))
    statuses = _STATE.get("agent_statuses", {}) if isinstance(_STATE.get("agent_statuses"), dict) else {}
    items: list[dict[str, str]] = []
    for agent in AGENT_ORDER:
        if agent == "ExecAgent" and not allow_exec:
            status = "disabled"
        else:
            status = str(statuses.get(agent, "idle"))
        if not running and status == "active":
            status = "done"
        items.append(
            {
                "id": agent,
                "label": AGENT_LABELS.get(agent, agent),
                "status": status,
            }
        )
    return items


def _append_live(line: str) -> None:
    if not line:
        return
    ts = datetime.now().strftime("%H:%M:%S")
    with _LOCK:
        _update_agent_state_from_log_locked(line)
        _STATE["live_log"].append(f"[{ts}] {line}")
        if len(_STATE["live_log"]) > MAX_LIVE_LOG_LINES:
            _STATE["live_log"] = _STATE["live_log"][-MAX_LIVE_LOG_LINES:]


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


def _extract_manager_messages(transcript_path: Path) -> list[dict[str, str]]:
    payload = json.loads(transcript_path.read_text(errors="replace"))
    final_text = _normalize_content(payload.get("final_text"))
    if final_text.strip():
        return [{"sender": "Manager", "role": "assistant", "content": final_text.strip()}]

    messages = payload.get("messages", [])
    for msg in reversed(messages):
        if str(msg.get("name", "")).strip() != "Orchestrator":
            continue
        content = _normalize_content(msg.get("content")).strip()
        if content:
            return [{"sender": "Manager", "role": "assistant", "content": content}]

    # Fallback for model runs where Orchestrator content is empty.
    for msg in reversed(messages):
        name = str(msg.get("name", "")).strip()
        if name in {"", "UserCommander"}:
            continue
        content = _normalize_content(msg.get("content")).strip()
        if content:
            return [{"sender": "Manager", "role": "assistant", "content": content}]

    return [{"sender": "Manager", "role": "assistant", "content": "(No manager response)"}]


def _tail_live_log(n: int = 80) -> str:
    with _LOCK:
        lines = list(_STATE["live_log"])[-n:]
    return "\n".join(lines)


def _pump_stdout(proc: subprocess.Popen[str]) -> None:
    if proc.stdout is None:
        return
    for raw in iter(proc.stdout.readline, ""):
        if raw == "":
            break
        line = raw.rstrip()
        if _should_keep_log_line(line):
            _append_live(line)


def _is_quota_error(raw_lines: list[str]) -> bool:
    txt = "\n".join(raw_lines).lower()
    signals = [
        "toomanyrequests",
        "resource exhausted",
        "google.api_core.exceptions.toomanyrequests",
        "429 post",
        "error-code-429",
    ]
    return any(s in txt for s in signals)


def _should_keep_log_line(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if s.startswith("$ "):
        return True

    key_snippets = [
        "Next speaker:",
        "TERMINATING RUN",
        "EXECUTING CODE BLOCK",
        "exitcode:",
        "Code output",
        "wrote transcript:",
        "worker-error",
        "timeout",
        "ResponseValidationError",
        "Finish message:",
    ]
    for snippet in key_snippets:
        if snippet in s:
            return True

    speaker_tags = [
        "Orchestrator (to chat_manager):",
        "ScopeGuardian (to chat_manager):",
        "ReconAgent (to chat_manager):",
        "VulnResearchAgent (to chat_manager):",
        "ExploitationAgent (to chat_manager):",
        "ReportingAgent (to chat_manager):",
        "IntelligenceAgent (to chat_manager):",
        "ExecAgent (to chat_manager):",
    ]
    for tag in speaker_tags:
        if s.startswith(tag):
            return True

    # Drop verbose context dumps by default.
    return False


def _run_team_streaming(
    task: str,
    campaign: str,
    agents_md: str,
    env_file: str,
    max_round: int,
    speaker_selection: str,
    allow_exec: bool,
    run_timeout: int,
) -> dict[str, Any]:
    runs_dir = BASE_DIR / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    out_file = runs_dir / f"gui_run_{_now_stamp()}.json"

    cmd = [
        sys.executable,
        "run_team.py",
        "--campaign",
        campaign,
        "--agents-md",
        agents_md,
        "--task",
        task,
        "--max-round",
        str(max_round),
        "--speaker-selection",
        speaker_selection,
        "--out",
        str(out_file),
    ]
    cmd.append("--allow-exec" if allow_exec else "--no-allow-exec")
    if env_file.strip():
        cmd.extend(["--env-file", env_file.strip()])

    _append_live("$ " + " ".join(cmd))

    def run_once(extra_env: dict[str, str] | None = None) -> tuple[int, bool, list[str]]:
        env = os.environ.copy()
        if extra_env:
            env.update(extra_env)

        proc = subprocess.Popen(
            cmd,
            cwd=BASE_DIR,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
        )
        raw_lines: list[str] = []

        with _LOCK:
            _STATE["run_pid"] = proc.pid
            _STATE["run_started"] = time.time()

        def pump_stdout_with_buffer() -> None:
            if proc.stdout is None:
                return
            for raw in iter(proc.stdout.readline, ""):
                if raw == "":
                    break
                line = raw.rstrip()
                raw_lines.append(line)
                if len(raw_lines) > 1500:
                    del raw_lines[:500]
                if _should_keep_log_line(line):
                    _append_live(line)

        pump = threading.Thread(target=pump_stdout_with_buffer, daemon=True)
        pump.start()

        timed_out = False
        try:
            return_code = proc.wait(timeout=run_timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            _append_live(f"[timeout] run exceeded {run_timeout}s, killing pid={proc.pid}")
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            return_code = proc.wait()

        pump.join(timeout=2)

        with _LOCK:
            _STATE["run_pid"] = None
            _STATE["run_started"] = None

        return return_code, timed_out, raw_lines

    return_code, timed_out, raw_lines = run_once()
    raw_tail = "\n".join(raw_lines[-120:])

    if timed_out:
        return {
            "ok": False,
            "error": f"run_team timeout after {run_timeout}s",
            "out_file": str(out_file),
            "raw_tail": raw_tail,
        }

    if return_code != 0 and _is_quota_error(raw_lines):
        _append_live("[retry] quota 429 detected, retrying once with gemini-2.5-flash")
        return_code, timed_out, raw_lines = run_once(
            {
                "GOOGLE_GEMINI_MODEL": "gemini-2.5-flash",
                "AG2_MODEL": "gemini-2.5-flash",
            }
        )
        raw_tail = "\n".join(raw_lines[-120:])

    if timed_out:
        return {
            "ok": False,
            "error": f"run_team timeout after retry ({run_timeout}s)",
            "out_file": str(out_file),
            "raw_tail": raw_tail,
        }

    if return_code != 0:
        if _is_quota_error(raw_lines):
            return {
                "ok": False,
                "error": (
                    "Model quota exceeded (Google Vertex/Gemini 429) even after fallback retry. "
                    "Retry in a few minutes or lower traffic."
                ),
                "out_file": str(out_file),
                "raw_tail": raw_tail,
            }
        return {
            "ok": False,
            "error": f"run_team.py failed (exit {return_code})",
            "out_file": str(out_file),
            "raw_tail": raw_tail,
        }

    if not out_file.exists():
        return {
            "ok": False,
            "error": "run finished but transcript file was not created",
            "out_file": str(out_file),
        }

    messages = _extract_manager_messages(out_file)
    return {"ok": True, "messages": messages, "out_file": str(out_file)}


def _start_background_run(
    task: str,
    campaign: str,
    agents_md: str,
    env_file: str,
    max_round: int,
    speaker_selection: str,
    allow_exec: bool,
    run_timeout: int,
) -> None:
    def worker() -> None:
        done_log = False
        try:
            result = _run_team_streaming(
                task=task,
                campaign=campaign,
                agents_md=agents_md,
                env_file=env_file,
                max_round=max_round,
                speaker_selection=speaker_selection,
                allow_exec=allow_exec,
                run_timeout=run_timeout,
            )
        except Exception as exc:  # noqa: BLE001
            _append_live(f"[worker-error] {exc}")
            result = {
                "ok": False,
                "error": f"Unexpected GUI worker error: {exc}",
                "out_file": "",
            }

        with _LOCK:
            _STATE["running"] = False
            if result["ok"]:
                _set_active_done_locked()
                _STATE["history"].extend(result["messages"])
                _STATE["last_run"] = {
                    "out_file": result["out_file"],
                    "ts": datetime.now().isoformat(timespec="seconds"),
                }
                _STATE["job"] = {
                    "status": "done",
                    "message": f"Run termine. Transcript: {result['out_file']}",
                }
                done_log = True
            else:
                tail_lines = "\n".join(_STATE["live_log"][-80:])
                raw_tail = str(result.get("raw_tail", "")).strip()
                if raw_tail:
                    tail_lines = f"{tail_lines}\n\nRaw error tail:\n{raw_tail}"
                _STATE["history"].append(
                    {
                        "sender": "System",
                        "role": "system",
                        "content": f"{result['error']}\n\nLOG tail:\n{tail_lines}",
                    }
                )
                _set_active_error_locked()
                _STATE["job"] = {
                    "status": "error",
                    "message": f"Echec du run: {result['error']}",
                }
        if done_log:
            _append_live("[done] run completed")

    threading.Thread(target=worker, daemon=True).start()


@app.route("/", methods=["GET"])
def index():
    with _LOCK:
        history = list(_STATE["history"])
        settings = dict(_STATE["settings"])
        last_run = _STATE["last_run"]
        running = bool(_STATE["running"])
        job = _STATE["job"]
        live_log = "\n".join(_STATE["live_log"])
        run_pid = _STATE["run_pid"]
        run_started = _STATE["run_started"]
        agent_items = _agent_items_for_view(settings, running)

    elapsed = None
    if running and run_started:
        elapsed = int(max(0, time.time() - float(run_started)))

    return render_template(
        "chat.html",
        history=history,
        settings=settings,
        last_run=last_run,
        running=running,
        job=job,
        live_log=live_log,
        run_pid=run_pid,
        elapsed=elapsed,
        agent_items=agent_items,
    )


@app.route("/send", methods=["POST"])
def send():
    task = request.form.get("task", "").strip()
    campaign = request.form.get("campaign", "").strip() or DEFAULT_CAMPAIGN
    agents_md = request.form.get("agents_md", "").strip() or DEFAULT_AGENTS_MD
    env_file = request.form.get("env_file", "").strip()
    if env_file.startswith("@"):
        env_file = env_file[1:]

    max_round_raw = request.form.get("max_round", str(DEFAULT_MAX_ROUND)).strip()
    timeout_raw = request.form.get("run_timeout", str(DEFAULT_RUN_TIMEOUT)).strip()
    speaker_selection = request.form.get("speaker_selection", "auto").strip()
    allow_exec = request.form.get("allow_exec", "") == "on"

    if not task:
        flash("Le message/prompt est requis.")
        return redirect(url_for("index"))

    try:
        max_round = int(max_round_raw)
        if max_round < 2:
            raise ValueError
    except ValueError:
        flash("max_round doit etre un entier >= 2.")
        return redirect(url_for("index"))

    try:
        run_timeout = int(timeout_raw)
        if run_timeout < 30:
            raise ValueError
    except ValueError:
        flash("run_timeout doit etre un entier >= 30 secondes.")
        return redirect(url_for("index"))

    with _LOCK:
        if _STATE["running"]:
            flash("Un run est deja en cours. Utilise Stop run ou attends la fin.")
            return redirect(url_for("index"))

        _STATE["settings"] = {
            "campaign": campaign,
            "agents_md": agents_md,
            "env_file": env_file,
            "max_round": max_round,
            "run_timeout": run_timeout,
            "speaker_selection": speaker_selection,
            "allow_exec": allow_exec,
        }
        _STATE["history"].append({"sender": "You", "role": "user", "content": task})
        _STATE["live_log"] = []
        _STATE["running"] = True
        _STATE["job"] = {"status": "running", "message": "Run en cours..."}
        _init_agent_statuses_locked(allow_exec)

    _start_background_run(
        task=task,
        campaign=campaign,
        agents_md=agents_md,
        env_file=env_file,
        max_round=max_round,
        speaker_selection=speaker_selection,
        allow_exec=allow_exec,
        run_timeout=run_timeout,
    )
    flash("Run lance. Tu peux suivre les logs en direct dans Live Activity.")
    return redirect(url_for("index"))


@app.route("/stop", methods=["POST"])
def stop():
    with _LOCK:
        if not _STATE["running"]:
            flash("Aucun run en cours.")
            return redirect(url_for("index"))
        pid = _STATE["run_pid"]

    if pid is None:
        flash("Run en cours mais PID introuvable. Attends quelques secondes.")
        return redirect(url_for("index"))

    try:
        os.kill(int(pid), signal.SIGTERM)
        _append_live(f"[stop] SIGTERM sent to pid={pid}")
        with _LOCK:
            _STATE["job"] = {"status": "running", "message": f"Stop envoye a pid={pid}..."}
        flash(f"Stop envoye a pid={pid}.")
    except ProcessLookupError:
        flash("Le process n'existe plus. Rafraichis la page.")
    except Exception as exc:  # noqa: BLE001
        flash(f"Erreur stop: {exc}")

    return redirect(url_for("index"))


@app.route("/reset", methods=["POST"])
def reset():
    with _LOCK:
        if _STATE["running"]:
            flash("Impossible de reset pendant un run en cours.")
            return redirect(url_for("index"))
        _STATE["history"] = []
        _STATE["last_run"] = None
        _STATE["job"] = None
        _STATE["live_log"] = []
        _STATE["run_pid"] = None
        _STATE["run_started"] = None
        _init_agent_statuses_locked(bool(_STATE.get("settings", {}).get("allow_exec", True)))
    flash("Historique vide.")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=False)
