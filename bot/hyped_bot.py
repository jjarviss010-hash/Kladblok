"""Hyped-bot voor op je eigen pc: gewoon typen in #algemeen, de agent antwoordt.

- Elk bericht van de eigenaar in het kanaal gaat direct naar de Hyped-agent (Claude
  Managed Agents). De agent post zijn antwoord zelf in Discord.
- Reacties op je bericht: ⏳ de agent is bezig, ✅ klaar, ⚠️ er ging iets mis.
- Om 08:00, 14:00 en 20:00 (Amsterdam) start de bot zelf een scoutronde.
- Commando's: `!nieuw` (verse sessie), `!stop` (huidige taak afbreken), `!id`.

Starten: zet DISCORD_BOT_TOKEN en ANTHROPIC_API_KEY in `bot/.env` en draai
`python hyped_bot.py`.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import anthropic
import discord

HERE = Path(__file__).resolve().parent


def load_env(path: Path) -> None:
    """Leest KEY=waarde-regels uit bot/.env (zonder extra pakket)."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env(HERE / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("hyped")

TZ = ZoneInfo("Europe/Amsterdam")
CHANNEL_ID = int(os.environ.get("DISCORD_CHANNEL_ID", "1560048954706759740"))
OWNER_ID = int(os.environ["DISCORD_OWNER_ID"]) if os.environ.get("DISCORD_OWNER_ID") else None
AGENT_ID = os.environ.get("HYPED_AGENT_ID", "agent_013ycwX1hsBbPTg9QPfxjmq5")
ENVIRONMENT_ID = os.environ.get("HYPED_ENVIRONMENT_ID", "env_01WGArQbuPxkEVzwFS2qHgFQ")
VAULT_ID = os.environ.get("HYPED_VAULT_ID", "vlt_011Cg2qa9eGeAWiZ3jufGVVb")
MEMORY_STORE_ID = os.environ.get("HYPED_MEMORY_STORE_ID", "memstore_01BPM1DGQcaJEGHroGgJMgTD")
BUDGET_CENTS = os.environ.get("SESSION_BUDGET_CENTS", "500")  # max $5 per dag-sessie
SCOUT_TIMES = [
    tuple(int(x) for x in t.strip().split(":"))
    for t in os.environ.get("SCOUT_TIMES", "08:00,14:00,20:00").split(",")
    if t.strip()
]
STATE_FILE = HERE / "state.json"
MAX_WAIT = 30 * 60  # seconden


class Agent:
    """Eén sessie per dag, zodat "1 en 3 ja" naar de voorstellen van vandaag verwijst."""

    def __init__(self) -> None:
        self.client = anthropic.Anthropic()  # ANTHROPIC_API_KEY
        self.state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}

    def _save(self) -> None:
        STATE_FILE.write_text(json.dumps(self.state))

    def session(self, fresh: bool = False) -> str:
        today = datetime.now(TZ).strftime("%Y-%m-%d")
        if not fresh and self.state.get("day") == today and self.state.get("session_id"):
            return self.state["session_id"]
        session = self.client.beta.sessions.create(
            agent=AGENT_ID,
            environment_id=ENVIRONMENT_ID,
            vault_ids=[VAULT_ID],
            resources=[{"type": "memory_store", "memory_store_id": MEMORY_STORE_ID, "access": "read_write"}],
            budget={"type": "limit", "max_list_cost": {"amount": BUDGET_CENTS, "currency": "USD"}},
            title=f"Hyped {today}",
        )
        log.info("nieuwe sessie %s", session.id)
        self.state = {"day": today, "session_id": session.id}
        self._save()
        return session.id

    def send(self, text: str) -> str:
        event = {"type": "user.message", "content": [{"type": "text", "text": text}]}
        session_id = self.session()
        try:
            self.client.beta.sessions.events.send(session_id, events=[event])
        except (anthropic.BadRequestError, anthropic.NotFoundError) as exc:
            log.warning("sessie niet bruikbaar (%s), nieuwe sessie", exc)
            session_id = self.session(fresh=True)
            self.client.beta.sessions.events.send(session_id, events=[event])
        return session_id

    def wait_until_done(self, session_id: str) -> str:
        """Wacht tot de agent klaar is. Geeft 'klaar', 'budget', 'gestopt' of 'timeout'."""
        started, deadline = False, time.monotonic() + MAX_WAIT
        while time.monotonic() < deadline:
            time.sleep(5)
            session = self.client.beta.sessions.retrieve(session_id)
            if session.status == "running":
                started = True
            elif session.status == "terminated":
                return "gestopt"
            elif session.status == "idle" and (started or time.monotonic() > deadline - MAX_WAIT + 60):
                cost = int(session.usage.list_cost.amount) if session.usage and session.usage.list_cost else 0
                return "budget" if cost >= int(BUDGET_CENTS) else "klaar"
        return "timeout"

    def interrupt(self) -> None:
        if self.state.get("session_id"):
            self.client.beta.sessions.events.send(self.state["session_id"], events=[{"type": "user.interrupt"}])

    def reset(self) -> None:
        self.state = {}
        self._save()


