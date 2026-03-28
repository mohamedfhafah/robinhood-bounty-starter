#!/usr/bin/env bash
set -euo pipefail

# Differential authorization probe for two user tokens on the same endpoint set.
# Use only with accounts you own and only on in-scope hosts.

if [[ $# -lt 1 ]]; then
  echo "Usage: ./scripts/authz_diff_probe.sh <output-file> [paths-file]"
  echo "Env required: RH_H1_USERNAME RH_TEST_ACCOUNT_EMAIL RH_TOKEN_A"
  echo "Env optional: RH_TOKEN_B"
  exit 1
fi

OUT_FILE="$1"
PATHS_FILE="${2:-}"

: "${RH_H1_USERNAME:?source scripts/rh_env.sh <h1_username> <test_account_email>}"
: "${RH_TEST_ACCOUNT_EMAIL:?source scripts/rh_env.sh <h1_username> <test_account_email>}"
: "${RH_TOKEN_A:?export RH_TOKEN_A='Bearer <token>'}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${SCRIPT_DIR}/.."
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

if [[ -z "$PATHS_FILE" ]]; then
  PATHS_FILE="${TMP_DIR}/default_paths.txt"
  cat > "$PATHS_FILE" <<'PATHS'
https://api.robinhood.com/accounts/
https://api.robinhood.com/orders/
https://api.robinhood.com/positions/
https://api.robinhood.com/portfolios/
https://api.robinhood.com/documents/
https://api.robinhood.com/watchlists/
https://api.robinhood.com/notifications/devices/
https://nummus.robinhood.com/accounts/
https://nummus.robinhood.com/orders/
https://cashier.robinhood.com/accounts/
PATHS
fi

: > "$OUT_FILE"
echo -e "url\tactor\tstatus\tbytes\tbody_sha256\tredirect" >> "$OUT_FILE"

run_actor() {
  local actor="$1"
  local token="$2"

  while IFS= read -r url || [[ -n "$url" ]]; do
    url="${url%%#*}"
    url="$(echo "$url" | xargs)"
    [[ -z "$url" ]] && continue

    body_file="${TMP_DIR}/body_${actor}_$(echo -n "$url" | shasum -a 256 | awk '{print $1}')"
    result="$(${ROOT_DIR}/scripts/rh_curl.sh -sS -o "$body_file" \
      -w "%{http_code}\t%{size_download}\t%{redirect_url}" \
      --max-time 15 \
      -H "Authorization: ${token}" \
      "$url" 2>/dev/null || true)"

    if [[ -z "$result" ]]; then
      echo -e "${url}\t${actor}\t000\t0\t\t" >> "$OUT_FILE"
    else
      sha="$(shasum -a 256 "$body_file" | awk '{print $1}')"
      echo -e "${url}\t${actor}\t${result}\t${sha}" >> "$OUT_FILE"
    fi

    sleep 0.25
  done < "$PATHS_FILE"
}

run_actor "A" "$RH_TOKEN_A"

if [[ -n "${RH_TOKEN_B:-}" ]]; then
  run_actor "B" "$RH_TOKEN_B"
fi

echo "[+] wrote: ${OUT_FILE}"
