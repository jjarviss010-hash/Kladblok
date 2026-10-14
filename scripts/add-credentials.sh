#!/usr/bin/env bash
# Alternatief voor stap 5 als je de sleutel niet via de Console wilt toevoegen:
# zet YOUTUBE_API_KEY als secret in de cloud-omgeving,
# start een nieuwe sessie, en draai dit script vanuit de repo-root.
# De waarde komt nooit in de chat of in de repo.
set -euo pipefail

VAULT_ID=$(jq -r '.resources["./agents/hyped-scout/vault.yaml"].id' claude-lock.json)
: "${YOUTUBE_API_KEY:?YOUTUBE_API_KEY ontbreekt in de omgeving}"

ant beta:vaults:credentials create --vault-id "$VAULT_ID" --transform id -r <<YAML
display_name: YouTube Data API
auth:
  type: environment_variable
  secret_name: YOUTUBE_API_KEY
  secret_value: "$YOUTUBE_API_KEY"
  injection_location: {header: true}
  networking:
    type: limited
    allowed_hosts: [www.googleapis.com, youtube.googleapis.com]
YAML

echo "Credential toegevoegd aan $VAULT_ID"
