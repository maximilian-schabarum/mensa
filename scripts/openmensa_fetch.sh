#!/usr/bin/env bash

set -euo pipefail

readonly OPENMENSA_FEED_ID="${OPENMENSA_FEED_ID:-3222}"
readonly FETCH_URL="${OPENMENSA_FETCH_URL:-https://openmensa.org/feeds/${OPENMENSA_FEED_ID}/fetch}"

request_fetch() {
    local response_file
    local status
    response_file="$(mktemp)"
    trap 'rm -f "$response_file"' RETURN

    if ! status="$(
        curl --silent --show-error --location \
            --header "Accept: application/json" \
            --max-time 60 \
            --output "$response_file" \
            --write-out "%{http_code}" \
            "$FETCH_URL"
    )"; then
        echo "OpenMensa fetch request failed before receiving a response." >&2
        return 1
    fi

    if [[ "$status" == "429" ]]; then
        echo "OpenMensa rate limit reached; the next scheduled run will retry."
        return
    fi

    if [[ ! "$status" =~ ^2 ]]; then
        echo "OpenMensa fetch request returned HTTP $status." >&2
        cat "$response_file" >&2
        return 1
    fi

    if ! python - "$response_file" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as response:
    payload = json.load(response)

if payload.get("status") != "ok":
    raise SystemExit(f"OpenMensa reported a failed fetch: {payload}")
PY
    then
        return 1
    fi

    echo "OpenMensa successfully fetched the Taberna feed."
}

case "${1:-}" in
    fetch)
        request_fetch
        ;;
    *)
        echo "Usage: $0 fetch" >&2
        exit 2
        ;;
esac
