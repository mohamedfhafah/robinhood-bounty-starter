# Next 48 Hours Plan (No MITM, Maximum ROI)

Assumptions:
- Two owned test accounts available (Account A/B)
- Legal headers and in-scope handling already configured
- Focus on reproducible authz/authn issues with strong evidence quality

## Hour-by-hour execution

| Hour | Action | Practical output |
|---:|---|---|
| 0 | Prep workspace, create result dirs, define naming convention for captures | `findings/raw/`, `findings/diffs/`, `findings/repro/` ready |
| 1 | Validate tokens/sessions for Account A and B | sanity responses + token metadata notes |
| 2 | Baseline unauth vs auth request templates | reusable curl/http templates |
| 3 | Enumerate `/accounts/` objects with A and B | object URL lists per account |
| 4 | Cross-replay `/accounts/` object URLs (A token on B objects and reverse) | diff matrix + status/body hashes |
| 5 | Re-test any non-403/non-404 anomalies from hour 4 | confirmed/false-positive list |
| 6 | Enumerate `/orders/` objects for A/B | order URL corpus |
| 7 | Cross-replay `/orders/` object URLs | authz diff output |
| 8 | Enumerate `/positions/` objects for A/B | position URL corpus |
| 9 | Cross-replay `/positions/` objects | authz diff output |
| 10 | Enumerate `/portfolios/` objects for A/B | portfolio URL corpus |
| 11 | Cross-replay `/portfolios/` objects | authz diff output |
| 12 | Midpoint review #1; triage strongest anomalies | shortlist of candidate findings |
| 13 | Enumerate `/documents/` objects/links for A/B | document URL corpus |
| 14 | Cross-replay `/documents/` access attempts | PII exposure check results |
| 15 | Enumerate `/watchlists/` objects for A/B | watchlist IDs corpus |
| 16 | Cross-account read/update/delete attempts on `/watchlists/` | write-path authz evidence |
| 17 | Test `/notifications/` vs `/notifications/devices/` behavior with/without auth | boundary behavior notes |
| 18 | Attempt foreign device reference operations (safe, owned scope) | device-binding authz evidence |
| 19 | Stabilization pass: rerun all suspicious endpoints 3x | consistency report |
| 20 | Start OAuth integrity tests: `/oauth2/authorize/` parameter tampering | redirect/state handling outcomes |
| 21 | Continue OAuth: scope downgrades/upgrades and invalid combinations | scope enforcement notes |
| 22 | `/oauth2/token/` grant and client-binding checks (non-destructive) | token issuance integrity notes |
| 23 | `/oauth2/revoke_token/` revocation effectiveness + timing | revocation validation logs |
| 24 | Day 1 closeout: package evidence and draft 1–2 finding candidates | candidate reports v0 |
| 25 | Fresh session start; verify prior anomalies still reproducible | reproducibility status |
| 26 | MFA/session boundary design and test setup | test case sheet |
| 27 | `/mfa/` and step-up required flow checks | MFA enforcement notes |
| 28 | Session replay tests across MFA states | session binding evidence |
| 29 | Cross-host token audience tests: `api` token on `nummus` endpoints | audience segregation matrix |
| 30 | `nummus` account/order route auth behavior mapping | crypto edge auth map |
| 31 | Retry with alternate token states (fresh/older/revoked) | lifecycle behavior notes |
| 32 | Discover `mobile.api.robinhood.com` paths from safe probes | endpoint candidate list |
| 33 | Auth matrix on discovered `mobile.api` paths | unauth/auth response map |
| 34 | Discover `mobile-rest.api.robinhood.com` paths | endpoint candidate list |
| 35 | Auth matrix on discovered `mobile-rest` paths | response + auth gate map |
| 36 | Probe `auth.api`/`login.api`/`sso.api` for flow consistency | auth microservice comparison |
| 37 | Deepen best auth anomaly from hour 36 | reproducible PoC trace |
| 38 | `orders.api` + `exchange.api` discovery and auth parity checks | service-drift evidence |
| 39 | `api-streaming`/`gws` handshake auth and subscription checks | channel auth notes |
| 40 | Re-run top 3 anomalies with clean environment | high-confidence confirmation |
| 41 | Quantify impact per anomaly (data/control exposure) | severity mapping |
| 42 | Build minimal reproducible scripts for each candidate issue | `findings/repro/*.sh` |
| 43 | Draft report #1 full write-up | report draft |
| 44 | Draft report #2 full write-up | report draft |
| 45 | Quality gate: remove weak/noisy claims, ensure scope/legal safety | final candidate set |
| 46 | Final evidence packaging (requests, responses, timestamps, hashes) | submission-ready bundle |
| 47 | Final summary + handoff notes to main operator | `runlogs/next_48h_plan.md` and finding index updated |

## Execution rules (to maximize acceptance)
- Keep every test reproducible and low-noise (same request repeated 3x before claiming signal).
- Prefer read-only validation first; escalate to write operations only where necessary and safe.
- For every anomaly, capture: exact request, full response, timestamp, account context (A/B), and expected vs actual behavior.
- Do not include MITM-dependent claims in this 48h cycle.

## Primary targets by phase
- **Phase 1 (Hours 0–19):** BOLA across core brokerage resources
- **Phase 2 (Hours 20–31):** OAuth/MFA/session and cross-host token boundary
- **Phase 3 (Hours 32–40):** mobile/microservice/streaming edges
- **Phase 4 (Hours 41–47):** report-quality evidence and submission prep
