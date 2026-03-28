from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _looks_like_local_ops_task(task: str) -> bool:
    t = task.lower()
    keywords = [
        "open ",
        "launch ",
        "intellij",
        "vscode",
        "application",
        "app ",
        "finder",
        "terminal",
        "desktop",
        "file",
        "folder",
    ]
    return any(k in t for k in keywords)


def _read_text(path: Path, max_chars: int = 20000) -> str:
    if not path.exists() or not path.is_file():
        return ""
    data = path.read_text(errors="replace")
    if len(data) > max_chars:
        return data[:max_chars] + "\n...<truncated>..."
    return data


def load_campaign_context(campaign_dir: Path) -> dict[str, Any]:
    ctx: dict[str, Any] = {
        "campaign_dir": str(campaign_dir.resolve()),
        "exists": campaign_dir.exists(),
        "files": [],
        "snapshots": {},
    }

    if not campaign_dir.exists():
        return ctx

    files = sorted(p.name for p in campaign_dir.iterdir() if p.is_file() and not p.name.startswith("."))
    ctx["files"] = files

    key_files = [
        "phase1_live_summary.md",
        "campaign_priority_targets.md",
        "focus_targets.md",
        "campaign_live_interesting.txt",
        "live_priority_raw.tsv",
        "api_candidate_probe.tsv",
        "api_key_responses.txt",
        "graphql_probe.txt",
    ]

    for filename in key_files:
        p = campaign_dir / filename
        if p.exists():
            ctx["snapshots"][filename] = _read_text(p)

    for filename in ["campaign_priority_targets.csv", "focus_targets.txt"]:
        p = campaign_dir / filename
        if p.exists():
            ctx["snapshots"][filename] = _read_text(p, max_chars=12000)

    return ctx


def load_agents_md_excerpt(agents_md_path: Path) -> str:
    if not agents_md_path.exists():
        return ""
    text = _read_text(agents_md_path, max_chars=180000)

    start_markers = [
        "## 2. Agent Roles & Responsibilities",
        "## 5. Reconnaissance Pipeline",
        "## 6. Vulnerability Research Workflow",
        "## 8. Reporting Standards",
        "## 14. Legal & Ethical Framework",
    ]

    chunks: list[str] = []
    for marker in start_markers:
        start = text.find(marker)
        if start == -1:
            continue
        next_h2 = text.find("\n## ", start + 4)
        chunk = text[start : (next_h2 if next_h2 != -1 else len(text))]
        chunks.append(chunk)

    return "\n\n".join(chunks)


def build_initial_message(task: str, campaign_context: dict[str, Any], agents_md_excerpt: str) -> str:
    payload = {
        "task": task,
        "campaign_context": campaign_context,
        "agents_md_excerpt": agents_md_excerpt,
        "required_output": {
            "format": "markdown",
            "sections": [
                "Scope Decision",
                "Prioritized Findings or Opportunities",
                "Safe Test Plan",
                "Evidence Gaps",
                "Report Draft Skeleton",
                "Next Iteration Improvements",
            ],
        },
    }
    return json.dumps(payload, indent=2)


def build_manager_message(task: str, campaign_context: dict[str, Any], agents_md_excerpt: str) -> str:
    files = campaign_context.get("files", []) if isinstance(campaign_context, dict) else []
    snapshots = campaign_context.get("snapshots", {}) if isinstance(campaign_context, dict) else {}
    snapshot_names = ", ".join(sorted(snapshots.keys())) if snapshots else "none"

    lines: list[str] = []
    lines.append("User request:")
    lines.append(task.strip() or "(empty task)")
    lines.append("")
    if _looks_like_local_ops_task(task):
        lines.append("Task mode: local machine operation")
        lines.append("- Prefer ExecAgent directly.")
        lines.append("- Skip security-specialist routing unless explicitly requested.")
        lines.append("- Use plain text output only.")
        lines.append("- End final user-facing answer with TERMINATE.")
    else:
        lines.append("Campaign context:")
        lines.append(f"- campaign_dir: {campaign_context.get('campaign_dir', 'unknown')}")
        lines.append(f"- files_count: {len(files)}")
        lines.append(f"- key_artifacts: {snapshot_names}")
        lines.append("")
        lines.append("Coordination rules:")
        lines.append("- Orchestrator decides which specialist to call.")
        lines.append("- Use specialists only when needed.")
        lines.append("- Keep internal responses short.")
        lines.append("- User-facing response must be plain text, concise, no JSON.")
        lines.append("- End final user-facing answer with TERMINATE.")
        lines.append("")
        lines.append("AGENTS.md relevant excerpt (truncated):")
        lines.append(agents_md_excerpt[:3000] if agents_md_excerpt else "(no excerpt loaded)")
    return "\n".join(lines)
