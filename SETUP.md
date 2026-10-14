# Hyped-agent: opzetten

## Hoe het werkt (gratis, 24/7)

```
 jij typt in Discord #algemeen
        │
        ▼
 Hyped-bot op je pc (bot/hyped_bot.py)  ──►  Hyped-agent (Claude, bij Anthropic)
 - stuurt je bericht door                      │  YouTube Data API (lezen)
 - start om 08/14/20 een scoutronde            │  geheugen (bronnen, voorkeuren, …)
                                               └──► post zijn antwoord zelf in #algemeen
```

- **Gewoon typen** in `#algemeen`: de agent gaat direct aan de slag en antwoordt in het kanaal.
- **Reacties op je bericht:** ⏳ bezig, ✅ klaar, ⚠️ er ging iets mis.
- **Elke dag om 08:00, 14:00 en 20:00** doet hij zelf een scoutronde.
- **`!nieuw`** start een verse sessie (het geheugen blijft bewaard). **`!stop`** breekt de huidige taak af. **`!id`** toont je gebruikers-ID.
- **Hij clipt en post niet.** Hij levert per video de fragmenttijden, captions, hook en intro-script; jij clipt in OpusClip.
- **De bot draait op je pc, net als Jarvis.** Hij maakt alleen uitgaand verbinding (Discord en Anthropic), dus Tailscale en open poorten zijn niet nodig. Staat de pc uit, dan is de bot offline.

## Onderdelen

| Onderdeel | Waar | ID / naam |
|---|---|---|
| Agent | Claude Console | `hyped-agent`, `agent_013ycwX1hsBbPTg9QPfxjmq5` |
| Sandbox (alleen YouTube + Discord) | Claude Console | `env_01WGArQbuPxkEVzwFS2qHgFQ` |
| Kluis | Claude Console | `hyped-scout`: `YOUTUBE_API_KEY` ✅, `DISCORD_BOT_TOKEN` ⏳ |
| Geheugen | Claude Console | `hyped-geheugen`, `memstore_01BPM1DGQcaJEGHroGgJMgTD` |
| Bot | jouw pc | `bot/hyped_bot.py` |
| Discord-kanaal | Discord | `#algemeen`, `1560048954706759740` |

## Installeren op je pc

1. **Python 3.10 of nieuwer.** Heb je dat al voor Jarvis, dan ben je klaar. Controleer met `python --version`.
2. **Code ophalen:** `git clone https://github.com/jjarviss010-hash/Kladblok` en daarna `git checkout claude/eloquent-clarke-hwv4xa`. Of download de map `bot/` als zip via GitHub.
3. **Pakketten:** ga in de map `bot` en draai `pip install -r requirements.txt`.
4. **Sleutels:** kopieer `.env.example` naar `.env` en vul in:
   - `DISCORD_BOT_TOKEN`: je bot-token
   - `ANTHROPIC_API_KEY`: een **nieuwe** sleutel uit platform.claude.com → API keys
5. **Testen:** draai `python hyped_bot.py`. Je ziet `ingelogd als Hyped#…` en de bot staat online in Discord. Typ in `#algemeen`: `hoi, wat kun je?`
6. **Automatisch starten bij opstarten:**
   - **Windows:** druk Win+R, typ `shell:startup` en zet daar een snelkoppeling naar `bot\start-windows.bat`.
   - **macOS / Linux:** voeg `bot/start.sh` toe aan je opstartitems, of gebruik dezelfde aanpak als bij Jarvis.

## Eenmalig in de Claude Console

- Ga naar Vaults → `hyped-scout` → *Add credential* → *Environment variable*:
  - naam: `DISCORD_BOT_TOKEN`
  - waarde: je bot-token
  - host: `discord.com`
  - injectie: header

  Zonder deze credential kan de agent niet posten.
- Werkt alles? Verwijder dan de oude API-sleutel die in de chat is geplakt.

## Wijzigen

- **Instructies van de agent:** pas `agents/hyped-scout/agent.md` aan. Daarna `ant apply agents/hyped-scout/agent.md`, met eerst `--dry-run`. Installeer `ant` met `bash scripts/install-ant.sh`. Een lopende dag-sessie houdt de oude versie; `!nieuw` pakt de nieuwe.
- **Tijden en budget:** `SCOUT_TIMES` en `SESSION_BUDGET_CENTS` in `bot/.env`.
- **Testen zonder Discord-bot:** `python scripts/chat_cli.py "je vraag"`. De agent post het antwoord ook in Discord.

## Kosten

- Hosting: €0 (je eigen pc).
- Agent: ±$0,55 per scoutronde, enkele centen per vraag. Maximum $5 per dag-sessie.

## Niet meer in gebruik

- `supabase/`: de `/hyped`-variant. De functie staat nog in Supabase, maar de uurlijkse tik is uitgezet en Discord stuurt er niets naartoe.

## Later (bewust nog uit)

- Clippen en posten via OpusClip: de officiële API en CLI staan in `github.com/opus-pro/opus-skills`.
- Een transcriptdienst, voor preciezere momenten.
- Instagram-comments en -statistieken (vereist een Meta-app).
