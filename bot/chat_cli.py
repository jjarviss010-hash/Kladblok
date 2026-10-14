"""Test de agent zonder Discord: python bot/chat_cli.py "je bericht"

Leest de ID's uit claude-lock.json en ANTHROPIC_API_KEY uit de omgeving.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
lock = json.loads((ROOT / "claude-lock.json").read_text())["resources"]
prefix = "./agents/hyped-scout/"
os.environ.setdefault("HYPED_AGENT_ID", lock[prefix + "agent.md"]["id"])
os.environ.setdefault("HYPED_ENVIRONMENT_ID", lock[prefix + "environment.yaml"]["id"])
os.environ.setdefault("HYPED_VAULT_ID", lock[prefix + "vault.yaml"]["id"])
os.environ.setdefault("HYPED_MEMORY_STORE_ID", lock[prefix + "memory_store-geheugen.yaml"]["id"])
os.environ.setdefault("SESSION_BUDGET_CENTS", "100")

from hyped_agent import HypedAgent, split_for_discord  # noqa: E402

agent = HypedAgent()
text = " ".join(sys.argv[1:]) or "Wat kun je allemaal?"
result = agent.run_turn(
    f"[Chat] (test via terminal)\n{text}",
    lambda reply: print("\n--- bericht ---\n" + "\n--- bericht ---\n".join(split_for_discord(reply))),
)
print(f"\n[klaar: {result.stop_reason}] sessie: https://platform.claude.com/workspaces/default/sessions/{agent.session_id}")
if result.notice:
    print(result.notice)
