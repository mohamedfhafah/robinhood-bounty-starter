# Agent Log - Mobile-RE

- Status: PIVOT_MODE_ACTIVE (artifact-only pass complete; surface prioritization complete for next 48h)
- Objective: Extract mobile attack surface for `com.robinhood.global` from existing local project artifacts.
- Deliverables:
  - `surface/mobile_attack_surface.md` ✅
  - `surface/endpoints.jsonl` ✅
  - `runlogs/agents/mobile-re.md` ✅

## Progress Checkpoints
- [x] Campaign artifacts reviewed for mobile-relevant hosts/endpoints
- [x] Mobile-first attack-surface map drafted from local evidence only
- [x] Endpoint candidates populated in `surface/endpoints.jsonl` with source traceability
- [x] Scope constrained to Robinhood in-scope API context (focused on `robinhood.com` API surfaces)
- [x] Pivot prioritization completed: top-20 ROI queue produced (`surface/priority_queue.md`)
- [x] Next 48h execution plan produced (`runlogs/next_48h_plan.md`)
- [ ] APK baseline and versioning captured
- [ ] Deeplink map from manifest/resources extracted
- [ ] Sensitive storage / cert pinning observations captured

## Evidence Reviewed
- `output/campaign_20260217_205128/focus_targets.csv`
- `output/campaign_20260217_205128/api_candidate_probe.tsv`
- `output/campaign_20260217_205128/api_key_responses.txt`
- `output/campaign_20260217_205128/api_followup_probe.txt`
- `output/campaign_20260217_205128/live_priority_raw.tsv`

## Key Findings (artifact-derived)
- Confirmed core brokerage API surface on `https://api.robinhood.com` with multiple auth-gated resources (`/accounts/`, `/orders/`, `/portfolios/`, `/positions/`, `/mfa/`).
- Confirmed public market-data exposure paths (`/instruments/`, `/quotes/`, `/markets/`, `/fundamentals/`) useful for API graph expansion.
- Confirmed notification plane linkage (`/notifications/` exposing `/notifications/devices/`) with auth enforcement signal.
- Identified mobile/crypto-adjacent hosts from focus outputs: `mobile.api.robinhood.com`, `mobile-rest.api.robinhood.com`, `m.api.crypto.robinhood.com`, `api.nummus.robinhood.com`, `nummus.robinhood.com`.

## Blockers
- No APK or decompiled Android artifacts for `com.robinhood.global` were present in this repository snapshot.
- Therefore, no direct mobile client extraction was possible for:
  - AndroidManifest deeplinks/intent-filters
  - hardcoded endpoint constants
  - certificate pinning configuration
  - local storage/token handling behavior

## Pivot Mode Update (Surface Prioritizer)
- Completed ranked ROI queue for immediate testing without MITM: `surface/priority_queue.md`.
- Completed practical hour-by-hour plan for the next 48 hours: `runlogs/next_48h_plan.md`.
- Prioritization emphasis: object-level authorization (`/accounts`, `/orders`, `/positions`, `/portfolios`, `/documents`, `/watchlists`) first; then OAuth/MFA/session integrity; then cross-host/mobile/streaming boundaries.
- Recommended immediate prerequisite: obtain two owned-account bearer contexts (A/B) to execute high-confidence BOLA differential testing.
