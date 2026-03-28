# Promising Lead Summary

- **lead id:** RH-2026-LA-005
- **why promising:** `POST /oauth2/revoke_token/` on `api.robinhood.com` returns deterministic **HTTP 500** for unauthenticated form-encoded `token=...` payloads (3/3), while equivalent JSON payloads on same endpoint return controlled `400`, and `/oauth2/token/` control stays `401`. This indicates endpoint-specific parser/auth-order exception path on a security-sensitive OAuth revoke surface.

## Repro steps
1. Send unauthenticated request:
   - `POST https://api.robinhood.com/oauth2/revoke_token/`
   - `Content-Type: application/x-www-form-urlencoded`
   - Body: `token=11111111-1111-1111-1111-111111111111`
2. Observe `HTTP 500` with generic server error HTML body.
3. Repeat 3 times; verify stable response hash (`fd62a53a...`).
4. Control comparisons:
   - Same endpoint with JSON body `{"token":"11111111-1111-1111-1111-111111111111"}` => `400` (`57cde762...`).
   - `POST /oauth2/token/` with form payload => `401` (`7fea647e...`).

## Evidence pointers
- `verified/verification_run_2026-02-18_authz_diff.md` (Batch 6)
- `output/revoke_form_probe_20260218T2352.tsv`
- `output/revoke_500_repro_20260218T2354.tsv`
- `output/oauth_noauth_matrix_20260218T2351.tsv`
- `output/noauth_family_probe_20260218T2348.tsv`

## Final recommendation (after impact-validation mini-batch)
- **Decision:** **hold and gather more** (do not submit yet)
- **Confidence:** medium
- **Rationale:**
  - Strongly confirmed deterministic bug: in bounded testing (23 cases), non-empty form token classes repeatedly produced endpoint-specific `500` on `/oauth2/revoke_token/` (stable body hash), while neighboring controls returned controlled `400/415`.
  - However, current evidence still maps to a generic pre-auth server error path without demonstrated confidentiality/integrity impact or measured availability degradation at meaningful (yet safe) rates.
  - No stack leakage, no cache poisoning signal, and no anomalous proxy behavior beyond expected CloudFront error forwarding.

## Suggested next actions (if pursuing upgrade to reportable impact)
1. Safe low-rate time-window check (still non-destructive) to estimate sustained 5xx ratio and operational impact signal.
2. Owned authenticated revoke-semantic test to determine whether malformed form handling affects real token revocation logic.
3. Correlate request IDs/error telemetry fields (if exposed) to better evidence backend exception class and security relevance.


## LA-005 final escalation decision
- Status: validated anomaly, limited security impact signal.
- Recommended disposition: submit as reliability/security-hardening issue with clear caveat, or deprioritize if program historically marks these as informative.
- Latest artifact: la005_escalation_matrix_20260219_003210.tsv
