-- Run in Supabase SQL Editor (Dashboard → SQL → New query)

create table if not exists public.scans (
  id                    uuid primary key default gen_random_uuid(),
  label                 text,
  input_type            text not null default 'text'
    check (input_type in ('text', 'file', 'with_reference')),
  total_sentences       integer not null,
  plagiarized_sentences integer not null,
  plagiarism_percent    double precision not null,
  source_breakdown      jsonb not null default '{}'::jsonb,
  results               jsonb not null default '[]'::jsonb,
  created_at            timestamptz not null default now()
);

create index if not exists scans_created_at_idx on public.scans (created_at desc);

alter table public.scans enable row level security;

-- Backend uses the service role key and bypasses RLS.
-- For direct browser access with the anon key, allow read/write on scans:
create policy "Allow anon read scans"
  on public.scans for select
  to anon, authenticated
  using (true);

create policy "Allow anon insert scans"
  on public.scans for insert
  to anon, authenticated
  with check (true);
