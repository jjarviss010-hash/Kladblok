# Hyped-agent: opzetten

## Hoe het werkt

```
 jij (Discord #algemeen)  ⇄  Hyped-bot (Railway, 24/7)  ⇄  Hyped-agent (Claude, bij Anthropic)
                                  │                              │
                                  └─ start om 08/14/20 uur       └─ YouTube Data API (alleen lezen)
                                     zelf een scoutronde            + geheugen (bronnen, voorkeuren, …)
```

- **Je typt een bericht**, de agent gaat direct aan de slag en antwoordt in hetzelfde kanaal.
- **Elke dag om 08:00, 14:00 en 20:00** doet hij zelf een scoutronde.
- **Hij clipt en post niet.** Hij levert per video de fragmenttijden, captions, hook en intro-script; jij clipt in OpusClip.
- **Commando's in Discord:** `!nieuw` start een verse sessie (het geheugen blijft bewaard), `!stop` breekt de huidige taak af.

## Status

| Onderdeel | Status |
|---|---|
| Agent (`hyped-agent`, `agent_013ycwX1hsBbPTg9QPfxjmq5`) | ✅ aangemaakt en getest |
| Sandbox (alleen YouTube bereikbaar, `env_01WGArQbuPxkEVzwFS2qHgFQ`) | ✅ |
| Kluis (`vlt_011Cg2qa9eGeAWiZ3jufGVVb`) | ✅ aangemaakt, **YouTube-sleutel ontbreekt nog** |
| Geheugen (`memstore_01BPM1DGQcaJEGHroGgJMgTD`) | ✅ gevuld: instellingen, bronnen, voorkeuren, al geclipt, voorstellen, logboek |
| Bot-code (`bot/`) | ✅ klaar en getest zonder Discord |
| Bot online (Railway) | ⏳ stap C |

Een testgesprek kostte $0,11.

---

## Stap A (jij): YouTube-sleutel in de kluis

1. Ga naar console.cloud.google.com → nieuw project → *APIs & Services → Library* → **YouTube Data API v3** → *Enable*.
2. Ga naar *Credentials → Create credentials → API key*. Kies daarna *Edit*, en zet onder *API restrictions* alleen de YouTube Data API v3 aan.
3. Ga naar platform.claude.com → **Managed Agents → Vaults → `hyped-scout`** → *Add credential* → type **Environment variable**:
   - Naam: `YOUTUBE_API_KEY`
   - Waarde: je sleutel
   - Toegestane hosts: `www.googleapis.com` en `youtube.googleapis.com`
   - Injectie: **header**

## Stap B (jij): Discord-bot

1. Ga naar discord.com/developers/applications → *New Application* (naam: Hyped) → tab **Bot**:
   - **Reset Token**: kopieer het token en bewaar het. Dit is geheim.
   - **Message Content Intent**: aanzetten.
2. Ga naar *OAuth2 → URL Generator*:
   - Scope: `bot`.
   - Rechten: *View Channels*, *Send Messages*, *Read Message History*, *Add Reactions*.
   - Open de link en kies je server.
3. ID's kopiëren:
   - Zet in Discord de ontwikkelaarsmodus aan: *Instellingen → Geavanceerd*.
   - Kopieer het **kanaal-ID** van `#algemeen`.
   - Kopieer je eigen **gebruikers-ID**.

## Stap C (jij): bot online zetten op Railway (±$5/maand)

1. Ga naar railway.com, log in met GitHub en neem het **Hobby**-abonnement.
2. *New Project → Deploy from GitHub repo* → kies `jjarviss010-hash/Kladblok`, branch `claude/eloquent-clarke-hwv4xa`.
3. Ga bij de service naar **Settings**:
   - **Root Directory**: `bot`
   - **Start Command**: `python main.py`. Dit staat ook in `bot/railway.json`; vul het in als Railway het niet oppikt.
4. Ga naar **Variables** en voeg toe:

| Naam | Waarde |
|---|---|
| `DISCORD_BOT_TOKEN` | token uit stap B (geheim) |
| `ANTHROPIC_API_KEY` | een **nieuwe** sleutel uit platform.claude.com → API keys (geheim; niet de sleutel die in de chat stond) |
| `DISCORD_CHANNEL_ID` | kanaal-ID van `#algemeen` |
| `DISCORD_OWNER_ID` | jouw gebruikers-ID |
| `HYPED_AGENT_ID` | `agent_013ycwX1hsBbPTg9QPfxjmq5` |
| `HYPED_ENVIRONMENT_ID` | `env_01WGArQbuPxkEVzwFS2qHgFQ` |
| `HYPED_VAULT_ID` | `vlt_011Cg2qa9eGeAWiZ3jufGVVb` |
| `HYPED_MEMORY_STORE_ID` | `memstore_01BPM1DGQcaJEGHroGgJMgTD` |
| `SESSION_BUDGET_CENTS` | `500` (max $5 per dag; optioneel) |
| `SCOUT_TIMES` | `08:00,14:00,20:00` (optioneel) |

5. Kies *Deploy*. In de logs moet `ingelogd als Hyped#…` verschijnen.
6. Werkt alles? Verwijder dan in de Claude Console de oude API-sleutel die in de chat is geplakt.

## Stap D: testen

Typ in `#algemeen`: `doe nu een scoutronde`. Binnen een paar seconden zie je "Hyped is aan het typen…", en na een paar minuten de voorstellen.

---

## Wijzigen

- **Instructies van de agent:** pas `agents/hyped-scout/agent.md` aan. Daarna:
  ```sh
  bash scripts/install-ant.sh
  ant apply agents/hyped-scout/agent.md
  ```
  Toon eerst het plan met `--dry-run`. Lopende sessies houden de oude versie; `!nieuw` in Discord pakt de nieuwe.
- **Agent testen zonder Discord:** `python bot/chat_cli.py "je vraag"`.
- **Geheugen bekijken:** Claude Console → Managed Agents → Memory stores → `hyped-geheugen`.

## Later (bewust nog uit)

- Clippen en posten via OpusClip: de officiële API en CLI staan in `github.com/opus-pro/opus-skills`.
- Een transcriptdienst, voor preciezere momenten.
- Instagram-comments en -statistieken (vereist een Meta-app).
