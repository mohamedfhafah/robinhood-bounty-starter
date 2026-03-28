# Mobile-first Attack Surface Map (`com.robinhood.global`)

## Method / Constraints
- Built only from local campaign artifacts (no APK/runtime tooling used in this pass).
- Scope constrained to Robinhood in-scope API surface relevant to mobile workflows.
- Primary evidence files:
  - `output/campaign_20260217_205128/focus_targets.csv`
  - `output/campaign_20260217_205128/api_candidate_probe.tsv`
  - `output/campaign_20260217_205128/api_key_responses.txt`
  - `output/campaign_20260217_205128/api_followup_probe.txt`
  - `output/campaign_20260217_205128/live_priority_raw.tsv`

## Surface Buckets (Mobile-relevant)

### 1) Core brokerage API plane
- Host: `api.robinhood.com`
- Evidence:
  - 200 on `/` and live in priority set.
  - Auth gates present (401/405) for sensitive paths.
- Candidate high-value paths:
  - `/oauth2/token/`, `/oauth2/authorize/`, `/oauth2/revoke_token/`
  - `/accounts/`, `/portfolios/`, `/positions/`, `/orders/`, `/documents/`
  - `/options/orders/`, `/mfa/`

### 2) Public market-data plane (still mobile-consumed)
- Host: `api.robinhood.com`
- Evidence of unauth/public data responses (200):
  - `/instruments/`
  - `/quotes/`
  - `/markets/`
  - `/fundamentals/`
- Follow-on linked endpoints observed in responses:
  - `/markets/{MIC}/hours/{date}/`
  - `/instruments/{uuid}/splits/`

### 3) Notifications/device linkage plane
- Host: `api.robinhood.com`
- Evidence:
  - `/notifications/` returns link object with `devices` URL.
  - `/notifications/devices/` denies unauth with explicit auth metadata error.
- Candidate path:
  - `/notifications/devices/`

### 4) Crypto/mobile-adjacent backend plane
- Hosts:
  - `nummus.robinhood.com` (200, JSON-like responses)
  - `api.nummus.robinhood.com` (focus target)
  - `m.api.crypto.robinhood.com` (focus target)
  - `mobile.api.robinhood.com` (focus target)
  - `mobile-rest.api.robinhood.com` (focus target)
- Notes:
  - These are high-likelihood mobile backend edges but path-level confirmation is limited by current artifacts.

### 5) Funding / cashier plane
- Host: `cashier.robinhood.com`
- Evidence:
  - 200 root; `/health/` responds 200.
- Candidate financial paths (to validate cautiously with owned accounts):
  - `/transfers/`, `/ach/`, `/withdrawals/`, `/deposits/`

### 6) Session/auth adjacency (mobile login ecosystem)
- Hosts from focus shortlist:
  - `auth.api.robinhood.com`, `login.api.robinhood.com`, `sso.api.robinhood.com`
  - `auth.robinhood.com`, `login.robinhood.com`, `sso.robinhood.com`
- Notes:
  - Most were unresolved in conservative probe (`000`) but remain high-priority mobile auth surface candidates.

## Mobile-first testing priorities inferred
1. Auth/session boundary tests across `api.robinhood.com` OAuth + account/order endpoints.
2. Notification/device binding abuse checks around `/notifications/` ↔ `/notifications/devices/`.
3. Object-level authorization in account/trading resources (`/accounts/`, `/orders/`, `/positions/`, `/portfolios/`).
4. Cross-surface token handling between brokerage (`api.robinhood.com`) and crypto/mobile hosts (`nummus`, `mobile-rest`, `mobile.api`).

## Known blockers in this pass
- No local APK/manifest/runtime capture artifacts for `com.robinhood.global` were present in this workspace.
- Therefore no direct deeplink extraction, cert-pinning confirmation, or client-side storage findings were possible in this run.
