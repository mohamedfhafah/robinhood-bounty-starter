#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="${SCRIPT_DIR}/.."

if [[ $# -lt 1 ]]; then
  echo "Usage: ./scripts/active_probe_focus.sh <campaign_dir> [max_hosts]"
  echo "Example: ./scripts/active_probe_focus.sh ./output/campaign_20260217_205128 60"
  exit 1
fi

CAMPAIGN_DIR="$1"
MAX_HOSTS="${2:-60}"
FOCUS_FILE="${CAMPAIGN_DIR}/focus_targets.txt"
OUT_FILE="${CAMPAIGN_DIR}/active_probe_results.tsv"

: "${RH_H1_USERNAME:?source scripts/rh_env.sh <h1_username> <test_account_email>}"
: "${RH_TEST_ACCOUNT_EMAIL:?source scripts/rh_env.sh <h1_username> <test_account_email>}"

if [[ ! -f "$FOCUS_FILE" ]]; then
  echo "focus_targets.txt not found; building it now"
  python3 "${SCRIPT_DIR}/build_focus_targets.py" "$CAMPAIGN_DIR" "$MAX_HOSTS" 40
fi

: > "$OUT_FILE"
echo -e "host\turl\tstatus_code\ttotal_time_s\tredirect_url" >> "$OUT_FILE"

count=0
while IFS= read -r host; do
  [[ -z "$host" ]] && continue
  count=$((count + 1))
  if [[ "$count" -gt "$MAX_HOSTS" ]]; then
    break
  fi

  for scheme in https http; do
    url="${scheme}://${host}/"

    result="$(${BASE_DIR}/scripts/rh_curl.sh -sS -o /dev/null \
      -w "%{http_code}\t%{time_total}\t%{redirect_url}" \
      --max-time 10 \
      "$url" 2>/dev/null || true)"

    if [[ -n "$result" ]]; then
      echo -e "${host}\t${url}\t${result}" >> "$OUT_FILE"
      break
    fi
  done

  # Stay conservative and avoid burst traffic.
  sleep 0.4
done < "$FOCUS_FILE"

echo "[+] wrote: ${OUT_FILE}"
