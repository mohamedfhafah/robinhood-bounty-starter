# Agent Log - Traffic-Auth

- Status: DONE (analysis + annotations complete; execution blockers remain for authenticated replay)
- Objective: Capture authenticated request flows and isolate auth/session boundaries.
- Deliverables:
  - `surface/endpoints.jsonl` (auth annotations)
  - `runlogs/agents/traffic-auth.md` (checkpoints)

## Checkpoints
- [x] Proxy baseline working (existing campaign artifacts consumed)
- [x] Core auth flow mapped (Bearer/JWT boundaries + public vs auth-gated split)
- [x] Token/session edge cases logged (invalid JWT handling, metadata auth requirement, method boundaries)

## Progress Summary

### 1) Headers and session artifacts identified
- Program-required recon headers in scripts:
  - `X-Bug-Bounty: <h1_username>`
  - `X-Test-Account-Email: <owned_test_email>`
- Auth/session artifacts inferred from responses and scripts:
  - `Authorization: Bearer <JWT>` for account-scoped API routes.
  - `WWW-Authenticate: Bearer` returned by `api.robinhood.com` auth-gated routes.
  - Invalid token telemetry: `rh-auth-blocked-reason: jwt_invalid` + `JWT verification failed`.
  - Downstream metadata gate on notifications devices: `"Authorization" key does not exist in metadata`.
  - X1 GraphQL stack advertises identity headers in CORS: `X-Thrive-Identity-Id`, `X-Thrive-Identity-Token` (+ staging variants), with `Authorization` also allowed.

### 2) Auth boundaries mapped
- **Auth-gated (high confidence)** on `api.robinhood.com`: `/accounts/`, `/orders/`, `/positions/`, `/portfolios/`, `/watchlists/`, `/documents/`, `/mfa/`, `/oauth2/authorize/`, `/notifications/devices/`.
- **Public/unauthenticated** on `api.robinhood.com`: `/instruments/`, `/markets/`, `/quotes/?symbols=...`, `/fundamentals/<symbol>/`, top-level `/notifications/` discovery object.
- **Method boundary**: `/oauth2/token/` and `/oauth2/revoke_token/` present but GET=405 (likely POST-only grant/revoke flows).
- **Cross-host auth surface hint**:
  - `nummus.robinhood.com/accounts/` and `/orders/` => 401 (endpoint exists and is auth-gated).
  - `cashier.robinhood.com/accounts/` => 404 (route absent/different contract).

### 3) Endpoint annotation output
- Updated `surface/endpoints.jsonl` with normalized auth annotations:
  - `source_file`
  - `endpoint_or_host`
  - `auth_required_guess`
  - `auth_artifact`
  - `confidence`
  - `notes`

## Blockers
1. No valid owned-account bearer tokens captured in current artifacts; cannot complete authenticated replay or scope/audience validation.
2. No dual-account token pair (`RH_TOKEN_A` + `RH_TOKEN_B`) available yet for horizontal authz differential checks using `scripts/authz_diff_probe.sh`.
3. X1 GraphQL authenticated context unavailable (identity header values and valid auth token not captured), so GraphQL authorization boundary remains inferred-only.

## Top 8 High-Value AuthZ Test Cases (Owned-account model only)
1. **Horizontal BOLA on `/accounts/`**: replay account URLs/IDs between Account A and Account B tokens; expect strict ownership enforcement.
2. **Horizontal BOLA on `/orders/` and `/positions/`**: swap object references across two owned accounts and compare status/body hashes.
3. **Document access isolation on `/documents/`**: attempt cross-account document URL/object fetch with second owned token.
4. **Watchlist ownership checks on `/watchlists/`**: read/update/delete attempts against other owned account watchlist identifiers.
5. **Notifications boundary**: validate `/notifications/` remains discovery-only while `/notifications/devices/` enforces bearer ownership and rejects foreign-device operations.
6. **Token audience/scope separation (`api` vs `nummus`)**: test whether a valid `api.robinhood.com` bearer is accepted/rejected on `nummus` auth-gated endpoints and whether scopes differ correctly.
7. **OAuth flow integrity**: verify `/oauth2/authorize/` + `/oauth2/token/` state handling, redirect constraints, and token binding to the authenticating principal (no cross-account reuse).
8. **MFA/session binding**: ensure MFA-completed session/token for Account A cannot be replayed for Account B resources and cannot bypass step-up checks.

## Notes for next execution pass
- Acquire owned tokens safely via normal login flow; never test third-party accounts.
- Run `scripts/authz_diff_probe.sh <outfile>` with both owned account tokens to generate deterministic diff evidence.
- Keep request rate low and remain strictly in-scope (`com.robinhood.global` assets only).
