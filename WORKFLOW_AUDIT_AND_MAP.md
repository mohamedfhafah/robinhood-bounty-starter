# Workflow Audit + Agent Mapping (v1)

Date: 2026-02-18

## 1) Architecture audit (current state)

## Strengths
- Clear scope separation in `scope/` with explicit out-of-scope host/path/type files.
- Guardrail wrappers exist (`in_scope.sh`, `rh_curl.sh`, `rh_env.sh`) to enforce compliant headers.
- Recon pipeline is staged (`passive_recon.sh` -> `run_campaign.sh` -> `aggregate_campaign.py` -> `build_focus_targets.py`).
- Conservative active probing (`active_probe_focus.sh`) includes pacing and capped host counts.
- Authz differential probe exists (`authz_diff_probe.sh`) with owned-account token model.
- AG2 team architecture exists with manager + specialists and optional local `ExecAgent`.

## Fragilities / gaps
1. No strict machine-validated handoff schema between stages (JSONL contracts missing).
2. Vuln research is broad; no per-class hunter role contracts (XSS/IDOR/SSRF etc.) yet.
3. No artifact quality gate (reject finding lacking repro/evidence/impact/confidence).
4. Reporting readiness is template-based but not enforced by pre-submit checks.
5. Run output consistency can drift across agents without a validator.

---

## 2) Mapping current agents to target multi-agent workflow

| Target workflow role | Existing equivalent | Status | Notes |
|---|---|---|---|
| Scope Guardian | `ScopeGuardian` | ✅ Exists | Good policy gate, keep as hard pre-check before active steps. |
| Recon Agent | `ReconAgent` + scripts | ✅ Exists | Strong passive base. |
| Surface Mapper | Partial (`ReconAgent`, campaign artifacts) | ⚠️ Partial | Endpoints/params extraction contract should be explicit. |
| Vuln Hunter (parallel by class) | `VulnResearchAgent` | ⚠️ Broad only | Split into class-specialized workers for parallel depth. |
| PoC Verifier | `ExploitationAgent` (partial) | ⚠️ Partial | Needs explicit false-positive rejection criteria and scoring output. |
| Report Writer | `ReportingAgent` | ✅ Exists | Add pre-submit lint for completeness. |
| Intelligence/Lessons | `IntelligenceAgent` | ✅ Exists | Good for iterative improvement. |

---

## 3) Missing pieces created in this pass

1. `contracts/finding_contract.md` (strict finding handoff)
2. `contracts/verified_contract.md` (strict verified finding contract)
3. `scripts/readiness_check.sh` (one-shot environment + syntax + AG2 dry-run)
4. `scripts/validate_findings.py` (quality gate for required fields)

---

## 4) Readiness result summary

Checked on host:
- Tool binaries: `subfinder`, `amass`, `httpx`, `rg`, `jq`, `python3` -> present.
- Shell syntax for all scripts in `scripts/` -> pass.
- AG2 dry run (`ag2/run_team.py --dry-run`) -> pass.

Operationally ready for next bounded campaign run.

---

## 5) Immediate next improvements (high ROI)

1. Add per-class hunter prompt files (`vuln_hunter_xss.md`, `vuln_hunter_idor.md`, `vuln_hunter_ssrf.md`) with fixed output schema.
2. Wire validator as mandatory gate before report generation.
3. Add `verified/index.csv` auto-build step.
4. Add deterministic run manifest (`runlogs/manifest.json`) containing tool versions, env knobs, and timestamps.
