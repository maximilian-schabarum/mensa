#!/usr/bin/env bash

set -euo pipefail

readonly FETCH_URL="https://openmensa.org/feeds/3222/fetch"
readonly PENDING_MARKER="docs/.openmensa-fetch-pending"
readonly TABERNA_FEEDS=(
    "docs/feed/speierlingshof_speierlingshof.xml"
    "docs/today/speierlingshof_speierlingshof.xml"
)

mark_pending_if_feed_changed() {
    if ! git diff --quiet -- "${TABERNA_FEEDS[@]}"; then
        touch "$PENDING_MARKER"
        echo "Taberna feed changed; OpenMensa fetch is pending."
    fi
}

request_pending_fetch() {
    if [[ ! -f "$PENDING_MARKER" ]]; then
        echo "No OpenMensa fetch is pending."
        return
    fi

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
        echo "OpenMensa rate limit reached; retrying at the next scheduled run."
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

    rm "$PENDING_MARKER"
    echo "OpenMensa successfully fetched the Taberna feed."
}

case "${1:-}" in
    mark-pending)
        mark_pending_if_feed_changed
        ;;
    fetch-pending)
        request_pending_fetch
        ;;
    *)
        echo "Usage: $0 {mark-pending|fetch-pending}" >&2
        exit 2
        ;;
esac
