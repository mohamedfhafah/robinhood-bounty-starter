# Verification Run — 2026-02-18 (AuthZ Differential)

## Context
- Two owned test sessions used (Account A and Account B).
- Differential checks executed against selected API endpoints discovered from live web traffic and prior surface maps.
- Goal: test for cross-account authorization bypass (IDOR/AuthZ confusion) without mobile MITM.

## Results

### 1) `/inbox/notifications/badge?userUuid=<uuid>`
- A token + A uuid => 200
- A token + B uuid => 200 (same effective badge result as caller context)
- B token + B uuid => 200
- B token + A uuid => 200 (same effective badge result as caller context)

Observation:
- Endpoint appears to resolve by caller context; `userUuid` parameter did not grant cross-account access.
- No exploitable cross-account data disclosure observed in this check.

### 2) `/kaizen/experiments/<user_uuid>/?trigger=false&names=account-switcher-v2`
- A token + A uuid => 200
- A token + B uuid => 403 with explicit `user ID mismatch`
- B token + B uuid => 200
- B token + A uuid => 403 with explicit `user ID mismatch`

Observation:
- Strong positive authorization control detected.
- Cross-account object access denied as expected.

## Interim verdict
- No confirmed IDOR/AuthZ bypass from these two differential checks.
- These tests are useful negative controls and should be recorded as rejected hypotheses for these specific vectors.

## Next checks (high ROI)
1. Identify endpoints returning account-scoped resource URLs and replay those URLs with opposite token.
2. Test write/modify actions (where safe and allowed) with mismatched ownership context.
3. Expand to endpoints surfaced in `surface/priority_queue.md` requiring user/resource identifiers.

## Batch 2 — SAFE mutation/method-boundary differential checks

Account context used: existing owned Account A/B Bearer auth contexts from prior run notes.

| # | Endpoint | Method | Request shape (redacted) | A status | B status | Cross-account attempt result | Side-effect observed | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | `/discovery/lists/items/?list_id=<list_uuid>` | GET | query `list_id=<own_or_other_list_uuid>` | own list `200`, other list `404` | own list `200`, other list `404` | Cross-list access denied (`404` both directions) | No | **PASS (AuthZ enforced)** |
| 2 | `/kaizen/experiments/<user_uuid>/?trigger=false&names=account-switcher-v2` | GET | path `<user_uuid>` + query `trigger=false&names=account-switcher-v2` | own `200`, other `403 user ID mismatch` | own `200`, other `403 user ID mismatch` | Explicit cross-user denial in response message | No | **PASS (strong ownership check)** |
| 3 | `/inbox/notifications/badge?userUuid=<user_uuid>` | GET | query `userUuid=<own_or_other_user_uuid>` | `200` on own and other UUID | `200` on own and other UUID | Parameter is caller-context bound; no foreign data observed | No | **No vuln observed (behavior consistent with caller binding)** |
| 4 | `/discovery/lists/items/?list_id=<list_uuid>` | DELETE (method-boundary) | query `list_id=<own_or_other_list_uuid>`; no body | own/cross both `405` | own/cross both `405` | Method blocked before object access; no bypass signal | No | **PASS (method not allowed)** |
| 5 | `/notifications/devices/` | POST (dry-run invalid) | JSON `{platform:<invalid>, device_id:<dummy>, token:<invalid>}` | `400` invalid platform | `400` invalid platform | N/A (no foreign object identifier in request) | No | **PASS (input validation, no state change)** |

### Batch 2 summary
- Executed 5 SAFE differential checks with A vs B contexts.
- No confirmed AuthZ/IDOR vulnerability identified in this batch.
- One endpoint (`/inbox/notifications/badge`) remains a monitoring candidate, but current evidence shows caller-context binding rather than cross-account disclosure.

## Batch 3 — Business-logic sequence checks

> Execution note: In this subagent runtime, owned Account A/B auth contexts were not present (`RH_TOKEN_A`/`RH_TOKEN_B` unset). To avoid unsafe guessing or side effects, only preflight validation was executed and all live sequence checks were **blocked** pending token/context injection.

