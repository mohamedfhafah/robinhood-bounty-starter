#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="${SCRIPT_DIR}/.."
SCOPE_DIR="${BASE_DIR}/scope"
OUT_BASE="${BASE_DIR}/output"

DOMAINS_FILE="${1:-${SCOPE_DIR}/root_domains.txt}"

if [[ ! -f "$DOMAINS_FILE" ]]; then
  echo "Domains file not found: $DOMAINS_FILE"
  echo "Usage: ./scripts/run_campaign.sh [domains-file]"
  exit 1
fi

STAMP="$(date +%Y%m%d_%H%M%S)"
CAMPAIGN_DIR="${OUT_BASE}/campaign_${STAMP}"
mkdir -p "$CAMPAIGN_DIR"

RUN_SUBFINDER="${RUN_SUBFINDER:-1}"
RUN_AMASS="${RUN_AMASS:-1}"
RUN_HTTPX="${RUN_HTTPX:-0}"
REQUIRE_BOUNTY_HEADERS="${REQUIRE_BOUNTY_HEADERS:-1}"
AMASS_TIMEOUT_SECONDS="${AMASS_TIMEOUT_SECONDS:-120}"
HTTPX_TIMEOUT_SECONDS="${HTTPX_TIMEOUT_SECONDS:-120}"
CLASSIFY_JOBS="${CLASSIFY_JOBS:-16}"
HTTPX_THREADS="${HTTPX_THREADS:-20}"
HTTPX_RATE_LIMIT="${HTTPX_RATE_LIMIT:-5}"

if [[ "$RUN_HTTPX" == "1" && "$REQUIRE_BOUNTY_HEADERS" == "1" ]]; then
  if [[ -z "${RH_H1_USERNAME:-}" || -z "${RH_TEST_ACCOUNT_EMAIL:-}" ]]; then
    echo "[!] RUN_HTTPX=1 requested but missing RH_H1_USERNAME/RH_TEST_ACCOUNT_EMAIL"
    echo "[!] source scripts/rh_env.sh <h1_username> <test_account_email> first"
    echo "[!] continuing with RUN_HTTPX=0"
    RUN_HTTPX="0"
  fi
fi

echo "[+] campaign output: ${CAMPAIGN_DIR}"
echo "[+] settings: RUN_SUBFINDER=${RUN_SUBFINDER} RUN_AMASS=${RUN_AMASS} RUN_HTTPX=${RUN_HTTPX}"

while IFS= read -r domain || [[ -n "$domain" ]]; do
  domain="$(echo "$domain" | sed 's/#.*//' | xargs)"
  [[ -z "$domain" ]] && continue

  echo "[+] === domain: ${domain} ==="
  RUN_SUBFINDER="$RUN_SUBFINDER" \
  RUN_AMASS="$RUN_AMASS" \
  RUN_HTTPX="$RUN_HTTPX" \
  REQUIRE_BOUNTY_HEADERS="$REQUIRE_BOUNTY_HEADERS" \
  AMASS_TIMEOUT_SECONDS="$AMASS_TIMEOUT_SECONDS" \
  HTTPX_TIMEOUT_SECONDS="$HTTPX_TIMEOUT_SECONDS" \
  CLASSIFY_JOBS="$CLASSIFY_JOBS" \
  HTTPX_THREADS="$HTTPX_THREADS" \
  HTTPX_RATE_LIMIT="$HTTPX_RATE_LIMIT" \
  "${SCRIPT_DIR}/passive_recon.sh" "$domain" "$CAMPAIGN_DIR"
done < "$DOMAINS_FILE"

python3 "${SCRIPT_DIR}/aggregate_campaign.py" "$CAMPAIGN_DIR" "$SCOPE_DIR"

echo "[+] campaign complete"
