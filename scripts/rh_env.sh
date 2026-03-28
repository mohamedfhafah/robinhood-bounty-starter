#!/usr/bin/env bash
_rh_is_sourced=0
if [[ -n "${ZSH_VERSION-}" ]]; then
  case $ZSH_EVAL_CONTEXT in
    *:file) _rh_is_sourced=1 ;;
  esac
elif [[ -n "${BASH_VERSION-}" ]]; then
  if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
    _rh_is_sourced=1
  fi
fi

if [[ $_rh_is_sourced -eq 0 ]]; then
  echo "Source this file instead of executing it."
  echo "Usage: source scripts/rh_env.sh <h1_username> <test_account_email>"
  exit 1
fi

if [[ $# -ne 2 ]]; then
  echo "Usage: source scripts/rh_env.sh <h1_username> <test_account_email>"
  return 1 2>/dev/null || exit 1
fi

export RH_H1_USERNAME="$1"
export RH_TEST_ACCOUNT_EMAIL="$2"
export RH_HEADER_BUG_BOUNTY="X-Bug-Bounty: ${RH_H1_USERNAME}"
export RH_HEADER_TEST_ACCOUNT="X-Test-Account-Email: ${RH_TEST_ACCOUNT_EMAIL}"

echo "Robinhood bounty headers exported for ${RH_H1_USERNAME}."
