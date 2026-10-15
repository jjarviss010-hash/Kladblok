# Hyped-agent: opzetten

## Hoe het werkt (gratis, 24/7)

```
 jij in Discord: /hyped <bericht>
        │
        ▼
 Supabase-functie "hyped-discord"  ──►  Hyped-agent (Claude, bij Anthropic)
 (gratis, altijd aan)                     │  YouTube Data API (lezen)
        ▲                                 │  geheugen (bronnen, voorkeuren, …)
 pg_cron: elk uur een tik;                └──► post zijn antwoord zelf in #algemeen
 om 08/14/20 uur start hij een scoutronde
```

- **`/hyped <bericht>`** in `#algemeen`: de agent gaat direct aan de slag en zet zijn antwoord in het kanaal.
- **Elke dag om 08:00, 14:00 en 20:00** doet hij zelf een scoutronde.
- **`/hyped nieuw`** start een verse sessie (het geheugen blijft bewaard). **`/hyped stop`** breekt de huidige taak af.
- **Hij clipt en post niet.** Hij levert per video de fragmenttijden, captions, hook en intro-script; jij clipt in OpusClip.
- **De bot staat in Discord altijd als "offline".** Dat klopt: hij reageert via `/hyped` en hoeft niet online te zijn.

## Onderdelen

| Onderdeel | Waar | ID / naam |
|---|---|---|
| Agent | Claude Console | `hyped-agent`, `agent_013ycwX1hsBbPTg9QPfxjmq5` |
| Sandbox (alleen YouTube + Discord) | Claude Console | `env_01WGArQbuPxkEVzwFS2qHgFQ` |
| Kluis | Claude Console | `hyped-scout`, `vlt_011Cg2qa9eGeAWiZ3jufGVVb`: `YOUTUBE_API_KEY` ✅, `DISCORD_BOT_TOKEN` ✅ |
| Geheugen | Claude Console | `hyped-geheugen`, `memstore_01BPM1DGQcaJEGHroGgJMgTD` |
| Deurbel | Supabase | functie `hyped-discord` (`supabase/functions/`) |
| Schema + opslag | Supabase | tabel `hyped_state`, cron-job `hyped-tick` (`supabase/migrations/`) |
| Discord | Discord | app `1560067975631994931`, kanaal `#algemeen` `1560048955515998221`, server `1560048954706759740` |

## Eenmalige stappen voor jou

1. **Supabase-dashboard** → project → *Edge Functions* → **Secrets** → *Add new secret*:
   - `DISCORD_BOT_TOKEN`: je bot-token
   - `ANTHROPIC_API_KEY`: een **nieuwe** sleutel uit platform.claude.com → API keys, naam `hyped-supabase`
2. **Discord Developer Portal** → je app → *General Information* → **Interactions Endpoint URL**:
   `https://fxfkjnbhrcdvhofukcpc.supabase.co/functions/v1/hyped-discord` → *Save Changes*.
   Discord test de link meteen; bij een fout krijg je direct een melding.
3. Laat het Claude weten. Claude registreert dan het `/hyped`-commando en doet een test.
4. Werkt alles? Verwijder dan in de Claude Console de oude API-sleutel die in de chat is geplakt.

Applicatie-ID, Public Key, kanaal en jouw Discord-ID staan al in de functie (`CONFIG`) en in de tabel `hyped_state`.

## Wijzigen

- **Instructies van de agent:** pas `agents/hyped-scout/agent.md` aan. Daarna `ant apply agents/hyped-scout/agent.md`, met eerst `--dry-run`. Installeer `ant` met `bash scripts/install-ant.sh`. Een lopende dag-sessie houdt de oude versie; `/hyped nieuw` pakt de nieuwe.
- **Tijden en budget:** `CONFIG` bovenin `supabase/functions/hyped-discord/index.ts`, en daarna opnieuw deployen.
- **Testen zonder Discord:** `python scripts/chat_cli.py "je vraag"`. Dit post ook in Discord.
- **Geheugen bekijken:** Claude Console → Memory stores → `hyped-geheugen`.

## Kosten

- Hosting: €0 (Supabase gratis).
- Agent: ±$0,55 per scoutronde, enkele centen per vraag. Maximum $5 per dag-sessie.

## Later (bewust nog uit)

- Clippen en posten via OpusClip: de officiële API en CLI staan in `github.com/opus-pro/opus-skills`.
- Een transcriptdienst, voor preciezere momenten.
- Instagram-comments en -statistieken (vereist een Meta-app).
