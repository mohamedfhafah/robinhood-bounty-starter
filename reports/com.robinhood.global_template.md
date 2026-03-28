# [VERIFIED] <Vulnerability Title> (com.robinhood.global / <asset-host>)

> **Status:** Draft template instance for Robinhood campaign  
> **Rule:** Only populate from **verified** evidence. Keep hypotheses explicitly labeled.

## 1) Executive Summary
- **Vulnerability class:** <authz|idor|xss|ssrf|logic|other>
- **Affected asset:** <host / endpoint>
- **One-line impact:** <demonstrable security impact only>
- **Verification state:** verified | rejected | hypothesis (not reportable)

## 2) Scope & Program Compliance
- **Program target:** `com.robinhood.global`
- **Host / URL tested:**
- **In-scope validation performed:**
- **Out-of-scope issue types checked:**
- **Bug bounty headers used (if applicable):**
  - `X-Bug-Bounty: <username>`
  - `X-Test-Account-Email: <test-account-email>`

## 3) Reproduction Preconditions
- Account/role requirements:
- Environment assumptions:
- Any feature flags / app version constraints:

## 4) Step-by-Step Reproduction (Deterministic)
1. 
2. 
3. 

## 5) Proof of Concept Evidence
### Request Evidence
- Raw request / curl:

### Response Evidence
- HTTP status + key response excerpts:

### Artifact Files
- Screenshots / HAR / logs:
- Local file paths:

## 6) Demonstrable Impact (Required)
> Describe what was **actually accessed, modified, or executed** during testing.

- **Observed impact:**
- **Data/action reached:**
- **Why this matters to Robinhood users/business:**
- **What was NOT demonstrated (to avoid over-claiming):**

## 7) Severity Assessment
- **Initial severity suggestion:** informational | low | medium | high | critical
- **CVSS v3.1 vector:**
- **CVSS base score (initial):**
- **Rationale:**

## 8) Verification Metadata (from contract)
- `id`:
- `verification_status`:
- `false_positive_reason` (if rejected):
- `business_impact`:
- `safe_harbor_check`:
- `report_ready`:

## 9) Hypotheses / Follow-up (Non-verified)
> Keep separate from verified claims.

- Hypothesis A:
- Hypothesis B:
- Required additional validation:

## 10) Remediation Guidance
- Practical fix recommendation:
- Defense-in-depth controls:
- Suggested regression test:

## 11) Disclosure Quality Checklist
- [ ] Reproducible on fresh session
- [ ] Includes minimal deterministic steps
- [ ] Includes raw request/response evidence
- [ ] Demonstrates concrete impact (not theoretical only)
- [ ] No false or inflated claims
- [ ] Verified vs hypothesis clearly separated
