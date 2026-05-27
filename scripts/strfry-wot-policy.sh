#!/usr/bin/env bash
set -euo pipefail

TRUST_API_URL="http://localhost:3001"
CACHE_FILE="/opt/tollgate/relatr/wot-cache.json"
MIN_TRUST="${WOT_MIN_TRUST:-0.1}"
CACHE_TTL="${WOT_CACHE_TTL:-3600}"

trust_cache_get() {
    local pubkey="$1"
    if [[ ! -f "$CACHE_FILE" ]]; then
        echo "{}" > "$CACHE_FILE"
        return 1
    fi
    local now
    now=$(date +%s)
    local cached
    cached=$(jq -r --arg pk "$pubkey" '.[$pk] // empty' "$CACHE_FILE" 2>/dev/null || true)
    if [[ -n "$cached" ]]; then
        local ts
        ts=$(echo "$cached" | jq -r '.ts // 0')
        local age=$(( now - ts ))
        if [[ $age -lt $CACHE_TTL ]]; then
            echo "$cached" | jq -r '.score // 0'
            return 0
        fi
    fi
    return 1
}

trust_cache_set() {
    local pubkey="$1"
    local score="$2"
    local now
    now=$(date +%s)
    mkdir -p "$(dirname "$CACHE_FILE")"
    [[ -f "$CACHE_FILE" ]] || echo '{}' > "$CACHE_FILE"
    local tmp="${CACHE_FILE}.tmp"
    jq --arg pk "$pubkey" --argjson s "$score" --argjson t "$now" \
        'setpath([$pk]; {score: $s, ts: $t})' "$CACHE_FILE" > "$tmp" 2>/dev/null && \
        mv "$tmp" "$CACHE_FILE" || rm -f "$tmp"
}

query_trust_api() {
    local pubkey="$1"
    local score
    score=$(curl -s --max-time 3 "${TRUST_API_URL}/trust?pubkey=${pubkey}" 2>/dev/null \
        | jq -r '.score // 0' 2>/dev/null || echo "0")
    echo "${score:-0}"
}

get_trust_score() {
    local pubkey="$1"
    local cached
    if cached=$(trust_cache_get "$pubkey"); then
        echo "$cached"
        return
    fi
    local score
    score=$(query_trust_api "$pubkey")
    trust_cache_set "$pubkey" "$score"
    echo "$score"
}

main() {
    local input
    input=$(cat)
    local event_type
    event_type=$(echo "$input" | jq -r '.type // empty')

    if [[ "$event_type" == "lookback" ]]; then
        echo '{"action": "accept"}'
        return
    fi

    local pubkey
    pubkey=$(echo "$input" | jq -r '.event.pubkey // empty')

    if [[ -z "$pubkey" ]]; then
        echo '{"action": "reject", "msg": "missing pubkey"}'
        return
    fi

    local score
    score=$(get_trust_score "$pubkey")

    if awk "BEGIN{exit !($score >= $MIN_TRUST)}"; then
        echo '{"action": "accept"}'
    else
        echo "{\"action\": \"reject\", \"msg\": \"trust score ${score} below minimum ${MIN_TRUST}\"}"
    fi
}

main
