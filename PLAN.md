# Hyped Social Media Agent: plan

Laatst bijgewerkt: 14 oktober 2026

## Doel

Een Claude-agent (via de Claude API) die de Hyped-accounts runt op TikTok, Instagram en YouTube:

- bronvideo's vinden die het waard zijn om te clippen (podcasts, sport, grappige momenten)
- clippen via OpusClip
- de beste clips kiezen en per platform captions schrijven
- inplannen en publiceren
- reageren op volgers
- leren van wat goed presteert

## Huidige situatie (gemeten via OpusClip, 14 okt 2026)

| | |
|---|---|
| YouTube | Hyped (`UCWMqHvZffferuGDkosfCapQ`) |
| TikTok | `@itshyped` (Business) |
| Instagram | `@itshypedmedia` (Business) |
| OpusClip | Pro-plan, API-toegang actief, alle 3 accounts gekoppeld voor publiceren |
| Credits | 760 minuten over. API-limiet 900/maand, reset 1 nov. Ongeveer 1 credit per minuut bronvideo. |

**Postgedrag van 14 sep tot 13 okt:**

- 146 clips uit 114 bronvideo's. Elke clip ging tegelijk naar alle 3 platforms, samen 426 posts.
- Alles direct gepost, niets ingepland. Het aantal per dag wisselt tussen 0 en 12.
- Piek tussen 21 en 23 uur UTC (23 tot 01 uur Nederlandse tijd).
- 4 mislukte posts, waarvan 2 keer "YouTube daily upload limit".
- Inhoud: politiek/nieuwscommentaar, podcasts, sportstudio's (Champions League) en comedy (SNL).

## Kritieke risico's (deze bepalen het ontwerp)

### 1. YouTube remt clipkanalen af (aangekondigd 1 okt 2026)

YouTube geeft Shorts die vooral clips van anderen herposten minder bereik. Clips met eigen commentaar, montage of verhaal blijven wel gewaardeerd. Hyped past nu precies in de doelgroep van deze maatregel.

- Meer volume automatiseren zonder eigen toevoeging versnelt het probleem.
- **Gevolg voor het ontwerp:** de agent moet bij elke clip eigen waarde toevoegen: een eigen hook, tekst-overlay of commentaar.
- Status: bevestigd door meerdere media (Dexerto, Android Authority). YouTube noemde geen startdatum en geen drempel.

### 2. Auteursrecht

SNL (NBCUniversal) en uitzendingen van de Champions League horen bij de partijen die het actiefst claimen.

- Drie copyright-strikes op YouTube betekent dat het kanaal wordt verwijderd.
- **Gevolg voor het ontwerp:** elke bron krijgt een risicoscore. We werken met een whitelist van bronnen die clippen toestaan of aanmoedigen; veel podcasts doen dat. Bronnen met hoog risico gaan nooit automatisch live.

### 3. Platform-API's

- **Publiceren loopt via OpusClip.** OpusClip is al een goedgekeurde app bij TikTok, Instagram en YouTube.
- **Zelf koppelen kost veel tijd.** TikTok publiceert zonder audit alleen privé; die audit duurt weken. YouTube zet uploads vanuit niet-geverifieerde projecten op privé.
- **Reageren op comments:**
  - **YouTube:** kan via de YouTube Data API.
  - **Instagram:** kan via de Graph API (Meta-app nodig).
  - **TikTok:** geen officiële API om te reageren. Dit blijft voorlopig handwerk.

### 4. AI-reacties op politieke content

Een fout of toondoof antwoord onder een politieke clip kan het merk beschadigen. Daarom geen automatische reacties onder politieke clips.

### 5. OpusClip-credits zijn de bottleneck

Een podcast van 2 uur kost ongeveer 120 credits. Met 760 credits kun je dus zo'n 6 volledige podcasts clippen. De agent moet daarom eerst het interessante fragment bepalen en alleen dat stuk laten clippen (`rangeStart`/`rangeEnd`).

## Architectuur

```
 ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌───────────┐   ┌───────────┐
 │  Scout  │──▶│ Clipper  │──▶│  Editor  │──▶│ Goedkeuring│──▶│ Publisher │
 │ vindt   │   │ OpusClip │   │ kiest +  │   │ (Telegram) │   │ OpusClip  │
 │ bronnen │   │ (fragment)│  │ captions │   │  jij: ✅/❌ │   │ inplannen │
 └─────────┘   └──────────┘   └──────────┘   └───────────┘   └─────┬─────┘
      ▲                                                            │
      │        ┌──────────┐        ┌──────────────┐                │
      └────────│ Analist  │◀───────│  Engagement  │◀───────────────┘
               │ leert wat│        │ comments YT/IG│
               │ werkt    │        └──────────────┘
               └──────────┘
```

**Onderdelen:**

- **Claude API:** de agent-loop met eigen tools via de tool runner van de Anthropic SDK.
- **Tools (eerste versie):**
  - YouTube: zoeken en videostatistieken (Data API, alleen lezen)
  - OpusClip: `submit`, `list_clips`, `transcript`, `schedule`
  - Telegram: berichten sturen ter goedkeuring
