#!/usr/bin/env python3
import csv
import re
import sys
from pathlib import Path

EXCLUDE_SUBSTR = {
    "autodiscover",
    "mta-sts",
    "spf",
    "dkim",
    "sip",
    "smtp",
    "email",
    "dns",
    "cdn",
    "img",
    "assets",
    "static",
    "akamai",
}

INCLUDE_HINTS = {
    "api",
    "auth",
    "login",
    "oauth",
    "sso",
    "admin",
    "oak",
    "nummus",
    "crypto",
    "wallet",
    "order",
    "trade",
    "cashier",
    "payment",
    "money",
    "gateway",
    "stream",
    "graphql",
    "support",
}


def host_quality(host: str) -> int:
    score = 0

    if any(x in host for x in INCLUDE_HINTS):
        score += 20

    if host.startswith("www."):
        score -= 3

    labels = host.split(".")
    if any(label.isdigit() for label in labels):
        score -= 3

    if any(x in host for x in EXCLUDE_SUBSTR):
        score -= 20

    if re.match(r"^[a-z0-9.-]+$", host):
        score += 2

    return score


def main() -> int:
    if len(sys.argv) < 2 or len(sys.argv) > 4:
        print("Usage: ./scripts/build_focus_targets.py <campaign_dir> [max_hosts] [min_priority]")
        return 1

    campaign_dir = Path(sys.argv[1]).resolve()
    max_hosts = int(sys.argv[2]) if len(sys.argv) >= 3 else 80
    min_priority = int(sys.argv[3]) if len(sys.argv) >= 4 else 40

    src = campaign_dir / "campaign_priority_targets.csv"
    if not src.exists():
        print(f"Missing: {src}")
        return 1

    rows = []
    with src.open() as f:
        for row in csv.DictReader(f):
            host = row["host"].strip().lower()
            pri = int(row["priority_score"])
            if pri < min_priority:
                continue
            q = host_quality(host)
            if q < 0:
                continue
            row["quality_score"] = q
            row["priority_score"] = pri
            rows.append(row)

    rows.sort(key=lambda r: (-(r["priority_score"] + r["quality_score"]), -r["priority_score"], r["host"]))
    rows = rows[:max_hosts]

    out_txt = campaign_dir / "focus_targets.txt"
    out_csv = campaign_dir / "focus_targets.csv"
    out_md = campaign_dir / "focus_targets.md"

    out_txt.write_text("\n".join(r["host"] for r in rows) + ("\n" if rows else ""))

    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "host",
                "tier",
                "priority_score",
                "quality_score",
                "reasons",
            ],
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "host": r["host"],
                    "tier": r["tier"],
                    "priority_score": r["priority_score"],
                    "quality_score": r["quality_score"],
                    "reasons": r["reasons"],
                }
            )

    lines = [
        "# Focus Targets",
        "",
        f"- Selected hosts: {len(rows)}",
        f"- Source: {src}",
        "",
        "| Rank | Host | Tier | Priority | Quality | Reasons |",
        "|---|---|---|---:|---:|---|",
    ]

    for i, r in enumerate(rows, start=1):
        lines.append(
            f"| {i} | {r['host']} | {r['tier']} | {r['priority_score']} | {r['quality_score']} | {r['reasons']} |"
        )

    lines.append("")
    out_md.write_text("\n".join(lines))

    print(f"[+] wrote: {out_txt}")
    print(f"[+] wrote: {out_csv}")
    print(f"[+] wrote: {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