| # | Hypothesis | Endpoint(s) | Sequence attempted | Status codes | Observed behavior | Side effect | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | Precondition bypass on notifications badge (cross-user param + caller binding) | `GET /inbox/notifications/badge?userUuid=<uuid>` | Planned: A(own)->A(foreign uuid)->B(own)->B(foreign uuid), plus replay of stale URL order | N/A (blocked) | Could not execute without A/B tokens in this runtime | No | **Blocked (missing A/B auth context)** |
| 2 | Order constraint check: list read before/after method-boundary call | `GET /discovery/lists/items/?list_id=<uuid>`, then `DELETE` same path, then `GET` again | Planned: verify no state drift and no sequence bypass after disallowed method | N/A (blocked) | Could not execute without A/B tokens and owned list IDs | No | **Blocked (missing A/B auth context)** |
| 3 | Feature/state mismatch: kaizen experiment UUID binding vs caller identity | `GET /kaizen/experiments/<user_uuid>/?trigger=false&names=account-switcher-v2` | Planned: A own->A other->B own->B other and repeated stale replay | N/A (blocked) | Could not execute without A/B tokens + user UUIDs | No | **Blocked (missing A/B auth context)** |
| 4 | Method transition boundary on notifications devices (read -> invalid write -> read) | `GET /notifications/devices/`, `POST /notifications/devices/` (invalid dry-run), `GET /notifications/devices/` | Planned: verify pre/post consistency and no hidden transition | N/A (blocked) | Could not execute without authenticated context | No | **Blocked (missing A/B auth context)** |
| 5 | Cross-host auth-context sequencing consistency (`api` vs `nummus`) | `GET /accounts/` on `api.robinhood.com` then same token on `nummus.robinhood.com` | Planned: A/B matrix to detect scope bleed via sequence/order | N/A (blocked) | Could not execute without A/B tokens | No | **Blocked (missing A/B auth context)** |

### Batch 3 summary
- SAFE execution policy respected; no mutation-risk traffic sent without owned authenticated context.
- No new vuln claim made from this blocked run.
- Required to proceed: inject owned Account A/B auth material (tokens + minimal object identifiers such as `user_uuid`, `list_id`) and rerun Batch 3 matrix.

## Batch 3 (executed in main session) — Business-logic sequence checks

Run time: 2026-02-18T22:50:15


### Check 1: Cross-account list item fetch via list_id replay

- Endpoints: `GET /discovery/lists/default/ -> GET /discovery/lists/items/?list_id=...`

- Sequence attempted: Fetch own list_id then replay with opposite token

- A status: 200

- B status: 200

- Cross-account result: A->B 404, B->A 404

- Side effect observed: No

- Verdict: **enforced (404 cross-account)**


### Check 2: Method/precondition bypass on notifications device registration

- Endpoints: `GET/POST /notifications/devices/`

- Sequence attempted: GET baseline then invalid POST with A and B

- A status: GET 200; POST 400

- B status: POST 400

- Cross-account result: not applicable

- Side effect observed: No

- Verdict: **input/method controls appear enforced**


### Check 3: userUuid parameter might override caller context

- Endpoints: `GET /inbox/notifications/badge?userUuid=...`

- Sequence attempted: Call with own and opposite userUuid under A/B tokens

- A status: own 200 alt 200

- B status: own 200 alt 200

- Cross-account result: A sigs 82e74f847376/82e74f847376; B sigs 13ec96969129/13ec96969129

- Side effect observed: No

- Verdict: **caller-context-bound in observed responses**


### Check 4: Order/precondition mismatch may leak issue/chat context

- Endpoints: `GET /pathfinder/support_chats/ and /pathfinder/issues/`

- Sequence attempted: Query chats then issues for A/B; compare shapes

- A status: chats 200, issues 200

- B status: chats 200, issues 200

- Cross-account result: chat sig 86910d4ef9d4/86910d4ef9d4 issue sig 4f53cda18c2b/4f53cda18c2b

- Side effect observed: No

- Verdict: **no cross-account signal detected**


### Check 5: entity id swap might bypass ownership checks

- Endpoints: `GET /kaizen/experiments/<user_uuid>/`

- Sequence attempted: Own id then opposite id under A/B

- A status: own 200 alt 403

- B status: own 200 alt 403

- Cross-account result: alt path returns 403 user mismatch

- Side effect observed: No

- Verdict: **strong ownership enforcement**

## Batch 4 — Write-adjacent method/state boundary checks

Run time: 2026-02-18T23:07:16


### Check 1: Unexpected write acceptance on support_chats endpoint

- Endpoint: `/pathfinder/support_chats/`

- Sequence attempted: GET baseline; POST invalid minimal payload with A and B

- A status: GET 200; POST 200

- B status: POST 200

- Cross-account result: not applicable

- Side effect observed: No

- Verdict: **review**


### Check 2: User settings endpoint might allow unsafe state update pattern

- Endpoint: `/ceres/v1/user_settings`

- Sequence attempted: GET then PATCH invalid/unknown field

- A status: GET 400; PATCH 404

- B status: PATCH 404

- Cross-account result: not applicable

- Side effect observed: No

- Verdict: **review**


