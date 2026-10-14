// Hyped-deurbel: koppelt Discord aan de Hyped-agent (Claude Managed Agents).
//
// - POST /hyped-discord        Discord-interactie (/hyped <bericht>). Antwoordt binnen 3 s
//                              en stuurt het bericht door naar de agent; de agent post zijn
//                              antwoord zelf in Discord.
// - POST /hyped-discord/tick   Elk uur aangeroepen door pg_cron. Start om 08/14/20 uur
//                              (Amsterdam) één scoutronde per tijdslot en houdt het
//                              /hyped-commando geregistreerd. Idempotent, dus veilig zonder
//                              geheim.
//
// Geheimen (Supabase → Edge Functions → Secrets): ANTHROPIC_API_KEY, DISCORD_BOT_TOKEN.

import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import Anthropic from "npm:@anthropic-ai/sdk@0.134.0";
import nacl from "npm:tweetnacl@1.0.3";
import { createClient } from "npm:@supabase/supabase-js@2.49.4";

const CONFIG = {
  discordAppId: "YOUR_DISCORD_APP_ID",
  discordPublicKey: "YOUR_DISCORD_PUBLIC_KEY",
  discordChannelId: "1560048954706759740",
  agentId: "agent_013ycwX1hsBbPTg9QPfxjmq5",
  environmentId: "env_01WGArQbuPxkEVzwFS2qHgFQ",
  vaultId: "vlt_011Cg2qa9eGeAWiZ3jufGVVb",
  memoryStoreId: "memstore_01BPM1DGQcaJEGHroGgJMgTD",
  sessionBudgetCents: "500", // max $5 per dag-sessie
  scoutHours: [8, 14, 20],
  timeZone: "Europe/Amsterdam",
  commandVersion: "1",
};

const DISCORD_API = "https://discord.com/api/v10";
// Pas aanmaken bij gebruik: zonder ANTHROPIC_API_KEY moet de functie toch kunnen opstarten.
let anthropicClient: Anthropic | null = null;
const anthropic = () => (anthropicClient ??= new Anthropic()); // ANTHROPIC_API_KEY
const db = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);

// ---------- opslag ----------

async function getState(key: string): Promise<string | null> {
  const { data } = await db.from("hyped_state").select("value").eq("key", key).maybeSingle();
  return data?.value ?? null;
}

async function setState(key: string, value: string): Promise<void> {
  await db.from("hyped_state").upsert({ key, value, updated_at: new Date().toISOString() });
}

// ---------- tijd ----------

function localParts(now = new Date()) {
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat("nl-NL", {
      timeZone: CONFIG.timeZone, year: "numeric", month: "2-digit", day: "2-digit",
      hour: "2-digit", minute: "2-digit", hourCycle: "h23",
    }).formatToParts(now).map((p) => [p.type, p.value]),
  );
  return {
    date: `${parts.year}-${parts.month}-${parts.day}`,
    hour: Number(parts.hour),
    label: `${parts.day}-${parts.month} ${parts.hour}:${parts.minute}`,
  };
}

// ---------- agent ----------

async function createSession(day: string): Promise<string> {
  const session = await anthropic().beta.sessions.create({
    agent: CONFIG.agentId,
    environment_id: CONFIG.environmentId,
    vault_ids: [CONFIG.vaultId],
    resources: [{ type: "memory_store", memory_store_id: CONFIG.memoryStoreId, access: "read_write" }],
    budget: { type: "limit", max_list_cost: { amount: CONFIG.sessionBudgetCents, currency: "USD" } },
    title: `Hyped ${day}`,
  });
  await setState("session", JSON.stringify({ id: session.id, day }));
  return session.id;
}

async function todaysSession(): Promise<string> {
  const { date } = localParts();
  const saved = await getState("session");
  if (saved) {
    const { id, day } = JSON.parse(saved);
    if (day === date) return id;
  }
  return await createSession(date);
}

/** Stuurt tekst naar de agent. Is de sessie op (budget/beëindigd), dan in een verse sessie. */
async function sendToAgent(text: string): Promise<void> {
  const event = { type: "user.message" as const, content: [{ type: "text" as const, text }] };
  const sessionId = await todaysSession();
  try {
    await anthropic().beta.sessions.events.send(sessionId, { events: [event] });
  } catch (err) {
    if (!(err instanceof Anthropic.BadRequestError || err instanceof Anthropic.NotFoundError)) throw err;
    console.warn("sessie niet bruikbaar, nieuwe sessie", err.message);
    const fresh = await createSession(localParts().date);
    await anthropic().beta.sessions.events.send(fresh, { events: [event] });
  }
}

// ---------- Discord ----------

function discordHeaders(): HeadersInit {
  return {
    Authorization: `Bot ${Deno.env.get("DISCORD_BOT_TOKEN")}`,
    "Content-Type": "application/json",
    "User-Agent": "DiscordBot (https://github.com/jjarviss010-hash/Kladblok, 1.0)",
  };
}

function hexToBytes(hex: string): Uint8Array {
  return new Uint8Array(hex.match(/.{1,2}/g)!.map((b) => parseInt(b, 16)));
}

