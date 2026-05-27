#!/usr/bin/env bash
set -euo pipefail

RELATR_URL="http://localhost:3000"
MIN_TRUST="${WOT_MIN_TRUST:-0.1}"

query_trust() {
    local npub="$1"
    local score
    score=$(curl -s --max-time 5 "${RELATR_URL}/api/trust?pubkey=${npub}" 2>/dev/null | jq -r '.score // 0' 2>/dev/null || echo "0")
    if [[ -z "$score" || "$score" == "null" ]]; then
        score="0"
    fi
    echo "$score"
}

filter_servers() {
    while IFS= read -r line; do
        local npub
        npub=$(echo "$line" | grep -oP 'npub[a-zA-Z0-9]+' | head -1 || true)
        if [[ -z "$npub" ]]; then
            echo "$line"
            continue
        fi
        local score
        score=$(query_trust "$npub")
        if (( $(echo "$score >= $MIN_TRUST" | bc -l 2>/dev/null || echo "0") )); then
            echo "$line"
        else
            echo "# FILTERED: trust=${score} ${line}" >&2
        fi
    done
}

if [[ "${1:-}" == "--test" ]]; then
    echo "Testing Relatr connection..."
    curl -s --max-time 5 "${RELATR_URL}/" > /dev/null && echo "OK: Relatr reachable" || echo "FAIL: Relatr unreachable"
    exit 0
fi

filter_servers
