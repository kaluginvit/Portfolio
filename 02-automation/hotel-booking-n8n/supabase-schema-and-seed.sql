-- Supabase schema + seed for graduation project
-- Project: Hotel booking via form + notifications
-- Stack: n8n (webhook/cron) + Supabase + Gmail + Tally
--
-- How to use:
-- 1) Open Supabase SQL Editor
-- 2) Paste and run this whole script
-- 3) Verify tables rooms/bookings and seed rows in rooms

begin;

-- 1) rooms
create table if not exists public.rooms (
  id uuid primary key default gen_random_uuid(),
  room_id text generated always as (id::text) stored,
  hotel_name text not null,
  room_type text not null,
  date_from date not null,
  date_to date not null,
  status text not null default 'free' check (status in ('free', 'reserved')),
  price numeric not null check (price >= 0),
  updated_at timestamptz not null default now()
);

create index if not exists rooms_lookup_idx
  on public.rooms (hotel_name, room_type, status);

create index if not exists rooms_dates_idx
  on public.rooms (date_from, date_to);

-- 2) bookings
create table if not exists public.bookings (
  id uuid primary key default gen_random_uuid(),
  booking_id text generated always as (id::text) stored,
  request_id text not null unique,
  room_id uuid null references public.rooms(id) on delete set null,
  client_name text not null,
  email text not null,
  hotel_name text not null,
  room_type text not null,
  date_from date not null,
  date_to date not null,
  status text not null default 'reserved' check (status in ('reserved', 'confirmed', 'cancelled')),
  payment_status text not null default 'pending' check (payment_status in ('pending', 'paid')),
  created_at timestamptz not null default now()
);

create index if not exists bookings_created_at_idx
  on public.bookings (created_at desc);

create index if not exists bookings_status_idx
  on public.bookings (status, payment_status);

-- 3) Optional: keep updated_at fresh on room updates
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

drop trigger if exists trg_rooms_updated_at on public.rooms;
create trigger trg_rooms_updated_at
before update on public.rooms
for each row execute function public.set_updated_at();

-- 4) Seed rooms (5–10 rows)
-- Date model (per project assumption): rooms.date_from/date_to define availability window.
insert into public.rooms (hotel_name, room_type, date_from, date_to, status, price)
values
  ('Hotel_Aurora', 'standard', '2026-05-01', '2026-05-31', 'free', 4500),
  ('Hotel_Aurora', 'standard', '2026-06-01', '2026-06-30', 'free', 4700),
  ('Hotel_Aurora', 'deluxe',   '2026-05-10', '2026-06-10', 'free', 7200),
  ('Hotel_Neva',   'standard', '2026-05-01', '2026-05-20', 'free', 3900),
  ('Hotel_Neva',   'deluxe',   '2026-05-01', '2026-05-31', 'free', 6100),
  ('Hotel_Ocean',  'standard', '2026-05-15', '2026-06-15', 'free', 5200),
  ('Hotel_Ocean',  'suite',    '2026-05-01', '2026-05-31', 'free', 9900),
  ('Hotel_Ural',   'standard', '2026-05-01', '2026-05-31', 'reserved', 4100),
  ('Hotel_Ural',   'deluxe',   '2026-05-01', '2026-05-31', 'free', 6800)
on conflict do nothing;

commit;