### Check 3: trigger=true state transition may bypass ownership for foreign entity

- Endpoint: `/kaizen/experiments/a04cbcdc-e9d5-4669-b993-1802ccae9a77/`

- Sequence attempted: A on B entity with trigger=false then trigger=true; compare with B own

- A status: trigger=false 403; trigger=true 403

- B status: B own trigger=false 200

- Cross-account result: A foreign signatures 8ab73e0458ca/8ab73e0458ca

- Side effect observed: No

- Verdict: **ownership enforced**


### Check 4: Collection delete may be improperly exposed

- Endpoint: `/discovery/lists/user_items/`

- Sequence attempted: GET then DELETE collection under A/B

- A status: GET 200; DELETE 405

- B status: DELETE 405

- Cross-account result: not applicable

- Side effect observed: No

- Verdict: **method restricted**


### Check 5: Referral landing may accept unintended mutation method

- Endpoint: `/bonfire/crypto/rewards/referral_landing/`

- Sequence attempted: GET baseline then POST preview-like payload

- A status: GET 404; POST 404

- B status: POST 404

- Cross-account result: not applicable

- Side effect observed: No

- Verdict: **safe handling observed**


### Batch 4 correction note
- `POST /pathfinder/support_chats/` returned `200` and created chatbot inquiry IDs for both accounts (expected product behavior, **not** cross-account bypass).
- This is a stateful action (opens support chat), so subsequent checks should avoid this endpoint to prevent support-channel noise.

## Batch 5 — Strictly non-stateful checks

Run time: 2026-02-18T23:40:28


### Check 1: badge userUuid override

- Endpoint(s): `/inbox/notifications/badge`

- A status: A own/alt 200/200

- B status: B own/alt 200/200

- Cross-account result: A sig 82e74f847376/82e74f847376 ; B sig 13ec96969129/13ec96969129

- Side effect observed: No

- Verdict: **caller-bound, no cross leak observed**


### Check 2: kaizen foreign entity access

- Endpoint(s): `/kaizen/experiments/<user_uuid>/`

- A status: A on B 403

- B status: B on A 403

- Cross-account result: expect 403 mismatch

- Side effect observed: No

- Verdict: **ownership enforced**


### Check 3: cross-list replay

- Endpoint(s): `/discovery/lists/default + /discovery/lists/items`

- A status: A default 200

- B status: B default 200

- Cross-account result: A->B 404; B->A 404

- Side effect observed: No

- Verdict: **ownership enforced**


### Check 4: notifications stack cross leakage

- Endpoint(s): `/midlands/notifications/stack/`

- A status: A 200

- B status: B 200

- Cross-account result: sig 0275e5323da6/0275e5323da6

- Side effect observed: No

- Verdict: **no cross-account signal**


### Check 5: pathfinder issues active_only boundary

- Endpoint(s): `/pathfinder/issues/?active_only=True`

- A status: A 200

- B status: B 200

- Cross-account result: sig 4f53cda18c2b/4f53cda18c2b

- Side effect observed: No

- Verdict: **no cross-account signal**

## Batch 6 — Focused OAuth boundary checks (less-tested family) — STOP after promising lead

Run time: 2026-02-18T23:48–23:54+01:00

Scope note: SAFE unauthenticated/request-shape checks only. No token revocation attempts against real tokens; only dummy values.

### Check set A: Multi-family no-auth method matrix
Evidence file: `output/noauth_family_probe_20260218T2348.tsv`

- Probed GET/OPTIONS/POST across: `mobile.api`, `mobile-rest.api`, `auth.api`, `login.api`, `sso.api`, `orders.api`, `exchange.api`, `gws.api`, `api-streaming`, `nummus`, and OAuth endpoints on `api.robinhood.com`.
- Observations:
  - Several microservice hosts returned TLS handshake failure from this runtime (`status 000`), limiting direct method characterization.
  - `nummus` endpoints consistently returned `401` across tested methods (no bypass signal).
  - OAuth endpoints exposed differing parser behavior by endpoint and content type.

### Check set B: OAuth payload-shape differential (targeted)
Evidence file: `output/oauth_noauth_matrix_20260218T2351.tsv`

- `POST /oauth2/revoke_token/`:
  - JSON `{}` -> `400` (`Missing token parameter`)
  - JSON `{"token":"deadbeef"}` -> `400` with UUID-validation style detail
  - **Form-encoded `token=...` -> moved to focused repro due to anomalous server handling**
- Control endpoint `POST /oauth2/token/` with comparable no-auth payloads returned expected `400/401` (no 5xx observed in this set).

