"""Hyped-bot: 24/7 Discord-koppeling voor de Hyped-agent.

- Elk bericht van de eigenaar in het kanaal gaat direct naar de agent; het antwoord
  komt terug in hetzelfde kanaal.
- Drie keer per dag start de bot zelf een scoutronde (SCOUT_TIMES, Amsterdamse tijd).
- Commando's: `!nieuw` (verse sessie), `!stop` (huidige taak afbreken), `!id` (toont je gebruikers-ID).
- Alleen de eigenaar wordt doorgestuurd: DISCORD_OWNER_ID, of anders de eigenaar van de Discord-app.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta

import discord

from hyped_agent import TZ, HypedAgent, split_for_discord

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("hyped.bot")

CHANNEL_ID = int(os.environ["DISCORD_CHANNEL_ID"])
# Optioneel: zonder deze variabele is de eigenaar van de Discord-app de eigenaar van de bot.
OWNER_ID = int(os.environ["DISCORD_OWNER_ID"]) if os.environ.get("DISCORD_OWNER_ID") else None
SCOUT_TIMES = [
    tuple(int(x) for x in t.strip().split(":"))
    for t in os.environ.get("SCOUT_TIMES", "08:00,14:00,20:00").split(",")
    if t.strip()
]


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
        self.agent = HypedAgent()
        self.lock = asyncio.Lock()  # één taak tegelijk; volgende berichten wachten netjes
        self.owner_id = OWNER_ID

    async def setup_hook(self) -> None:
        if self.owner_id is None:
            app = await self.application_info()
            self.owner_id = app.team.owner_id if app.team else app.owner.id
        self.loop.create_task(self.scheduler())

    async def on_ready(self) -> None:
        log.info("ingelogd als %s, kanaal %s, eigenaar %s", self.user, CHANNEL_ID, self.owner_id)

    async def channel(self) -> discord.abc.Messageable:
        return self.get_channel(CHANNEL_ID) or await self.fetch_channel(CHANNEL_ID)

    async def relay(self, channel: discord.abc.Messageable, text: str) -> None:
        """Stuurt tekst naar de agent en zet elk antwoord direct in Discord."""
        async with self.lock:
            loop = asyncio.get_running_loop()
            queue: asyncio.Queue[str | None] = asyncio.Queue()

            async def post_replies() -> None:
                while (reply := await queue.get()) is not None:
                    for chunk in split_for_discord(reply):
                        await channel.send(chunk)

            poster = asyncio.create_task(post_replies())
            try:
                async with channel.typing():
                    result = await asyncio.to_thread(
                        self.agent.run_turn, text, lambda r: loop.call_soon_threadsafe(queue.put_nowait, r)
                    )
            except Exception:
                log.exception("fout tijdens beurt")
                result = None
                await channel.send("⚠️ Er ging iets mis bij de agent. Kijk in de logs of probeer het opnieuw.")
            finally:
                queue.put_nowait(None)
                await poster
            if result and result.notice:
                await channel.send(result.notice)

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or message.channel.id != CHANNEL_ID:
            return
        content = message.content.strip()
        if content == "!id":
            await message.channel.send(f"Jouw gebruikers-ID: `{message.author.id}`")
            return
        if message.author.id != self.owner_id:
            return
        if content == "!nieuw":
            self.agent.reset()
            await message.channel.send("🆕 Volgende bericht start een verse sessie (geheugen blijft bewaard).")
            return
        if content == "!stop":
            stopped = await asyncio.to_thread(self.agent.interrupt)
            await message.channel.send("⏹️ Gestopt." if stopped else "Er loopt niets.")
            return
        if not content:
            return
        if self.lock.locked():
            await message.add_reaction("⏳")  # komt aan de beurt zodra de huidige taak klaar is
        stamp = datetime.now(TZ).strftime("%d-%m %H:%M")
        await self.relay(message.channel, f"[Chat] (Discord-bericht {message.id}, {stamp})\n{content}")

    async def scheduler(self) -> None:
        await self.wait_until_ready()
        while not self.is_closed():
            now = datetime.now(TZ)
            run_at = next_scout_time(now)
            log.info("volgende scoutronde: %s", run_at.isoformat())
            await asyncio.sleep((run_at - now).total_seconds())
            try:
                await self.relay(await self.channel(), f"[Scoutronde] {run_at:%d-%m %H:%M}")
            except Exception:
                log.exception("scoutronde mislukt")


if __name__ == "__main__":
    HypedBot().run(os.environ["DISCORD_BOT_TOKEN"], log_handler=None)
