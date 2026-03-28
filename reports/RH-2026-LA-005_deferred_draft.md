# RH-2026-LA-005 — Deferred Draft (Reliability / Security Hardening)

## Title
`/oauth2/revoke_token/` returns deterministic HTTP 500 for unauthenticated non-empty form token payloads

## Summary
A bounded, low-rate test series identified deterministic server-side 500 behavior on:

- `POST https://api.robinhood.com/oauth2/revoke_token/`
- `Content-Type: application/x-www-form-urlencoded`
- body `token=<non-empty-value>`

Control tests on sibling paths and alternative content-types returned non-5xx responses, indicating endpoint-specific exception behavior.

## Reproduction
1. Send:
   - Method: `POST`
   - URL: `/oauth2/revoke_token/`
   - Header: `Content-Type: application/x-www-form-urlencoded`
   - Body: `token=123e4567-e89b-12d3-a456-426614174000`
2. Observe status `500`.
3. Repeat multiple times (observed deterministic behavior).

## Control Cases
- Same endpoint with JSON body: `400`
- Same endpoint with missing/empty token form param: `400`
- Same endpoint with `text/plain`: `415`
- Neighbor endpoint `/oauth2/token/`: non-5xx behavior in tested controls

## Observed Impact
- Confirmed: pre-auth server error path is reachable and deterministic.
- Not confirmed (in current bounded tests): auth bypass, sensitive data disclosure, stack trace leakage, high-amplification DoS characteristics.

## Current Assessment
- Category: Reliability / Security hardening anomaly
- Security confidence: low–medium
- Submission recommendation: optional (likely informative/low severity unless program values 5xx reliability issues)

## Evidence Artifacts
- `output/revoke_500_repro_20260218T2354.tsv`
- `output/la005_impact_matrix_20260218_235219.tsv`
- `output/la005_escalation_matrix_20260219_003210.tsv`
- `verified/verification_run_2026-02-18_authz_diff.md`

## Next Validation (if needed before submission)
1. Verify behavior across additional edge token encodings and bounded retry windows.
2. Confirm whether backend logs/owner response indicate known issue or routing fault.
3. Test whether this path can be abused for measurable service degradation under strict safe-harbor limits (only with explicit permission).
