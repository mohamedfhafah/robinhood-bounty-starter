# Robinhood Report Readiness Checklist (Pass/Fail Gates)

> Use this checklist before promoting any finding to final submission.
> A single **FAIL** in mandatory gates means **NOT REPORT-READY**.

## Decision Rule
- **REPORT-READY** only if:
  - all **Mandatory Gates** are **PASS**, and
  - `verification_status=verified`, `safe_harbor_check=pass`, `report_ready=true`.
- Otherwise: **HOLD / REJECT / RE-TEST**.

---

## Gate 1 — Program & Scope Compliance (Mandatory)
- [ ] PASS / [ ] FAIL — Program target is `com.robinhood.global`.
- [ ] PASS / [ ] FAIL — Tested host/URL is in-scope for Robinhood policy.
- [ ] PASS / [ ] FAIL — Out-of-scope category check completed and documented.
- [ ] PASS / [ ] FAIL — Required bounty headers used where applicable:
  - `X-Bug-Bounty: <username>`
  - `X-Test-Account-Email: <test-account-email>`

**Fail conditions:** wrong target, ambiguous asset ownership, missing safe-harbor preconditions.

## Gate 2 — Contract Completeness (Mandatory)
Must satisfy `contracts/finding_contract.md` + `contracts/verified_contract.md`.
- [ ] PASS / [ ] FAIL — `id` present and unique.
- [ ] PASS / [ ] FAIL — `target_host` + `target_url` present.
- [ ] PASS / [ ] FAIL — `vuln_class` valid enum.
- [ ] PASS / [ ] FAIL — `summary` concise and factual.
- [ ] PASS / [ ] FAIL — `repro_steps` deterministic.
- [ ] PASS / [ ] FAIL — Evidence includes request + response + artifact paths.
- [ ] PASS / [ ] FAIL — `impact_statement` realistic and non-hyped.
- [ ] PASS / [ ] FAIL — `verification_status` set.
- [ ] PASS / [ ] FAIL — If rejected: `false_positive_reason` present.
- [ ] PASS / [ ] FAIL — `severity` present.
- [ ] PASS / [ ] FAIL — `business_impact` present.
- [ ] PASS / [ ] FAIL — `safe_harbor_check` present.
- [ ] PASS / [ ] FAIL — `report_ready` present.

**Fail conditions:** any required field missing or internally inconsistent.

## Gate 3 — Reproducibility Quality (Mandatory)
- [ ] PASS / [ ] FAIL — Reproduced from a fresh session/environment.
- [ ] PASS / [ ] FAIL — Steps are minimal, ordered, and deterministic.
- [ ] PASS / [ ] FAIL — Preconditions (role/account/version/flags) documented.
- [ ] PASS / [ ] FAIL — Expected vs actual behavior clearly shown.
- [ ] PASS / [ ] FAIL — Re-test by reviewer yields same result.

**Fail conditions:** flaky behavior, hidden prerequisites, non-repeatable PoC.

## Gate 4 — Evidence Quality & Integrity (Mandatory)
- [ ] PASS / [ ] FAIL — Raw request (or equivalent curl) included.
- [ ] PASS / [ ] FAIL — Raw response includes status and key body excerpt.
- [ ] PASS / [ ] FAIL — Artifacts (screenshots/HAR/logs) are referenced and accessible.
- [ ] PASS / [ ] FAIL — Sensitive data redacted safely without losing proof value.
- [ ] PASS / [ ] FAIL — Timestamp/context is sufficient for triage.

**Fail conditions:** evidence is summarized only, unverifiable, or redacted beyond usefulness.

## Gate 5 — Impact Demonstration (Mandatory, Impact-First)
- [ ] PASS / [ ] FAIL — Actual security impact was demonstrated (not theoretical only).
- [ ] PASS / [ ] FAIL — Data/action actually accessed, modified, or executed is explicit.
- [ ] PASS / [ ] FAIL — User/business consequence is specific to Robinhood context.
- [ ] PASS / [ ] FAIL — Non-demonstrated claims are explicitly excluded.
- [ ] PASS / [ ] FAIL — No inflation (e.g., account takeover claim without takeover evidence).

**Fail conditions:** impact is hypothetical, overclaimed, or detached from evidence.

## Gate 6 — Root-Cause & Dedupe Hygiene (Mandatory)
- [ ] PASS / [ ] FAIL — Probable root-cause described (control failure, trust boundary, authz gap, etc.).
- [ ] PASS / [ ] FAIL — Variant vs duplicate reasoning documented.
- [ ] PASS / [ ] FAIL — Same root cause across endpoints consolidated where appropriate.
- [ ] PASS / [ ] FAIL — Unique exploitation path preserved when materially different.

**Fail conditions:** duplicate submissions split artificially; no root-cause articulation.

## Gate 7 — Safe Harbor & Testing Conduct (Mandatory)
- [ ] PASS / [ ] FAIL — Testing stayed within safe-harbor constraints.
- [ ] PASS / [ ] FAIL — No prohibited actions (destructive access, broad scraping, privacy violations).
- [ ] PASS / [ ] FAIL — Used authorized test accounts and least-privilege approach.
- [ ] PASS / [ ] FAIL — Scope boundaries and stop conditions respected.

**Fail conditions:** any safe-harbor violation => do not submit until reviewed.

## Gate 8 — CVSS v3.1 Rationale (Mandatory for triage clarity)
- [ ] PASS / [ ] FAIL — CVSS vector provided (or explicit reason omitted).
- [ ] PASS / [ ] FAIL — Metrics align with evidence:
  - AV / AC / PR / UI / S / C / I / A
- [ ] PASS / [ ] FAIL — Score is consistent with demonstrated impact.
- [ ] PASS / [ ] FAIL — Narrative explains key metric choices in plain language.

**Fail conditions:** vector contradicts PoC (e.g., PR:N while authenticated exploit used).

## Gate 9 — Report Packaging for Triage (Mandatory)
- [ ] PASS / [ ] FAIL — Title is precise (asset + class + impact hint).
- [ ] PASS / [ ] FAIL — Executive summary is one paragraph, impact-first.
- [ ] PASS / [ ] FAIL — Verified findings and hypotheses are clearly separated.
- [ ] PASS / [ ] FAIL — Remediation guidance is actionable and proportionate.
- [ ] PASS / [ ] FAIL — Final metadata set: `verification_status=verified`, `safe_harbor_check=pass`, `report_ready=true`.

**Fail conditions:** mixed hypothesis/fact narrative, unclear ask for triager, missing final flags.

---

## Final Disposition
- Result: [ ] REPORT-READY  [ ] HOLD  [ ] REJECT
- Reviewer:
- Date/time:
- Blocking failures (if any):
- Required follow-ups:
