# Verification Plan (Owned-Account Safe) — AuthZ/IDOR Hypotheses

Date: 2026-02-18
Scope: Verification planning only (no vulnerability claims). No mobile MITM required.
Sources: `vulns/candidates/idor_authz.jsonl`, `surface/endpoints.jsonl`, `runlogs/agents/traffic-auth.md`, contracts.

## Preconditions (apply to all candidates)

1. Use two fully owned in-scope test accounts: **Account A** and **Account B**.
2. Capture valid auth contexts via normal login flows (no credential stuffing, no third-party accounts).
3. Include required bounty headers in all requests:
   - `X-Bug-Bounty: <h1_username>`
   - `X-Test-Account-Email: <owned_test_email>`
4. Keep request rate low; record UTC timestamps for every run.
5. Preserve raw evidence: request, response status, key body fields, and correlation IDs.

---

## Prioritization

1. **LA-001 (Highest):** core account-scoped objects, strongest direct customer-data impact.
2. **LA-004 (High):** order-state logic can have direct financial impact, but higher operational care needed.
3. **LA-002 (Medium):** auth-context/header confusion at notification device boundary.
4. **LA-003 (Medium):** cross-environment/header-family confusion hypothesis on X1 GraphQL.

---

## LA-001 — Potential BOLA/IDOR on account-scoped REST objects
Candidate: `RH-2026-LA-001`

### Test steps
1. With token A, enumerate only A-owned objects from:
   - `/accounts/`, `/orders/`, `/positions/`, `/watchlists/`, `/documents/` (as available)
2. Build a test matrix of object URLs/IDs (`object_url`, `owner=A`).
3. Replay **read** operations against A objects using token B.
4. Replay low-risk **write** operations where safe (e.g., watchlist metadata), never market-moving actions.
5. Repeat inverse direction (B objects with token A).
6. Compare response tuples: `(status, error code, body hash, owner-linked fields)`.

### Expected signals
- **Secure behavior (expected):** 401/403/404 for foreign object access; no foreign data fields returned.
- **Potential issue signal:** 200/2xx on foreign object read/write, or leaked sensitive fields from foreign object on non-2xx.

### Evidence checklist
- Account ownership mapping table (A vs B object IDs).
- Raw request/response pairs for baseline and cross-account attempts.
- Diff output proving behavior change with only token swap.
- Minimal reproducible sequence (3–5 calls).

### Decision gates
- **Gate 1 (continue):** at least one deterministic cross-account differential observed twice.
- **Gate 2 (reject hypothesis):** all foreign-object tests consistently denied with no data leakage.
- **Gate 3 (escalate for verification):** repeatable unauthorized read/write with clear object ownership evidence.

---

## LA-004 — Potential order lifecycle sequence/race flaw
Candidate: `RH-2026-LA-004`

### Test steps
1. Use owned funded sandbox-appropriate setup and smallest permissible order sizes.
2. Establish baseline single-thread order lifecycle behavior (place/cancel/replace).
3. Run controlled concurrency tests (2–5 parallel requests) around transition windows:
   - cancel+replace race
   - duplicate modify attempts
   - stale-state replay attempts
4. Correlate final order state, fills, balances, and positions.
5. Re-run same sequence at least 3 times for determinism.

### Expected signals
- **Secure behavior (expected):** single consistent terminal state; duplicate/replayed actions rejected.
- **Potential issue signal:** inconsistent terminal states, duplicate execution, or authorization accepted for stale state/action.

### Evidence checklist
- Exact timeline (ms where possible) for each parallel request.
- Order IDs, pre/post state snapshots, and account balance/position deltas.
- Repro script/command set and run count with consistent anomalies.

### Decision gates
- **Gate 1 (continue):** anomaly reproducible across >=2 runs.
- **Gate 2 (reject hypothesis):** no state inconsistencies beyond transient UI delay.
- **Gate 3 (escalate for verification):** deterministic backend state violation with measurable side effect.

---

## LA-002 — Potential Authorization metadata/header confusion on notifications devices
Candidate: `RH-2026-LA-002`

### Test steps
1. Baseline with valid token on `/notifications/devices/` and confirm normal account-scoped behavior.
2. Test benign header-shape variants (case/canonicalization/duplicate `Authorization`) one variable at a time.
3. Test forwarding-header noise (`X-Forwarded-*`) without spoofing infra ownership claims.
4. Validate responses never cross account boundaries (A token should never expose B devices).
5. Repeat any anomalous case with fresh tokens.

### Expected signals
- **Secure behavior (expected):** strict auth parsing; invalid/ambiguous auth rejected; only caller-owned device records returned.
- **Potential issue signal:** auth accepted in malformed/ambiguous states, or foreign device records/actions possible.

### Evidence checklist
- Header matrix table (variant → status/body/error code).
- Baseline vs variant diffs with identical method/path.
- Proof of ownership for any returned device record.

### Decision gates
- **Gate 1 (continue):** unexpected acceptance of malformed/ambiguous auth observed.
- **Gate 2 (reject hypothesis):** all malformed variants denied and no cross-account data.
- **Gate 3 (escalate for verification):** reproducible auth-context confusion causing unauthorized access/effect.

---

## LA-003 — Potential cross-environment identity-header confusion (X1 GraphQL)
Candidate: `RH-2026-LA-003`

### Test steps
1. Obtain valid owned contexts for both intended environments (prod/staging) if program-allowed.
2. Establish baseline per host with correct header family/token.
3. Execute controlled matrix:
   - prod token + prod headers to staging host
   - staging token + staging headers to prod host
   - mixed `Authorization` with mismatched `X-Thrive-*` families
4. Restrict queries to safe identity/account-self reads only.
5. Validate object ownership remains caller-scoped in every accepted response.

### Expected signals
- **Secure behavior (expected):** strict environment and header-family segregation; mismatches rejected.
- **Potential issue signal:** cross-environment credential acceptance or caller receiving foreign-account data.

### Evidence checklist
- Host/header/token matrix with outcomes.
- Raw GraphQL requests/responses for baseline vs mismatch cases.
- Ownership proof for any returned identifiers.

### Decision gates
- **Gate 1 (continue):** any mismatch combination unexpectedly accepted.
- **Gate 2 (reject hypothesis):** all mismatches denied; accepted responses remain correctly scoped.
- **Gate 3 (escalate for verification):** deterministic boundary bypass with unauthorized data/action.

---

## Cross-candidate evidence minimum for promotion (per verified contract)

Before promoting any hypothesis beyond planning/testing:
- Deterministic reproducibility documented.
- Clear unauthorized condition shown (not just error-message variance).
- Business impact statement tied to observed behavior.
- Safe-harbor compliance confirmed.
- Sufficient artifacts for `verification_status` decision under `contracts/verified_contract.md`.

## Current status
All LA-001..LA-004 remain **hypotheses** pending owned-account execution and evidence collection.