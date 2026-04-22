# Robinhood Bug Bounty Starter

This workspace is set up for **safe, compliant** testing based on the Robinhood program rules you provided.

## What this kit includes

- `scope/`: in-scope and out-of-scope host/path lists.
- `scripts/in_scope.sh`: fast check for host/URL scope before testing.
- `scripts/rh_env.sh`: exports required request headers.
- `scripts/rh_curl.sh`: wrapper for `curl` with required bug bounty headers.
- `scripts/passive_recon.sh`: passive subdomain discovery + conservative live probe.
- `scripts/run_campaign.sh`: run recon across all configured root domains.
- `scripts/aggregate_campaign.py`: build unified campaign priority outputs.
- `scripts/build_focus_targets.py`: derive an actionable host shortlist.
- `scripts/active_probe_focus.sh`: low-rate, header-compliant active probing of shortlist.
- `scripts/authz_diff_probe.sh`: compare endpoint responses across one or two owned auth tokens.
- `templates/report_template.md`: report format for HackerOne submissions.

## Program guardrails to keep in mind

- Stop immediately and report if you encounter sensitive data.
- Test only with accounts you own.
- Do not exceed `$1,000` during unbounded-loss testing.
- Avoid disruptive or resource-intensive testing.
- Demonstrate actual impact, not only theoretical impact.

## Quick start

From `robinhood-bounty/`:

```bash
# 1) Set required Robinhood headers in your shell session
source scripts/rh_env.sh <HACKERONE_USERNAME> <TEST_ACCOUNT_EMAIL>

# 2) Confirm target is in scope before testing
./scripts/in_scope.sh https://api.robinhood.com/
./scripts/in_scope.sh https://shop.robinhood.com/

# 3) Send a request with required bounty headers
./scripts/rh_curl.sh -i https://api.robinhood.com/

# 4) Run passive recon for one root domain
./scripts/passive_recon.sh robinhood.com
```

Optional control flags:

```bash
# Keep runs bounded and reproducible
AMASS_TIMEOUT_SECONDS=120 HTTPX_TIMEOUT_SECONDS=120 CLASSIFY_JOBS=16 ./scripts/passive_recon.sh robinhood.com

# Dry-run mode (no external recon/probing)
RUN_SUBFINDER=0 RUN_AMASS=0 RUN_HTTPX=0 ./scripts/passive_recon.sh robinhood.com
```

## Full campaign run

```bash
# Phase 1: passive mapping across scope roots
RUN_HTTPX=0 AMASS_TIMEOUT_SECONDS=75 ./scripts/run_campaign.sh ./scope/root_domains.txt

# Build shortlist from campaign output
python3 ./scripts/build_focus_targets.py ./output/campaign_<timestamp> 80 40

# Phase 2: active probing with required Robinhood headers
source scripts/rh_env.sh <HACKERONE_USERNAME> <TEST_ACCOUNT_EMAIL>
./scripts/active_probe_focus.sh ./output/campaign_<timestamp> 60
```

Authenticated authz diff check (two owned accounts):

```bash
export RH_TOKEN_A='Bearer <token_account_a>'
export RH_TOKEN_B='Bearer <token_account_b>'   # optional
./scripts/authz_diff_probe.sh ./output/campaign_<timestamp>/authz_diff.tsv
```

## Suggested first testing flow

1. Start with authenticated workflows using your own test account.
2. Focus on business logic and authorization boundaries.
3. Validate each target host/path with `scripts/in_scope.sh` before touching it.
4. Keep request rates low and avoid heavy scans.
5. Log proof of impact and exact reproduction steps immediately.

## Notes

- Scope changes over time; re-verify with HackerOne before deep testing.
- `scope/out_of_scope_issue_types.md` contains major excluded finding categories.
- Mobile app bundle IDs are listed in program scope but are outside host-based checks in this toolkit.