def next_scout_time(now: datetime) -> datetime:
    candidates = [
        (now + timedelta(days=day)).replace(hour=h, minute=m, second=0, microsecond=0)
        for day in (0, 1)
        for h, m in SCOUT_TIMES
    ]
    return min(c for c in candidates if c > now)


class HypedBot(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.agent = Agent()
        self.owner_id = OWNER_ID

    async def setup_hook(self) -> None:
        if self.owner_id is None:
            app = await self.application_info()
            self.owner_id = app.team.owner_id if app.team else app.owner.id
        self.loop.create_task(self.scheduler())

    async def on_ready(self) -> None:
        log.info("ingelogd als %s - kanaal %s - eigenaar %s", self.user, CHANNEL_ID, self.owner_id)

    async def forward(self, text: str, message: discord.Message | None = None) -> None:
        """Stuurt tekst naar de agent en houdt de reactie op je bericht bij."""
        if message:
            await message.add_reaction("⏳")
        try:
            session_id = await asyncio.to_thread(self.agent.send, text)
            result = await asyncio.to_thread(self.agent.wait_until_done, session_id)
        except Exception as exc:
            log.exception("doorsturen mislukt")
            result = "fout"
            channel = message.channel if message else self.get_channel(CHANNEL_ID)
            await channel.send(f"⚠️ Kon de agent niet bereiken: {exc}")
        if result == "budget":
            self.agent.reset()
            channel = message.channel if message else self.get_channel(CHANNEL_ID)
            await channel.send("💸 Dagbudget van deze sessie bereikt. Je volgende bericht start een nieuwe sessie.")
        if message:
            await message.remove_reaction("⏳", self.user)
            await message.add_reaction("✅" if result == "klaar" else "⚠️")

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or message.channel.id != CHANNEL_ID:
            return
        content = message.content.strip()
        if content == "!id":
            await message.channel.send(f"Jouw gebruikers-ID: `{message.author.id}`")
            return
        if message.author.id != self.owner_id or not content:
            return
        if content == "!nieuw":
            self.agent.reset()
            await message.channel.send("🆕 Je volgende bericht start een verse sessie (het geheugen blijft bewaard).")
            return
        if content == "!stop":
            await asyncio.to_thread(self.agent.interrupt)
            await message.channel.send("⏹️ Gestopt.")
            return
        stamp = datetime.now(TZ).strftime("%d-%m %H:%M")
        await self.forward(f"[Chat] (Discord, {stamp})\n{content}", message)

    async def scheduler(self) -> None:
        await self.wait_until_ready()
        while not self.is_closed():
            now = datetime.now(TZ)
            run_at = next_scout_time(now)
            log.info("volgende scoutronde: %s", run_at.isoformat())
            await asyncio.sleep((run_at - now).total_seconds())
            await self.forward(f"[Scoutronde] {run_at:%d-%m %H:%M}")


if __name__ == "__main__":
    HypedBot().run(os.environ["DISCORD_BOT_TOKEN"], log_handler=None)
