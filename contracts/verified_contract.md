# Verified Finding Contract

A verified finding MUST include everything from candidate contract plus:

- `verification_status`: verified|rejected
- `false_positive_reason` (required if rejected)
- `severity` (informational|low|medium|high|critical)
- `cvss_vector` (optional but recommended)
- `business_impact`
- `safe_harbor_check`: pass|fail
- `report_ready`: true|false

Only `verification_status=verified` and `report_ready=true` should be promoted to report generation.
