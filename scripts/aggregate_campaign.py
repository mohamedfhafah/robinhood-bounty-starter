#!/usr/bin/env python3
import csv
import re
import sys
from pathlib import Path


def load_patterns(path: Path):
    patterns = []
    for line in path.read_text().splitlines():
        line = line.strip().lower()
        if not line or line.startswith("#"):
            continue
        patterns.append(line)
    return patterns


def load_tier_patterns(scope_dir: Path):
    tiers = {}
    for tier_file, tier_name in [
        ("tier1_hosts.txt", "TIER1"),
        ("tier2_hosts.txt", "TIER2"),
        ("tier3_hosts.txt", "TIER3"),
    ]:
        tiers[tier_name] = load_patterns(scope_dir / tier_file)
    return tiers


def wildcard_match(host: str, pattern: str) -> bool:
    # Convert simple wildcard pattern to regex.
    regex = "^" + re.escape(pattern).replace(r"\*", ".*") + "$"
    return re.match(regex, host) is not None


def tier_for_host(host: str, tier_patterns) -> str:
    for tier_name in ("TIER1", "TIER2", "TIER3"):
        for pattern in tier_patterns[tier_name]:
            if wildcard_match(host, pattern):
                return tier_name
    return "UNKNOWN"


def out_of_scope_match(host: str, out_patterns) -> bool:
    for pattern in out_patterns:
        if wildcard_match(host, pattern):
            return True
        # Exact out-of-scope host also excludes its subdomains.
        if "*" not in pattern and host.endswith("." + pattern):
            return True
    return False


def score_host(host: str, tier: str):
    score = 0
    reasons = []

    tier_score = {"TIER1": 30, "TIER2": 18, "TIER3": 12}.get(tier, 0)
    if tier_score:
        score += tier_score
        reasons.append(f"{tier}+{tier_score}")

    keyword_rules = [
        (("api",), 20, "api"),
        (("auth", "oauth", "login", "token", "sso"), 25, "auth"),
        (("admin", "oak", "support", "backoffice"), 25, "admin"),
        (("wallet", "nummus", "crypto"), 24, "crypto"),
        (("cashier", "payments", "payment", "card", "money"), 20, "payments"),
        (("trade", "trading", "broker", "order", "exchange"), 18, "trading"),
        (("gateway", "graphql", "gql"), 14, "gateway"),
        (("ws", "websocket", "stream"), 12, "realtime"),
        (("mobile", "android", "ios"), 8, "mobile"),
    ]

    matched_tags = set()
    for keywords, pts, label in keyword_rules:
        if any(k in host for k in keywords):
            if label not in matched_tags:
                score += pts
                reasons.append(f"{label}+{pts}")
                matched_tags.add(label)

    if host.startswith("www."):
        score -= 4
        reasons.append("www-4")

    return score, reasons


def read_lines(path: Path):
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        line = line.strip().lower()
        if line:
            out.append(line)
    return out


def is_valid_hostname(host: str) -> bool:
    if "_" in host:
        return False
    if len(host) > 253 or "." not in host:
        return False
    if not re.match(r"^[a-z0-9.-]+$", host):
        return False
    if ".." in host:
        return False
    return True


def main():
    if len(sys.argv) != 3:
        print("Usage: ./scripts/aggregate_campaign.py <campaign_dir> <scope_dir>")
        return 1

    campaign_dir = Path(sys.argv[1]).resolve()
    scope_dir = Path(sys.argv[2]).resolve()

    tier_patterns = load_tier_patterns(scope_dir)
    out_patterns = load_patterns(scope_dir / "out_of_scope_hosts.txt")

    all_discovered = set()
    all_in_scope = {}
    all_live = set()

    for domain_run in sorted(campaign_dir.glob("*_*/")):
        for host in read_lines(domain_run / "discovered_hosts.txt"):
            if not is_valid_hostname(host):
                continue
            all_discovered.add(host)

            if out_of_scope_match(host, out_patterns):
                continue

            tier = tier_for_host(host, tier_patterns)
            if tier != "UNKNOWN":
                all_in_scope[host] = tier

        for line in read_lines(domain_run / "httpx_alive.txt"):
            host = line.split()[0].strip().lower()
            host = host.replace("https://", "").replace("http://", "")
            host = host.split("/")[0].split(":")[0]
            if host:
                all_live.add(host)

    (campaign_dir / "campaign_all_discovered_hosts.txt").write_text(
        "\n".join(sorted(all_discovered)) + ("\n" if all_discovered else "")
    )
    (campaign_dir / "campaign_in_scope_hosts.txt").write_text(
        "\n".join(sorted(all_in_scope.keys())) + ("\n" if all_in_scope else "")
    )
    (campaign_dir / "campaign_live_hosts.txt").write_text(
        "\n".join(sorted(all_live)) + ("\n" if all_live else "")
    )

    rows = []
    for host in sorted(all_in_scope.keys()):
        tier = all_in_scope[host]
        score, reasons = score_host(host, tier)
        if host in all_live:
            score += 8
            reasons.append("live+8")
        rows.append(
            {
                "host": host,
                "tier": tier,
                "live": "yes" if host in all_live else "no",
                "priority_score": score,
                "reasons": ",".join(reasons),
            }
        )

    rows.sort(key=lambda r: (-int(r["priority_score"]), r["host"]))

    csv_path = campaign_dir / "campaign_priority_targets.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["host", "tier", "live", "priority_score", "reasons"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    md_path = campaign_dir / "campaign_priority_targets.md"
    lines = [
        "# Campaign Priority Targets",
        "",
        f"- Total discovered hosts: {len(all_discovered)}",
        f"- Total in-scope hosts: {len(all_in_scope)}",
        f"- Total live hosts: {len(all_live)}",
        "",
        "## Top 50",
        "",
        "| Rank | Host | Tier | Live | Score | Reasons |",
        "|---|---|---|---|---:|---|",
    ]

    for idx, row in enumerate(rows[:50], start=1):
        lines.append(
            f"| {idx} | {row['host']} | {row['tier']} | {row['live']} | {row['priority_score']} | {row['reasons']} |"
        )

    lines.append("")
    md_path.write_text("\n".join(lines))

    print(f"[+] Aggregated campaign: {campaign_dir}")
    print(f"    discovered={len(all_discovered)} in_scope={len(all_in_scope)} live={len(all_live)}")
    print(f"    priority_csv={csv_path}")
    print(f"    priority_md={md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
