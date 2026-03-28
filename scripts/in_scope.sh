#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCOPE_DIR="${SCRIPT_DIR}/../scope"

usage() {
  echo "Usage: ./scripts/in_scope.sh <host-or-url>"
}

trim() {
  local s="$1"
  s="${s#"${s%%[![:space:]]*}"}"
  s="${s%"${s##*[![:space:]]}"}"
  printf '%s' "$s"
}

normalize() {
  local raw="$1"
  raw="$(printf '%s' "$raw" | tr '[:upper:]' '[:lower:]')"
  raw="${raw#http://}"
  raw="${raw#https://}"
  raw="${raw%%#*}"
  raw="${raw%%\?*}"

  local host_path="$raw"
  local host="${host_path%%/*}"
  local path="/"

  if [[ "$host_path" == */* ]]; then
    path="/${host_path#*/}"
  fi

  host="${host%%:*}"
  host="${host#[}"
  host="${host%]}"

  if [[ "$path" != "/" ]]; then
    path="${path%/}"
  fi

  printf '%s %s' "$host" "$path"
}

match_pattern_file() {
  local value="$1"
  local file="$2"
  local pattern

  while IFS= read -r pattern || [[ -n "$pattern" ]]; do
    pattern="$(trim "$pattern")"
    [[ -z "$pattern" ]] && continue
    [[ "$pattern" == \#* ]] && continue

    if [[ "$value" == $pattern ]]; then
      printf '%s' "$pattern"
      return 0
    fi
  done < "$file"

  return 1
}

match_host_pattern_file() {
  local host="$1"
  local file="$2"
  local pattern

  while IFS= read -r pattern || [[ -n "$pattern" ]]; do
    pattern="$(trim "$pattern")"
    [[ -z "$pattern" ]] && continue
    [[ "$pattern" == \#* ]] && continue

    if [[ "$host" == $pattern ]]; then
      printf '%s' "$pattern"
      return 0
    fi

    # Treat an exact out-of-scope host as excluding all its subdomains too.
    if [[ "$pattern" != *"*"* && "$host" == *".${pattern}" ]]; then
      printf '%s (as-subdomain)' "$pattern"
      return 0
    fi
  done < "$file"

  return 1
}

if [[ $# -ne 1 ]]; then
  usage
  exit 1
fi

read -r host path <<< "$(normalize "$1")"
if [[ -z "$host" ]]; then
  echo "INVALID_INPUT"
  exit 4
fi

full_path="${host}${path}"
if path_pattern="$(match_pattern_file "$full_path" "${SCOPE_DIR}/out_of_scope_paths.txt" 2>/dev/null)"; then
  echo "OUT_OF_SCOPE_PATH ${host}${path} matched ${path_pattern}"
  exit 2
fi

if host_pattern="$(match_host_pattern_file "$host" "${SCOPE_DIR}/out_of_scope_hosts.txt" 2>/dev/null)"; then
  echo "OUT_OF_SCOPE_HOST ${host} matched ${host_pattern}"
  exit 2
fi

if tier_pattern="$(match_host_pattern_file "$host" "${SCOPE_DIR}/tier1_hosts.txt" 2>/dev/null)"; then
  echo "IN_SCOPE TIER1 ${host} matched ${tier_pattern}"
  exit 0
fi

if tier_pattern="$(match_host_pattern_file "$host" "${SCOPE_DIR}/tier2_hosts.txt" 2>/dev/null)"; then
  echo "IN_SCOPE TIER2 ${host} matched ${tier_pattern}"
  exit 0
fi

if tier_pattern="$(match_host_pattern_file "$host" "${SCOPE_DIR}/tier3_hosts.txt" 2>/dev/null)"; then
  echo "IN_SCOPE TIER3 ${host} matched ${tier_pattern}"
  exit 0
fi

echo "UNKNOWN_SCOPE ${host}"
exit 3
