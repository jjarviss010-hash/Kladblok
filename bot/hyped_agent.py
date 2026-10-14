"""Verbinding tussen de bot en de Hyped-agent (Claude Managed Agents).

Eén sessie per dag: berichten van dezelfde dag delen context (zodat "1 en 3 ja"
naar de voorstellen van die dag verwijst). Langetermijngeheugen zit in de
memory store, niet in de sessie.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable
from zoneinfo import ZoneInfo

import anthropic

log = logging.getLogger("hyped.agent")

TZ = ZoneInfo("Europe/Amsterdam")
DISCORD_LIMIT = 1900
SPLIT_MARKER = "==="


@dataclass
class TurnResult:
    stop_reason: str
    notice: str | None = None


class HypedAgent:
    def __init__(self) -> None:
        self.client = anthropic.Anthropic()  # leest ANTHROPIC_API_KEY
        self.agent_id = os.environ["HYPED_AGENT_ID"]
        self.environment_id = os.environ["HYPED_ENVIRONMENT_ID"]
        self.vault_id = os.environ["HYPED_VAULT_ID"]
        self.memory_store_id = os.environ["HYPED_MEMORY_STORE_ID"]
        self.budget_cents = os.environ.get("SESSION_BUDGET_CENTS", "500")
        self.session_id: str | None = None
        self.session_day: str | None = None

    # -- sessies ---------------------------------------------------------

    def _session(self) -> str:
        today = datetime.now(TZ).strftime("%Y-%m-%d")
        if self.session_id and self.session_day == today:
            return self.session_id
        session = self.client.beta.sessions.create(
            agent=self.agent_id,
            environment_id=self.environment_id,
            vault_ids=[self.vault_id],
            resources=[
                {
                    "type": "memory_store",
                    "memory_store_id": self.memory_store_id,
                    "access": "read_write",
                }
            ],
            budget={
                "type": "limit",
                "max_list_cost": {"amount": self.budget_cents, "currency": "USD"},
            },
            title=f"Hyped {today}",
        )
        log.info("nieuwe sessie %s", session.id)
        self.session_id, self.session_day = session.id, today
        return session.id

    def reset(self) -> None:
        self.session_id = None

    def interrupt(self) -> bool:
        if not self.session_id:
            return False
        self.client.beta.sessions.events.send(
            session_id=self.session_id, events=[{"type": "user.interrupt"}]
        )
        return True

    # -- één beurt -------------------------------------------------------

    def run_turn(self, text: str, on_text: Callable[[str], None]) -> TurnResult:
        """Stuurt één bericht naar de agent en geeft elk antwoord door aan on_text.

        Blokkeert tot de agent klaar is. Draait in een thread (niet in de
        Discord-eventloop).
        """
        session_id = self._session()
        turn_start = datetime.now(timezone.utc) - timedelta(seconds=1)
        seen: set[str] = set()
        sent = False

        for attempt in range(5):
            try:
                with self.client.beta.sessions.events.stream(session_id=session_id) as stream:
                    if not sent:
                        self.client.beta.sessions.events.send(
                            session_id=session_id,
                            events=[{"type": "user.message", "content": [{"type": "text", "text": text}]}],
                        )
                        sent = True
                    else:
                        # Na een verbroken verbinding: gemiste events van deze beurt ophalen.
                        for event in self.client.beta.sessions.events.list(
                            session_id=session_id, created_at_gte=turn_start
                        ):
                            stop = self._process(event, seen, on_text, session_id)
                            if stop:
                                return self._finish(stop)
                    for event in stream:
                        stop = self._process(event, seen, on_text, session_id)
                        if stop:
                            return self._finish(stop)
            except (anthropic.APIConnectionError, anthropic.InternalServerError) as exc:
                log.warning("verbinding verbroken (poging %d): %s", attempt + 1, exc)
                time.sleep(2**attempt)
        return TurnResult("connection_lost", "⚠️ Verbinding met de agent verloren. Probeer het zo opnieuw.")

    def _process(self, event, seen: set[str], on_text, session_id: str) -> str | None:
        if event.id not in seen:
            seen.add(event.id)
            if event.type == "agent.message":
                reply = "".join(block.text for block in event.content if block.type == "text")
                if reply.strip():
                    on_text(reply)
            elif event.type in ("agent.tool_use", "agent.mcp_tool_use") and getattr(
                event, "evaluated_permission", None
            ) == "ask":
                # Komt niet voor met always_allow; voor de zekerheid weigeren i.p.v. eeuwig wachten.
                self.client.beta.sessions.events.send(
                    session_id=session_id,
                    events=[{
                        "type": "user.tool_confirmation",
                        "tool_use_id": event.id,
                        "result": "deny",
                        "deny_message": "Geen goedkeuring beschikbaar in de bot.",
                    }],
                )
            elif event.type == "session.error":
                log.error("sessiefout: %s", getattr(event, "error", event))
        if event.type == "session.status_terminated":
            return "terminated"
        if event.type == "session.status_idle" and event.stop_reason.type != "requires_action":
            return event.stop_reason.type
        return None

    def _finish(self, stop_reason: str) -> TurnResult:
        if stop_reason == "end_turn":
            return TurnResult(stop_reason)
        self.reset()  # volgende bericht start een verse sessie
        if stop_reason == "budget_reached":
            return TurnResult(
                stop_reason,
                "💸 Dagbudget van deze sessie bereikt. Je volgende bericht start een nieuwe sessie.",
            )
        return TurnResult(stop_reason, f"⚠️ De agent stopte onverwacht ({stop_reason}). Probeer het opnieuw.")


def split_for_discord(text: str) -> list[str]:
    """Splitst op `===`-regels en daarna op de Discord-limiet (op regelgrenzen)."""
    parts = [p.strip() for p in text.split(f"\n{SPLIT_MARKER}\n")]
    chunks: list[str] = []
    for part in parts:
        part = part.strip(f"{SPLIT_MARKER}\n ").strip()
        while len(part) > DISCORD_LIMIT:
            cut = part.rfind("\n", 0, DISCORD_LIMIT)
            cut = cut if cut > 0 else DISCORD_LIMIT
            chunks.append(part[:cut].rstrip())
            part = part[cut:].lstrip()
        if part:
            chunks.append(part)
    return chunks
