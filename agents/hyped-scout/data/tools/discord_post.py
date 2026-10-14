"""Post een antwoord van de Hyped-agent in Discord.

Gebruik:  python3 /mnt/memory/hyped-geheugen/tools/discord_post.py < antwoord.txt
          (of de tekst als argument)

- Splitst op regels met alleen `===` (één Discord-bericht per deel) en op 1900 tekens.
- DISCORD_BOT_TOKEN komt uit de kluis; de sandbox ziet alleen een placeholder.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

CHANNEL_ID = "1560048954706759740"
LIMIT = 1900


def split(text: str) -> list[str]:
    chunks = []
    for part in text.split("\n===\n"):
        part = part.strip().strip("=").strip()
        while len(part) > LIMIT:
            cut = part.rfind("\n", 0, LIMIT)
            cut = cut if cut > 0 else LIMIT
            chunks.append(part[:cut].rstrip())
            part = part[cut:].lstrip()
        if part:
            chunks.append(part)
    return chunks


def post(content: str) -> None:
    request = urllib.request.Request(
        f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages",
        data=json.dumps({"content": content, "allowed_mentions": {"parse": []}}).encode(),
        headers={
            "Authorization": f"Bot {os.environ['DISCORD_BOT_TOKEN']}",
            "Content-Type": "application/json",
            "User-Agent": "DiscordBot (https://github.com/jjarviss010-hash/Kladblok, 1.0)",
        },
        method="POST",
    )
    for _ in range(5):
        try:
            urllib.request.urlopen(request, timeout=30).read()
            return
        except urllib.error.HTTPError as err:
            if err.code == 429:
                time.sleep(float(json.loads(err.read() or b"{}").get("retry_after", 2)) + 0.5)
                continue
            raise SystemExit(f"Discord-fout {err.code}: {err.read().decode(errors='replace')[:300]}")
    raise SystemExit("Discord bleef 429 (rate limit) geven.")


if __name__ == "__main__":
    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else sys.stdin.read()
    parts = split(text)
    for i, chunk in enumerate(parts):
        post(chunk)
        if i < len(parts) - 1:
            time.sleep(0.5)
    print(f"{len(parts)} bericht(en) gepost")
