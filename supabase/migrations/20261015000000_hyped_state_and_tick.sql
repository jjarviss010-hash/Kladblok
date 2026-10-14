-- Opslag voor de Hyped-deurbel (sessie van vandaag, eigenaar-ID, laatste scoutronde).
-- RLS aan zonder policies: alleen de edge function (service role) kan erbij.
create table if not exists public.hyped_state (
  key text primary key,
  value text not null default '',
  updated_at timestamptz not null default now()
);
alter table public.hyped_state enable row level security;

-- Elk uur de deurbel aanroepen. De functie zelf beslist (in Amsterdamse tijd) of het
-- 08:00, 14:00 of 20:00 is en start dan één scoutronde per tijdslot.
create extension if not exists pg_cron;
create extension if not exists pg_net;

select cron.schedule(
  'hyped-tick',
  '0 * * * *',
  $$
  select net.http_post(
    url := 'https://fxfkjnbhrcdvhofukcpc.supabase.co/functions/v1/hyped-discord/tick',
    headers := '{"Content-Type": "application/json"}'::jsonb,
    body := '{}'::jsonb
  );
  $$
);
