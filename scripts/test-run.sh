#!/usr/bin/env bash
# Start één handmatige scoutronde (werkt ook als het schema op pauze staat)
# en toont daarna de link naar de sessie en de laatste berichten van de agent.
set -euo pipefail

DEPLOYMENT_ID=$(jq -r '.resources["./agents/hyped-scout/deployment-scout.yaml"].id' claude-lock.json)
RUN_JSON=$(ant beta:deployments run --deployment-id "$DEPLOYMENT_ID" --format json)
SESSION_ID=$(echo "$RUN_JSON" | jq -r '.session_id // empty')

if [[ -z "$SESSION_ID" ]]; then
  echo "Run mislukt:" >&2
  echo "$RUN_JSON" | jq '.error' >&2
  exit 1
fi

echo "Sessie: https://platform.claude.com/workspaces/default/sessions/$SESSION_ID"
echo "Wachten tot de ronde klaar is (max. 20 min)..."

deadline=$(( $(date +%s) + 1200 ))
while (( $(date +%s) < deadline )); do
  status=$(ant beta:sessions retrieve --session-id "$SESSION_ID" --transform status -r)
  [[ "$status" == "idle" || "$status" == "terminated" ]] && break
  sleep 20
done
echo "Status: $status"

ant beta:sessions:events list --session-id "$SESSION_ID" --order desc --limit 50 \
  --transform '{type,text:content.#(type=="text").text}' --format jsonl \
  | jq -r 'select(.type=="agent.message") | .text' | head -40
