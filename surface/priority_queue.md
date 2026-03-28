# Priority Queue (Next 48h, No MITM)

Scoring: **Effort 1 (lowest) → 5 (highest)**. Impact reflects likely bounty/security severity if confirmed.

| Rank | Target endpoint / flow | Why now (ROI reason) | Likely vuln class | Required auth context | Effort | Impact potential |
|---|---|---|---|---|---:|---|
| 1 | `GET /accounts/` + object URLs replay across two owned accounts | Proven auth-gated core object root; fastest path to BOLA evidence | BOLA/IDOR | Two owned bearer tokens (A/B) | 2 | Critical |
| 2 | `GET/POST /orders/` cross-account object replay | Trading objects are high-value and usually bounty-rewarded | BOLA/privilege bypass | Two owned bearer tokens (A/B) | 3 | Critical |
| 3 | `GET /positions/` cross-account object replay | Position data is sensitive financial state | BOLA/data exposure | Two owned bearer tokens (A/B) | 2 | High |
| 4 | `GET /portfolios/` cross-account object replay | Portfolio aggregates often miss object ownership checks | BOLA | Two owned bearer tokens (A/B) | 2 | High |
| 5 | `GET /documents/` direct URL/object reuse | Document endpoints often leak PII if UUID ownership weak | BOLA/PII disclosure | Two owned bearer tokens (A/B) | 3 | Critical |
| 6 | `GET/PUT/DELETE /watchlists/` foreign object attempts | User-generated objects are frequent authz weak points | BOLA/mass assignment | Two owned bearer tokens (A/B) | 3 | High |
| 7 | `GET/POST /notifications/devices/` foreign-device operations | Explicit auth metadata gate seen; device binding logic likely rich | Broken object auth / account-device binding flaws | Valid bearer token(s), preferably A/B | 3 | High |
| 8 | `/oauth2/authorize/` parameter tampering (`redirect_uri`, `state`, `scope`) | Auth edge already confirmed; high-impact if flow integrity weak | OAuth misconfiguration/open redirect/code interception | Logged-in owned account | 4 | Critical |
| 9 | `POST /oauth2/token/` grant-type abuse & client binding checks | Endpoint exists (405 on GET), likely strict POST logic to validate | OAuth token issuance abuse | Owned app/client context + account | 4 | Critical |
|10| `POST /oauth2/revoke_token/` token confusion/revocation bypass | Revocation bugs can preserve compromised sessions | Session invalidation flaws | Valid and invalid tokens | 3 | Medium-High |
|11| `GET /mfa/` + MFA/session step-up boundary tests | MFA surface confirmed; check token replay after MFA | MFA bypass/session fixation | Two sessions/tokens with different MFA state | 4 | Critical |
|12| `api.robinhood.com` token reuse on `nummus.robinhood.com/accounts/` | Cross-service auth boundary already hinted by 401 signals | Token audience/scope confusion | Valid `api` bearer token | 3 | High |
|13| `nummus.robinhood.com/orders/` with `api` token then crypto-context token | Tests service-to-service scope segregation | Broken access control / scope mixup | At least one valid token; ideally crypto-enabled account | 4 | High |
|14| `mobile.api.robinhood.com` endpoint discovery + auth behavior matrix | Explicit mobile edge, currently under-explored | Misconfigured auth/CORS/rate-limit | Unauth first, then owned bearer | 2 | High |
|15| `mobile-rest.api.robinhood.com` endpoint discovery + auth matrix | High-likelihood mobile BFF plane; low current visibility | Broken authz/API gateway policy gaps | Unauth + owned bearer | 2 | High |
|16| `auth.api.robinhood.com` / `login.api.robinhood.com` basic flow fuzz | Auth microservices can expose inconsistent protections | Auth bypass/account enumeration | Mostly unauth + owned account for safe checks | 3 | High |
|17| `sso.api.robinhood.com` SSO parameter integrity tests | SSO paths are commonly high-severity when weak | SSO misbinding / open redirect / token leakage | Owned login session | 4 | Critical |
|18| `orders.api.robinhood.com` route discovery vs `/orders/` parity | Microservice drift can create weaker policy copy | Inconsistent authz across service boundary | Owned bearer token | 3 | High |
|19| `exchange.api.robinhood.com` request shaping + authorization checks | Trading backend edge may trust upstream too much | Missing authz / privilege escalation | Owned bearer token | 4 | High |
|20| `api-streaming.robinhood.com` + `gws.api.robinhood.com` handshake auth tests | Streaming channels often miss per-topic auth checks | Broken channel authorization / data leakage | Valid token; optional websocket client | 4 | High |

## Fast triage order (first pass)
1. Ranks 1–7 (direct BOLA/object authz checks)
2. Ranks 8–11 (OAuth + MFA integrity)
3. Ranks 12–20 (cross-host/service boundary tests)

## Evidence basis
- `surface/endpoints.jsonl`
- `surface/mobile_attack_surface.md`
- `runlogs/agents/traffic-auth.md`
- `runlogs/agents/mobile-re.md`
