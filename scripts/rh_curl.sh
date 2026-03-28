#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: ./scripts/rh_curl.sh <curl args...>"
  echo "Example: ./scripts/rh_curl.sh -i https://api.robinhood.com/"
  exit 1
fi

: "${RH_H1_USERNAME:?Run: source scripts/rh_env.sh <h1_username> <test_account_email>}"
: "${RH_TEST_ACCOUNT_EMAIL:?Run: source scripts/rh_env.sh <h1_username> <test_account_email>}"

exec curl "$@" \
  -H "X-Bug-Bounty: ${RH_H1_USERNAME}" \
  -H "X-Test-Account-Email: ${RH_TEST_ACCOUNT_EMAIL}"