function verifyDiscord(req: Request, body: string): boolean {
  const signature = req.headers.get("X-Signature-Ed25519");
  const timestamp = req.headers.get("X-Signature-Timestamp");
  if (!signature || !timestamp) return false;
  return nacl.sign.detached.verify(
    new TextEncoder().encode(timestamp + body),
    hexToBytes(signature),
    hexToBytes(CONFIG.discordPublicKey),
  );
}

async function ownerId(): Promise<string> {
  const cached = Deno.env.get("DISCORD_OWNER_ID") ?? (await getState("owner_id"));
  if (cached) return cached;
  const res = await fetch(`${DISCORD_API}/applications/@me`, { headers: discordHeaders() });
  if (!res.ok) throw new Error(`Discord applications/@me: ${res.status}`);
  const app = await res.json();
  const id: string = app.team?.owner_user_id ?? app.owner.id;
  await setState("owner_id", id);
  return id;
}

async function registerCommand(): Promise<void> {
  if ((await getState("command_version")) === CONFIG.commandVersion) return;
  const channel = await fetch(`${DISCORD_API}/channels/${CONFIG.discordChannelId}`, { headers: discordHeaders() });
  if (!channel.ok) throw new Error(`Discord kanaal ophalen: ${channel.status}`);
  const { guild_id } = await channel.json();
  const res = await fetch(`${DISCORD_API}/applications/${CONFIG.discordAppId}/guilds/${guild_id}/commands`, {
    method: "PUT",
    headers: discordHeaders(),
    body: JSON.stringify([{
      name: "hyped",
      description: "Stuur een bericht naar de Hyped-agent",
      type: 1,
      options: [{ type: 3, name: "bericht", description: "Wat moet de agent doen of beantwoorden?", required: true }],
    }]),
  });
  if (!res.ok) throw new Error(`Commando registreren: ${res.status} ${await res.text()}`);
  await setState("command_version", CONFIG.commandVersion);
  console.log("/hyped geregistreerd in server", guild_id);
}

async function followUp(token: string, content: string): Promise<void> {
  await fetch(`${DISCORD_API}/webhooks/${CONFIG.discordAppId}/${token}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
}

function reply(content: string, ephemeral = false): Response {
  return Response.json({ type: 4, data: { content, flags: ephemeral ? 64 : 0 } });
}

async function handleInteraction(req: Request): Promise<Response> {
  const body = await req.text();
  if (!verifyDiscord(req, body)) return new Response("ongeldige handtekening", { status: 401 });
  const interaction = JSON.parse(body);

  if (interaction.type === 1) return Response.json({ type: 1 }); // PING van Discord
  if (interaction.type !== 2 || interaction.data?.name !== "hyped") return reply("Onbekend commando.", true);

  const userId = interaction.member?.user?.id ?? interaction.user?.id;
  if (userId !== (await ownerId())) return reply("Deze agent luistert alleen naar de eigenaar.", true);
  if (interaction.channel_id !== CONFIG.discordChannelId) {
    return reply(`Gebruik /hyped in <#${CONFIG.discordChannelId}>.`, true);
  }

  const text: string = (interaction.data.options?.[0]?.value ?? "").trim();
  if (text.toLowerCase() === "nieuw") {
    EdgeRuntime.waitUntil(setState("session", ""));
    return reply("🆕 Het volgende bericht start een verse sessie (het geheugen blijft bewaard).");
  }
  if (text.toLowerCase() === "stop") {
    EdgeRuntime.waitUntil((async () => {
      const id = await todaysSession();
      await anthropic().beta.sessions.events.send(id, { events: [{ type: "user.interrupt" }] });
    })());
    return reply("⏹️ Gestopt.");
  }

  const { label } = localParts();
  EdgeRuntime.waitUntil(
    sendToAgent(`[Chat] (Discord, ${label})\n${text}`).catch(async (err) => {
      console.error("doorsturen mislukt", err);
      await followUp(interaction.token, `⚠️ Kon de agent niet bereiken: ${err.message}`);
    }),
  );
  return reply(`📨 **${text.slice(0, 1800)}**\n-# De agent is ermee bezig…`);
}

async function handleTick(): Promise<Response> {
  const result: Record<string, string> = {};
  try {
    await ownerId();
    await registerCommand();
    result.command = "ok";
  } catch (err) {
    result.command = `fout: ${(err as Error).message}`;
  }
  const { date, hour, label } = localParts();
  const slot = `${date}T${hour}`;
  if (CONFIG.scoutHours.includes(hour) && (await getState("last_scout_slot")) !== slot) {
    await setState("last_scout_slot", slot);
    await sendToAgent(`[Scoutronde] ${label}`);
    result.scout = `gestart (${label})`;
  }
  return Response.json(result);
}

Deno.serve(async (req) => {
  if (req.method !== "POST") return new Response("Hyped-deurbel", { status: 200 });
  try {
    return new URL(req.url).pathname.endsWith("/tick") ? await handleTick() : await handleInteraction(req);
  } catch (err) {
    console.error(err);
    return new Response("interne fout", { status: 500 });
  }
});