### Check set C: Focused reproducibility on revoke-token parser anomaly
Evidence files:
- `output/revoke_form_probe_20260218T2352.tsv`
- `output/revoke_500_repro_20260218T2354.tsv`

Deterministic result (3/3):
- `POST https://api.robinhood.com/oauth2/revoke_token/`
  - `Content-Type: application/x-www-form-urlencoded`
  - body `token=11111111-1111-1111-1111-111111111111`
  - => **HTTP 500** with generic server error HTML body (stable hash `fd62a53a...`)
- Same endpoint with JSON body (`{"token":"11111111-..."}`) => `400` (stable hash `57cde762...`)
- Control `POST /oauth2/token/` with form body remained `401` (stable hash `7fea647e...`)

### Batch 6 verdict
- **Promising lead identified** under criterion (3): endpoint accepts unexpected payload/content-type combination that triggers deterministic server-side failure on a security-sensitive OAuth revocation path.
- This is stronger than prior negative controls (which were mostly clean authz denials) because it indicates backend exception path reachable pre-auth via crafted request shape.
- Potential security relevance: unauthenticated error-path DoS surface and possibly deeper parser/auth-order flaw in revoke flow.
- Confidence: **medium** for the anomaly itself; **low-medium** for exploit impact pending load and authenticated-path validation.

## LA-005 impact validation

Run time: 2026-02-18T23:52–23:56+01:00  
Primary artifact: `output/la005_impact_matrix_20260218_235219.tsv`

### 1) Baseline 500 reproducibility and consistency
- Target: `POST https://api.robinhood.com/oauth2/revoke_token/`
- Request shape: unauthenticated, `Content-Type: application/x-www-form-urlencoded`, `token=<uuid-like>`
- Result: **6/6 returned HTTP 500**
- Body consistency: **stable hash** `fd62a53afdd4` for all baseline requests
- Latency (baseline): mean `0.74s` (min `0.175s`, max `1.089s`)

### 2) Input-class characterization (safe mini-batch)
- Total cases: 23 (low-rate, ~0.8s inter-request delay)
- Overall statuses: `500` x17, `400` x5, `415` x1

`/oauth2/revoke_token/` behavior by class:
- uuid-like / random strings / malformed non-empty / repeated token / URL-encoded edge cases => **500** (same 145-byte HTML error shape, same hash)
- `token=` (empty token) => **400** JSON `{"detail":"Empty value"}`
- missing token parameter (`foo=bar`) => **400** JSON invalid_request-style response

### 3) Neighboring controls
- Same endpoint with JSON body (`{"token":"<uuid>"}`) => **400** (UUID-validation-style JSON), not 500
- Same endpoint with `Content-Type: text/plain` => **415** unsupported media type
- Same endpoint with missing `Content-Type` (curl default form body) => **500**
- Control endpoint `POST /oauth2/token/` with both form and JSON shapes => **400** (unsupported_grant_type), no 5xx

### 4) Exploitability/impact indicators checked (non-destructive)
- **Error amplification signal:** deterministic 500 reachable pre-auth across many non-empty token variants (broad trigger condition)
- **Latency anomalies:** no extreme spikes observed in this bounded run (range stayed ~0.13–1.17s)
- **Leakage:** no stack traces or sensitive internals; generic 500 HTML only
- **Cache/proxy anomalies:** responses came via CloudFront with `X-Cache: Error from cloudfront`; no cache-hit behavior and no `Set-Cookie` observed

### Impact assessment (current)
- Confirmed: endpoint-specific pre-auth exception path on OAuth revoke surface.
- Not yet confirmed: practical service degradation at meaningful scale or security boundary bypass beyond informative 5xx.
- Recommendation: **hold and gather more** (safe low-rate resilience evidence + owned authenticated revoke-semantic check) before external submission.
- Confidence: **medium-high** on deterministic bug existence; **medium-low** on bounty-grade impact.


## LA-005 escalation pass (final)

Run time: 2026-02-19T00:32:10

- Scope: safe low-rate, unauth endpoint behavior only.

- Variants tested: content-type/body classes, header variance, HTTP method boundaries.


### Key findings

- form_uuid: status `500` (n=3), body_sig `fd62a53afdd4`, avg latency 938.9 ms.

- form_random32: status `500` (n=3), body_sig `fd62a53afdd4`, avg latency 907.2 ms.

- form_empty: status `400` (n=3), body_sig `eaeb210d842e`, avg latency 123.8 ms.

- form_missing: status `400` (n=3), body_sig `49a5d28f32e2`, avg latency 118.3 ms.

- json_uuid: status `400` (n=3), body_sig `57cde7625b72`, avg latency 127.7 ms.

