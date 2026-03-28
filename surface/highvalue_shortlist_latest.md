# High-Value Shortlist (latest)

Run: 2026-02-19 01:10–01:35 CET  
Strategy: high-ROI, less-tested auth/security-sensitive families; SAFE non-destructive checks only.

## Top 10 shortlist (next verification focus)

1. `https://api.robinhood.com/oauth2/authorize/`  
   - Why: auth-flow gate integrity; high impact if tamperable.
2. `https://api.robinhood.com/oauth2/token/`  
   - Why: token issuance boundary; compare method/content-type behavior.
3. `https://api.robinhood.com/challenge/`  
   - Why: challenge/MFA-adjacent flow root exposed anonymously (`GET 200`).
4. `https://api.robinhood.com/applications/`  
   - Why: deterministic `POST 421` routing anomaly vs `GET/OPTIONS 404`.
5. `https://api.robinhood.com/mfa/`  
   - Why: step-up auth boundary worth A/B session checks when tokens available.
6. `https://nummus.robinhood.com/`  
   - Why: reachable less-tested crypto family edge; baseline method controls.
7. `https://nummus.robinhood.com/accounts/`  
   - Why: account-scoped object path in alternate service family.
8. `https://nummus.robinhood.com/orders/`  
   - Why: security-sensitive state path; cross-service auth boundary target.
9. `https://nummus.robinhood.com/oauth2/token/`  
   - Why: verify OAuth surface parity mismatch vs `api` family.
10. `https://api-streaming.robinhood.com/`  
   - Why: streaming auth edge; verify method/route boundary drift.

## Quick status from this run
- No new medium+ confidence exploitable AuthZ/business-logic lead confirmed.
- Existing LA-005 remains strongest candidate.
- Low-confidence monitor-only anomaly: `POST /applications/` => `421` (stable).

## Evidence pointers
- `output/highvalue_batch_20260219/top10_diff_matrix.tsv`
- `output/highvalue_batch_20260219/auth_surface_matrix.tsv`
- `output/highvalue_batch_20260219/httpx_hosts.jsonl`
- `output/highvalue_batch_20260219/host_root_matrix.json`
