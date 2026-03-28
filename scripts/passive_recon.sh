#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: ./scripts/passive_recon.sh <root-domain> [output-dir]"
  echo "Example: ./scripts/passive_recon.sh robinhood.com"
  exit 1
fi

ROOT_DOMAIN="$1"
BASE_OUT_DIR="${2:-./output}"
STAMP="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="${BASE_OUT_DIR}/${ROOT_DOMAIN}_${STAMP}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCOPE_CHECKER="${SCRIPT_DIR}/in_scope.sh"
AMASS_TIMEOUT_SECONDS="${AMASS_TIMEOUT_SECONDS:-180}"
HTTPX_TIMEOUT_SECONDS="${HTTPX_TIMEOUT_SECONDS:-180}"
CLASSIFY_JOBS="${CLASSIFY_JOBS:-16}"
RUN_SUBFINDER="${RUN_SUBFINDER:-1}"
RUN_AMASS="${RUN_AMASS:-1}"
RUN_HTTPX="${RUN_HTTPX:-1}"
REQUIRE_BOUNTY_HEADERS="${REQUIRE_BOUNTY_HEADERS:-1}"
HTTPX_THREADS="${HTTPX_THREADS:-20}"
HTTPX_RATE_LIMIT="${HTTPX_RATE_LIMIT:-5}"

mkdir -p "$OUT_DIR"

have() {
  command -v "$1" >/dev/null 2>&1
}

echo "[+] Passive recon for ${ROOT_DOMAIN}"

echo "[+] Running subfinder (passive)"
if [[ "$RUN_SUBFINDER" == "1" ]] && have subfinder; then
  subfinder -silent -d "$ROOT_DOMAIN" > "${OUT_DIR}/subfinder.txt" || true
else
  : > "${OUT_DIR}/subfinder.txt"
  echo "[!] subfinder skipped or not found"
fi

echo "[+] Running amass passive"
if [[ "$RUN_AMASS" == "1" ]] && have amass; then
  if have timeout; then
    if ! timeout "$AMASS_TIMEOUT_SECONDS" amass enum -passive -norecursive -d "$ROOT_DOMAIN" -silent > "${OUT_DIR}/amass_passive.txt" 2>/dev/null; then
      timeout "$AMASS_TIMEOUT_SECONDS" amass enum -passive -d "$ROOT_DOMAIN" -silent > "${OUT_DIR}/amass_passive.txt" || true
    fi
  else
    if ! amass enum -passive -norecursive -d "$ROOT_DOMAIN" -silent > "${OUT_DIR}/amass_passive.txt" 2>/dev/null; then
      amass enum -passive -d "$ROOT_DOMAIN" -silent > "${OUT_DIR}/amass_passive.txt" || true
    fi
  fi
else
  : > "${OUT_DIR}/amass_passive.txt"
  echo "[!] amass skipped or not found"
fi

cat "${OUT_DIR}/subfinder.txt" "${OUT_DIR}/amass_passive.txt" \
  | tr '[:upper:]' '[:lower:]' \
  | sed '/^[[:space:]]*$/d' \
  | rg '^[a-z0-9.-]+$' \
  | rg '\.' \
  | rg -v '^_|\\._' \
  | sed '/\\.\\./d' \
  | sort -u > "${OUT_DIR}/discovered_hosts.txt"

: > "${OUT_DIR}/in_scope_hosts.txt"
: > "${OUT_DIR}/out_or_unknown_hosts.txt"
: > "${OUT_DIR}/scope_classification.txt"

if [[ -s "${OUT_DIR}/discovered_hosts.txt" ]]; then
  xargs -P "$CLASSIFY_JOBS" -I{} "$SCOPE_CHECKER" "{}" \
    < "${OUT_DIR}/discovered_hosts.txt" \
    > "${OUT_DIR}/scope_classification.txt" 2>/dev/null || true
fi

awk '$1 == "IN_SCOPE" {print $3}' "${OUT_DIR}/scope_classification.txt" \
  | sed '/^[[:space:]]*$/d' \
  | sort -u > "${OUT_DIR}/in_scope_hosts.txt"

awk '$1 != "IN_SCOPE" {print $2}' "${OUT_DIR}/scope_classification.txt" \
  | sed '/^[[:space:]]*$/d' \
  | sort -u > "${OUT_DIR}/out_or_unknown_hosts.txt"

if [[ "$RUN_HTTPX" == "1" ]] && have httpx && [[ -s "${OUT_DIR}/in_scope_hosts.txt" ]]; then
  echo "[+] Probing live in-scope hosts with conservative limits"
  : > "${OUT_DIR}/httpx_alive.txt"

  if [[ "$REQUIRE_BOUNTY_HEADERS" == "1" ]]; then
    if [[ -z "${RH_H1_USERNAME:-}" || -z "${RH_TEST_ACCOUNT_EMAIL:-}" ]]; then
      echo "[!] skipping httpx: set RH_H1_USERNAME and RH_TEST_ACCOUNT_EMAIL (or source scripts/rh_env.sh)"
      echo "[!] override with REQUIRE_BOUNTY_HEADERS=0 only if program policy permits"
      RUN_HTTPX="0"
    fi
  fi

  if [[ "$RUN_HTTPX" == "1" ]]; then
    httpx_cmd=(
      httpx
      -l "${OUT_DIR}/in_scope_hosts.txt"
      -silent
      -title
      -status-code
      -web-server
      -tech-detect
      -threads "$HTTPX_THREADS"
      -rate-limit "$HTTPX_RATE_LIMIT"
      -timeout 8
      -retries 1
    )

    if [[ -n "${RH_H1_USERNAME:-}" && -n "${RH_TEST_ACCOUNT_EMAIL:-}" ]]; then
      httpx_cmd+=(-H "X-Bug-Bounty: ${RH_H1_USERNAME}")
      httpx_cmd+=(-H "X-Test-Account-Email: ${RH_TEST_ACCOUNT_EMAIL}")
    fi
  fi

  if [[ "$RUN_HTTPX" == "1" ]] && have timeout; then
    timeout "$HTTPX_TIMEOUT_SECONDS" "${httpx_cmd[@]}" > "${OUT_DIR}/httpx_alive.txt" || true
  elif [[ "$RUN_HTTPX" == "1" ]]; then
    "${httpx_cmd[@]}" > "${OUT_DIR}/httpx_alive.txt" || true
  fi
else
  : > "${OUT_DIR}/httpx_alive.txt"
  echo "[!] httpx skipped, not found, or no in-scope hosts"
fi

total=$(wc -l < "${OUT_DIR}/discovered_hosts.txt" | tr -d ' ')
in_scope=$(wc -l < "${OUT_DIR}/in_scope_hosts.txt" | tr -d ' ')
live=$(wc -l < "${OUT_DIR}/httpx_alive.txt" | tr -d ' ')

echo "[+] Done"
echo "    output: ${OUT_DIR}"
echo "    discovered hosts: ${total}"
echo "    in-scope hosts: ${in_scope}"
echo "    live in-scope hosts: ${live}"
