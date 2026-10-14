# Hyped Scout: stap voor stap opzetten

**Wat het is:** een Claude Managed Agent. Anthropic draait de agent en het schema; je hebt geen eigen server nodig.

**Wat hij doet (versie 1):**
- 3× per dag nieuwe bronvideo's zoeken.
- Per video de beste fragmenten bepalen.
- Voorstellen in Discord zetten, met een schatting van de credits.

**Wat hij nog niet doet:** clippen en posten. Daarmee verbruikt hij **geen OpusClip-credits**.

Bestanden: `agents/hyped-scout/`. Het plan erachter staat in `PLAN.md`.

---

## Stap 1 (jij): Claude Console

1. Ga naar platform.claude.com en maak een account (of log in).
2. Billing: zet er tegoed op. $20 is genoeg voor de eerste weken testen.
3. API keys: maak een sleutel aan met de naam `hyped`.
4. Zet die sleutel in deze cloud-omgeving.
   - **Waar:** omgevingsmenu in de titelbalk van de sessie → Edit → *Network secrets* (of *Environment variables*).
   - **Naam:** `ANTHROPIC_API_KEY`
   - **Let op:** plak de sleutel nooit in de chat.

## Stap 2 (jij): YouTube Data API-sleutel

1. Ga naar console.cloud.google.com en maak een nieuw project (`hyped`).
2. *APIs & Services → Library → YouTube Data API v3 → Enable*.
3. *Credentials → Create credentials → API key*.
4. *Edit API key → API restrictions → alleen YouTube Data API v3*.
5. Bewaar de sleutel. Je zet hem in stap 5 in de kluis.

## Stap 3 (jij): Discord

1. Maak een eigen server (bijv. "Hyped HQ") met een kanaal `#scout`.
2. Ga naar discord.com/developers/applications → *New Application* → tab **Bot**:
   - **Reset Token:** kopieer en bewaar het token.
   - **Message Content Intent:** aanzetten. Zonder deze instelling kan de bot je antwoorden niet lezen.
3. Bot uitnodigen:
   - Ga naar *OAuth2 → URL Generator*.
   - Scope: `bot`.
   - Rechten: *View Channels*, *Send Messages*, *Read Message History*.
   - Open de link en kies je server.
4. ID's kopiëren:
   - Zet in Discord *Instellingen → Geavanceerd → Ontwikkelaarsmodus* aan.
   - Rechtsklik op `#scout` → *Kanaal-ID kopiëren*.
   - Rechtsklik op jezelf → *Gebruikers-ID kopiëren*.
   - Deze twee ID's zijn niet geheim; die mag je in de chat sturen.

## Stap 4 (Claude): agent aanmaken

Start een **nieuwe sessie**; die ziet de `ANTHROPIC_API_KEY` uit stap 1. Zeg daar: *"Lees SETUP.md en voer stap 4 uit"*, en stuur de twee Discord-ID's mee.

Claude doet dan het volgende:

```sh
bash scripts/install-ant.sh && export PATH=$PATH:$(go env GOPATH)/bin
# Discord-ID's invullen in agents/hyped-scout/data/instellingen.md
R="agents/hyped-scout"
ant apply --dry-run -v $R/agent.md $R/environment.yaml $R/vault.yaml $R/memory_store-geheugen.yaml
# alleen na jouw akkoord op het plan hierboven:
ant apply --yes $R/agent.md $R/environment.yaml $R/vault.yaml $R/memory_store-geheugen.yaml
bash scripts/seed-memory.sh
```

`claude-lock.json` (met alle ID's) wordt daarna gecommit.

## Stap 5 (jij): sleutels in de kluis

In de Claude Console, bij Managed Agents → **Vaults** → `hyped-scout`, voeg je twee *environment variable*-credentials toe:

| Naam | Waarde | Toegestane hosts |
|---|---|---|
| `YOUTUBE_API_KEY` | sleutel uit stap 2 | `www.googleapis.com`, `youtube.googleapis.com` |
| `DISCORD_BOT_TOKEN` | token uit stap 3 | `discord.com` |

Laat de injectie op **header** staan (standaard in de Console). De agent ziet de sleutels zelf nooit; Anthropic voegt ze pas toe als het verzoek de sandbox verlaat.

**Alternatief:**
1. Zet `YOUTUBE_API_KEY` en `DISCORD_BOT_TOKEN` als secrets in de cloud-omgeving.
2. Start een nieuwe sessie.
3. Laat Claude `bash scripts/add-credentials.sh` draaien.

Ook zo komen de sleutels nooit in de chat.

## Stap 6 (samen): testronde

1. Claude vult het vault-ID uit `claude-lock.json` in `deployment-scout.yaml` in. Daarna maakt hij het schema aan en zet het **direct op pauze**: `ant apply --yes $R/deployment-scout.yaml && ant beta:deployments pause --deployment-id <id>`.
2. Claude start één handmatige ronde: `bash scripts/test-run.sh`. Je krijgt een link naar de sessie in de Console, waar je kunt meekijken.
3. Jij kijkt in Discord of de voorstellen kloppen:
   - Zijn de bronnen goed gekozen?
   - Kloppen de fragmenten?
   - Zijn de invalshoeken bruikbaar?
4. Claude stelt de instructies bij. Herhaal tot je tevreden bent.

## Stap 7: schema aanzetten

Het schema hervatten: om 08:00, 14:00 en 20:00 (Amsterdam). Er geldt een maximum van $3 per ronde.

Jij reageert in `#scout`, bijvoorbeeld `1 3 ja, 2 nee - te politiek`. De agent leert daarvan in de volgende ronde.

## Daarna (versie 2)

- **Transcriptbron toevoegen.** De momenten worden dan veel preciezer dan alleen op basis van hoofdstukken en comments.
- **OpusClip-toegang.** De agent dient alleen de fragmenten in die jij hebt goedgekeurd, en nooit hele video's.
- **Captions en inplannen** via OpusClip.
