#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Create target directory layout from AGENTS.md section 3.6")
    p.add_argument("--root", default="~/bugbounty", help="Base workspace root")
    p.add_argument("--program", required=True, help="Program folder name")
    p.add_argument("--target", required=True, help="Target domain folder name")
    p.add_argument("--dry-run", action="store_true", help="Show paths without creating")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).expanduser().resolve()
    base = root / "targets" / args.program / args.target

    dirs = [
        base / "recon" / "subdomains" / "raw",
        base / "recon" / "subdomains" / "resolved",
        base / "recon" / "subdomains" / "screenshots",
        base / "recon" / "endpoints" / "wayback",
        base / "recon" / "endpoints" / "crawled",
        base / "recon" / "endpoints" / "js",
        base / "recon" / "dns",
        base / "recon" / "ports",
        base / "recon" / "tech",
        base / "findings",
        base / "reports" / "drafts",
        base / "reports" / "submitted",
    ]

    if args.dry_run:
        for d in dirs:
            print(d)
        print(base / "notes.md")
        return 0

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    notes = base / "notes.md"
    if not notes.exists():
        notes.write_text("# Target Notes\n\n- Scope summary:\n- Test accounts:\n- High-value flows:\n")

    print(f"[+] initialized target structure: {base}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