- text_plain: status `415` (n=3), body_sig `762a6e823c29`, avg latency 219.3 ms.


### Header variance on form_uuid

- base: status `500`, sig `fd62a53afdd4`, avg 938.9 ms.

- no_accept: status `500`, sig `fd62a53afdd4`, avg 900.1 ms.

- accept_json: status `500`, sig `fd62a53afdd4`, avg 804.5 ms.

- accept_html: status `406`, sig `a5d55bea935e`, avg 113.6 ms.

- x_forwarded_proto_http: status `500`, sig `fd62a53afdd4`, avg 827.1 ms.


### Method boundary

- GET: status `405`, sig `0a7215324970`.

- PUT: status `405`, sig `a817fdc1bd7d`.

- PATCH: status `405`, sig `3e91ddbaf795`.

- DELETE: status `405`, sig `e93f84a99b10`.

- OPTIONS: status `405`, sig `a320a0c45616`.


### Final decision

- Deterministic pre-auth 500 remains reproducible primarily on non-empty `application/x-www-form-urlencoded` token payloads.

- No evidence of privilege bypass, data exposure, or high-amplification behavior in bounded tests.

- Recommendation: **Submit as reliability/security-hardening issue (low confidence security impact)** OR hold if program rejects pure 5xx stability issues.

- Evidence matrix: `/Users/mohamedfhafah/Desktop/PROJECTS/30_SECURITY_CTF/BUGBOUNTY/robinhood-bounty/output/la005_escalation_matrix_20260219_003210.tsv`

## High-value batch next (2026-02-19 01:10–01:35 CET)

Goal: run strict-ROI, low-noise pass on less-tested auth families with bounded SAFE checks only.

### Surface expansion + triage notes
- Tools executed: `httpx`, `ffuf`, Python request matrix (low-rate), plus archive attempts (`gau`, `waybackurls`) on less-tested subdomains.
- Archive coverage for selected microservice hosts returned no useful historical paths in this runtime.
- TLS/connectivity from this runtime to several `*.api.robinhood.com` microservice hosts remained limited (handshake/connect errors), so endpoint-differential focus stayed on reachable high-value surfaces: `api.robinhood.com` and `nummus.robinhood.com`.

### Top-10 high-ROI endpoints tested (not previously exhausted in prior batches)
1. `GET/OPTIONS/POST /oauth2/authorize/`
2. `GET/OPTIONS/POST /oauth2/token/` (incl. content-type boundary)
3. `GET/OPTIONS/POST /challenge/`
4. `GET/OPTIONS/POST /applications/`
5. `GET/OPTIONS/POST /mfa/`
6. `GET/OPTIONS/POST https://nummus.robinhood.com/`
7. `GET/OPTIONS/POST https://nummus.robinhood.com/accounts/`
8. `GET/OPTIONS/POST https://nummus.robinhood.com/orders/`
9. `GET/OPTIONS/POST https://nummus.robinhood.com/oauth2/token/`
10. Host-level method baseline on `api-streaming.robinhood.com/`

### Differential outcomes (bounded A/B-style request-shape/method comparisons)
- `Accept: text/html` consistently produced `406` across protected endpoints; JSON/`*/*` returned expected auth/method statuses (no bypass signal).
- `/oauth2/token/` behaved consistently (`GET 405`, `POST 400`, `OPTIONS 200`) with no 5xx.
- `/challenge/` exposed anonymous minimal object (`GET 200`, `{}`) and strict method control (`POST 405`), no mutation path observed.
- `/applications/` showed stable `POST 421` while `GET/OPTIONS 404`; reproducible parser/routing oddity but no security impact signal from this batch.
- `nummus` protected paths (`/accounts/`, `/orders/`) remained caller-auth gated (`401`) under all tested method/content-type variants.
- `api-streaming` root remained `404` for tested methods; no unauth endpoint behavior anomaly.

### Verdict
- No new medium+ confidence payout-likely AuthZ/business-logic finding beyond existing LA-005 in this pass.
- One low-confidence anomaly worth passive tracking only: `POST /applications/` deterministic `421` with `GET/OPTIONS 404`.
- Stop condition respected (no destructive/stateful actions; no support-channel noise).

### Artifacts
- `output/highvalue_batch_20260219/hosts.txt`
- `output/highvalue_batch_20260219/httpx_hosts.jsonl`
- `output/highvalue_batch_20260219/auth_surface_matrix.tsv`
- `output/highvalue_batch_20260219/top10_diff_matrix.tsv`
- `output/highvalue_batch_20260219/host_root_matrix.json`
- `surface/highvalue_shortlist_latest.md`
