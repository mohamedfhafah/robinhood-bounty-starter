#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOARD = ROOT / "runlogs" / "board.md"
AGENT_LOGS = {
    "Mobile-RE": ROOT / "runlogs" / "agents" / "mobile-re.md",
    "Traffic-Auth": ROOT / "runlogs" / "agents" / "traffic-auth.md",
    "Logic-AuthZ": ROOT / "runlogs" / "agents" / "logic-authz.md",
    "Verifier-Reporter": ROOT / "runlogs" / "agents" / "verifier-reporter.md",
}


def parse_status(p: Path) -> str:
    if not p.exists():
        return "MISSING"
    for line in p.read_text(errors="replace").splitlines():
        if line.lower().startswith("- status:"):
            return line.split(":", 1)[1].strip().upper() or "UNKNOWN"
    return "UNKNOWN"


def parse_progress(p: Path) -> int:
    if not p.exists():
        return 0
    lines = p.read_text(errors="replace").splitlines()
    total = sum(1 for l in lines if l.strip().startswith("- ["))
    done = sum(1 for l in lines if l.strip().startswith("- [x]"))
    if total == 0:
        return 0
    return int((done / total) * 100)


def update_board() -> None:
    if not BOARD.exists():
        raise FileNotFoundError(f"Missing board: {BOARD}")

    text = BOARD.read_text(errors="replace")
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    text = text.replace(
        next((l for l in text.splitlines() if l.startswith("Last updated:")), "Last updated:"),
        f"Last updated: {now}",
        1,
    )

    rows = []
    for name, path in AGENT_LOGS.items():
        status = parse_status(path)
        progress = parse_progress(path)
        rows.append((name, status, progress, path))

    # naive row rewrite by replacing known TODO rows
    out = []
    for line in text.splitlines():
        replaced = False
        for name, status, progress, path in rows:
            if line.startswith(f"| {name} |"):
                out.append(
                    f"| {name} | {'APK/static/runtime' if name=='Mobile-RE' else 'Proxy traffic/session/auth' if name=='Traffic-Auth' else 'IDOR/business logic/authz' if name=='Logic-AuthZ' else 'Validation/report/CVSS'} | {status} | {progress}% | See agent log | {path.relative_to(ROOT)} |"
                )
                replaced = True
                break
        if not replaced:
            out.append(line)

    BOARD.write_text("\n".join(out) + "\n")
    print(f"updated: {BOARD}")


if __name__ == "__main__":
    update_board()
