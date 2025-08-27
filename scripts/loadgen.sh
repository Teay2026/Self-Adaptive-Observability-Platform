#!/usr/bin/env bash
set -euo pipefail
URL=${1:-http://localhost:8080/}
DURATION=${2:-60}
CONCURRENCY=${3:-4}

end=$((SECONDS+DURATION))
pids=()
worker(){
  while [ $SECONDS -lt $end ]; do
    curl -s "$URL" >/dev/null || true
    sleep 0.1
  done
}
for i in $(seq 1 $CONCURRENCY); do
  worker &
  pids+=("$!")
done
trap 'kill ${pids[*]} 2>/dev/null || true' EXIT
wait

