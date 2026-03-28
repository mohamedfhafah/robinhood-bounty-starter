# Example: Converting a Hypothesis into a Verified Robinhood Report Body

> Purpose: show how to move from suspicion to submission-grade evidence without overclaiming.

## 1) Initial Hypothesis (Not reportable yet)

**Hypothesis statement (acceptable):**
- "The account-statement download endpoint may allow IDOR by changing `statement_id` to another user value."

**Why this is not yet reportable:**
- No validated cross-account access proof.
- No deterministic reproduction.
- No demonstrated business impact.

---

## 2) Validation Plan (to reach verifiable state)

1. Use two authorized test accounts (A and B).
2. Capture a valid request from account A to fetch its own statement.
3. Replay with account A session but replace `statement_id` with account B value.
4. Record full request/response pairs for control and manipulated cases.
5. Confirm repeatability in fresh session.
6. Document exactly what data became accessible.

---

## 3) Evidence Collected (Example)

### Control Request (expected allowed)
```http
GET /api/v1/statements/7f8a-A-own.pdf HTTP/1.1
Host: api.example.robinhood.com
Authorization: Bearer <token_account_A>
X-Bug-Bounty: researcher_name
X-Test-Account-Email: testA@example.com
```

### Control Response
- `200 OK`
- Returns statement file for account A.

### Manipulated Request (test for IDOR)
```http
GET /api/v1/statements/2b11-B-other.pdf HTTP/1.1
Host: api.example.robinhood.com
Authorization: Bearer <token_account_A>
X-Bug-Bounty: researcher_name
X-Test-Account-Email: testA@example.com
```

### Manipulated Response (verified issue)
- `200 OK`
- Returns statement belonging to account B (name/account suffix differs from account A).

### Artifacts
- HAR: `artifacts/idor_statement_access.har`
- Screenshot: `artifacts/idor_statement_belongs_to_B.png`
- Notes: `artifacts/repro_notes.md`

---

## 4) From Hypothesis Text to Verified Report Text

### ❌ Overclaiming version (bad)
- "This gives full account takeover and complete platform compromise."

### ✅ Verified, bounded version (good)
- "An authenticated user (account A) can retrieve another user’s statement (account B) by modifying `statement_id`, demonstrating broken object-level authorization."
- "Demonstrated impact is unauthorized read access to another user’s financial statement data."
- "No account takeover, fund movement, or write action was demonstrated in this test."

---

## 5) Submission-Ready Body (Example)

### Executive Summary
An authenticated IDOR exists in the statement retrieval endpoint on `api.example.robinhood.com`. While logged in as test account A, replacing `statement_id` with a value from test account B returns B’s statement (`200 OK`). This demonstrates unauthorized cross-account data exposure.

### Reproduction Steps (deterministic)
1. Log in as test account A.
2. Request A’s own statement and capture request.
3. Replace `statement_id` in the same request with B’s known statement id.
4. Send request with A’s session token unchanged.
5. Observe `200 OK` and response content belonging to account B.
6. Repeat in a fresh session to confirm reproducibility.

### Demonstrable Impact
- Observed: unauthorized read access to another user’s statement document.
- Data reached: statement owner identity fields + financial statement contents.
- Business relevance: exposure of sensitive financial records between customers.
- Not demonstrated: privilege escalation beyond read, transaction execution, or account takeover.

### Severity & CVSS Rationale (example)
- Suggested severity: **High** (subject to program calibration).
- CVSS v3.1 example: `CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N`
- Rationale:
  - Network reachable endpoint (AV:N)
  - Simple parameter manipulation (AC:L)
  - Auth required (PR:L)
  - No victim interaction (UI:N)
  - High confidentiality impact from cross-account statement exposure (C:H)
  - No integrity or availability impact demonstrated (I:N/A:N)

### Metadata (contract-aligned)
- `verification_status`: verified
- `safe_harbor_check`: pass
- `report_ready`: true

---

## 6) Quick Anti-Overclaim Rules
- Claim only what artifacts prove.
- Separate "demonstrated" from "possible but unproven."
- If unsure, lower confidence and request follow-up testing.
- Prefer precise scope language ("statement endpoint") over broad platform claims.