- **Opslag:** SQLite met bronnen, gemaakte clips, posts, prestaties en jouw beslissingen. Dit voorkomt dubbele posts en vormt het geheugen waarmee de agent leert.
- **Planner:** een cronjob die elke paar uur draait.
- **Leerdata die al bestaat:** van alle clips die OpusClip de afgelopen maand maakte, koos jij er 146 om te posten. Die keuzes (en je hartjes in OpusClip) laten zien wat jij goed vindt. De Editor gebruikt ze als voorbeelden.

## Fasen

### Fase 1: MVP, clip-pipeline met goedkeuring

**Wat hij doet:**

- **Scout:** volgt een lijst met bronkanalen en meet hoe snel views groeien (views per uur sinds publicatie).
- **Clipper:** bepaalt het beste fragment en laat alleen dat clippen.
- **Editor:** kiest de beste 1 à 2 clips en schrijft een aparte caption per platform, inclusief eigen hook.
- **Goedkeuring:** stuurt de clips naar Telegram met preview, caption, bron en risicoscore.
- **Publisher:** plant goedgekeurde clips verspreid over de dag in via OpusClip. Hij houdt rekening met de uploadlimiet van YouTube.

**Klaar als:** jij minder dan 15 minuten per dag kwijt bent, er minstens evenveel output is als nu, en posts gelijkmatig over de dag verspreid zijn.

### Fase 2: Engagement

- De agent schrijft conceptreacties op comments op YouTube en Instagram. Jij keurt ze goed via Telegram.
- Nooit automatische reacties onder politieke clips.
- TikTok blijft handwerk (geen API).

### Fase 3: Analist

- Prestaties ophalen: YouTube Analytics API en Instagram Insights. Voor TikTok moet nog worden onderzocht wat via de Business API kan.
- Wekelijks rapport: welke bronnen, onderwerpen, lengtes en tijdstippen werken.
- De uitkomsten sturen de Scout en de Editor bij.

### Fase 4: Geleidelijke autonomie

- Automatisch posten zonder goedkeuring, alleen voor categorieën met laag risico en bewezen prestaties.
- Automatisch reageren op eenvoudige comments (bedankjes, vragen naar de bron).

## Wat de agent bewust niet doet (voorlopig)

- Posten zonder jouw goedkeuring.
- Reageren onder politieke clips of op DM's.
- Dezelfde caption gebruiken op alle drie de platforms.
- Volledige lange video's clippen als een fragment volstaat.

## Kosten (schatting, meten in week 1)

| Post | Orde van grootte |
|---|---|
| Claude API (`claude-opus-5-5`, $4/$20 per miljoen tokens) | ±$0,30–0,50 per scoutronde. Bij 6 rondes per dag: $50–90/maand. Prompt caching en een lagere effort kunnen dit fors verlagen. |
| OpusClip | Je huidige Pro-abonnement. Credits zijn de beperking, niet geld. |
| Hosting | $5–10/maand (kleine server of Railway/Fly) |
| YouTube Data API / Telegram | gratis binnen de limieten |

## Benodigd (keys en accounts)

- [ ] Anthropic API key (console.anthropic.com)
- [ ] OpusClip API key (Pro-API is in bèta; toegang staat al aan)
- [ ] Google Cloud-project met YouTube Data API v3 (API key om te lezen)
- [ ] Telegram-bot (via @BotFather)
- [ ] Fase 2: Meta-app voor Instagram-comments, OAuth voor YouTube-comments

## Open beslissingen

1. Programmeertaal: Python (aanbevolen) of TypeScript?
2. Goedkeuring: via Telegram (aanbevolen) of via een webdashboard?
3. Hosting: kleine eigen server of Anthropic Managed Agents?
4. Bronnenlijst: welke kanalen en podcasts moet de Scout volgen?
5. Waar kost het huidige proces je de meeste tijd: bronnen zoeken, clips kiezen, captions schrijven of posten?

## Bronnen

- [TikTok Content Posting API (Direct Post)](https://developers.tiktok.com/docs/en/content-posting-api-reference-direct-post)
- [YouTube Data API: videos.insert](https://developers.google.com/youtube/v3/docs/videos/insert)
- [Instagram Content Publishing](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/content-publishing)
- [OpusClip social posting API](https://help.opus.pro/api-reference/endpoints/social-posting/overview)
- [Dexerto: YouTube cracks down on clipping channels](https://www.dexerto.com/youtube/youtube-cracks-down-on-clipping-channels-in-shorts-update-prioritizing-original-content-3415700/)
- [Android Authority: YouTube Shorts promoting original content](https://www.androidauthority.com/youtube-shorts-promoting-original-content-reposts-3718668/)
- [RapidDev: TikTok comment moderation via API](https://www.rapidevelopers.com/md/api-automations/how-to-automate-tiktok-comment-moderation-using-the-api)
