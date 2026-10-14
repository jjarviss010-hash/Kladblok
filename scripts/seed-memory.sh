#!/usr/bin/env bash
# Laadt de startbestanden uit agents/hyped-scout/data/ in het geheugen van de agent.
# Draai vanuit de repo-root, na `ant apply` (claude-lock.json moet bestaan).
# Bestaat een bestand al in het geheugen, dan wordt het overgeslagen (409).
set -euo pipefail

DATA_DIR="agents/hyped-scout/data"
STORE_ID=$(jq -r '.resources["./agents/hyped-scout/memory_store-geheugen.yaml"].id' claude-lock.json)

if [[ -z "$STORE_ID" || "$STORE_ID" == "null" ]]; then
  echo "Geen memory store gevonden in claude-lock.json. Eerst ant apply draaien." >&2
  exit 1
fi

if grep -q "YOUR_" "$DATA_DIR/instellingen.md"; then
  echo "Vul eerst de Discord-ID's in $DATA_DIR/instellingen.md in." >&2
  exit 1
fi

for file in "$DATA_DIR"/*.md; do
  name=$(basename "$file")
  if ant beta:memory-stores:memories create --memory-store-id "$STORE_ID" --path "/$name" <<YAML >/dev/null
content: "@./$file"
YAML
  then
    echo "geladen: /$name"
  else
    echo "overgeslagen (bestaat al of fout): /$name"
  fi
done

ant beta:memory-stores:memories list --memory-store-id "$STORE_ID" --transform path -r
