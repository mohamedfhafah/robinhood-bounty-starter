#!/bin/bash
# BOLA/IDOR Systematic Hunt - Robinhood EU
# Phase 1: Enumerate objects from A and B, then cross-replay

set -euo pipefail

TOKEN_A="$RH_TOKEN_A"
TOKEN_B="$RH_TOKEN_B"
USER_A="47429b1f-a717-4e4d-a6e0-d504dd1a5825"
USER_B="a04cbcdc-e9d5-4669-b993-1802ccae9a77"
BASE="https://api.robinhood.com"
OUTDIR="/Users/mohamedfhafah/Desktop/PROJECTS/30_SECURITY_CTF/BUGBOUNTY/robinhood-bounty/output/bola_$(date +%Y%m%dT%H%M%S)"
mkdir -p "$OUTDIR"

UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

do_req() {
  local label="$1" url="$2" token="$3" outfile="$4"
  local status body_hash
  resp=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $token" -H "User-Agent: $UA" -H "Accept: application/json" "$url" 2>/dev/null)
  status=$(echo "$resp" | tail -1)
  body=$(echo "$resp" | sed '$d')
  body_hash=$(echo "$body" | sha256sum | cut -c1-16)
  echo -e "$label\t$status\t$body_hash\t$(echo "$body" | head -c 500)" >> "$outfile"
  echo "$body"
}

echo "=== BOLA Hunt started at $(date -u) ==="
echo "Output: $OUTDIR"

# ─── Step 1: Enumerate /accounts/ ───
echo "[1/6] Enumerating /accounts/..."
ACCTS_A=$(do_req "accounts_A_own" "$BASE/accounts/" "$TOKEN_A" "$OUTDIR/enum.tsv")
ACCTS_B=$(do_req "accounts_B_own" "$BASE/accounts/" "$TOKEN_B" "$OUTDIR/enum.tsv")

echo "$ACCTS_A" > "$OUTDIR/accounts_A.json"
echo "$ACCTS_B" > "$OUTDIR/accounts_B.json"

# Extract account URLs/IDs
ACCT_URLS_A=$(echo "$ACCTS_A" | python3 -c "import sys,json; d=json.load(sys.stdin); [print(r.get('url','') or r.get('id','')) for r in d.get('results',d if isinstance(d,list) else [])]" 2>/dev/null || echo "PARSE_FAIL")
ACCT_URLS_B=$(echo "$ACCTS_B" | python3 -c "import sys,json; d=json.load(sys.stdin); [print(r.get('url','') or r.get('id','')) for r in d.get('results',d if isinstance(d,list) else [])]" 2>/dev/null || echo "PARSE_FAIL")

echo "Account A URLs: $ACCT_URLS_A"
echo "Account B URLs: $ACCT_URLS_B"

# ─── Step 2: Enumerate /portfolios/ ───
echo "[2/6] Enumerating /portfolios/..."
PORT_A=$(do_req "portfolios_A_own" "$BASE/portfolios/" "$TOKEN_A" "$OUTDIR/enum.tsv")
PORT_B=$(do_req "portfolios_B_own" "$BASE/portfolios/" "$TOKEN_B" "$OUTDIR/enum.tsv")
echo "$PORT_A" > "$OUTDIR/portfolios_A.json"
echo "$PORT_B" > "$OUTDIR/portfolios_B.json"

# ─── Step 3: Enumerate /positions/ ───
echo "[3/6] Enumerating /positions/..."
POS_A=$(do_req "positions_A_own" "$BASE/positions/" "$TOKEN_A" "$OUTDIR/enum.tsv")
POS_B=$(do_req "positions_B_own" "$BASE/positions/" "$TOKEN_B" "$OUTDIR/enum.tsv")
echo "$POS_A" > "$OUTDIR/positions_A.json"
echo "$POS_B" > "$OUTDIR/positions_B.json"

# ─── Step 4: Enumerate /orders/ ───
echo "[4/6] Enumerating /orders/..."
ORD_A=$(do_req "orders_A_own" "$BASE/orders/" "$TOKEN_A" "$OUTDIR/enum.tsv")
ORD_B=$(do_req "orders_B_own" "$BASE/orders/" "$TOKEN_B" "$OUTDIR/enum.tsv")
echo "$ORD_A" > "$OUTDIR/orders_A.json"
echo "$ORD_B" > "$OUTDIR/orders_B.json"

# ─── Step 5: Enumerate /watchlists/ ───
echo "[5/6] Enumerating /watchlists/..."
WL_A=$(do_req "watchlists_A_own" "$BASE/watchlists/" "$TOKEN_A" "$OUTDIR/enum.tsv")
WL_B=$(do_req "watchlists_B_own" "$BASE/watchlists/" "$TOKEN_B" "$OUTDIR/enum.tsv")
echo "$WL_A" > "$OUTDIR/watchlists_A.json"
echo "$WL_B" > "$OUTDIR/watchlists_B.json"

# ─── Step 6: Enumerate /documents/ ───
echo "[6/6] Enumerating /documents/..."
DOC_A=$(do_req "documents_A_own" "$BASE/documents/" "$TOKEN_A" "$OUTDIR/enum.tsv")
DOC_B=$(do_req "documents_B_own" "$BASE/documents/" "$TOKEN_B" "$OUTDIR/enum.tsv")
echo "$DOC_A" > "$OUTDIR/documents_A.json"
echo "$DOC_B" > "$OUTDIR/documents_B.json"

echo ""
echo "=== Enumeration complete ==="
echo "Results in: $OUTDIR/enum.tsv"
cat "$OUTDIR/enum.tsv"
echo ""
echo "=== Starting cross-replay phase ==="
