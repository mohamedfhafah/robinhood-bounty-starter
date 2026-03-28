# Finding Contract (Candidate)

Every candidate finding MUST include:

- `id`: unique id (e.g., RH-2026-0001)
- `target_host`
- `target_url`
- `vuln_class` (xss|idor|ssrf|authz|sqli|logic|other)
- `summary` (1-2 lines)
- `evidence`:
  - request (raw or curl)
  - response (status + key body excerpt)
  - artifact paths (screenshots/log files)
- `repro_steps` (minimal deterministic list)
- `impact_statement` (realistic, non-hyped)
- `confidence` (low|medium|high)
- `need_human_review` (true|false)

Reject candidate if any mandatory section is missing.
