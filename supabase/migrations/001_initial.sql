create table if not exists profiles (
 id uuid primary key, email text not null unique, name text not null,
 role text not null default 'student' check(role in ('student','counsellor','admin','expert')),
 password_hash text, degree text, semester integer check(semester between 1 and 16),
 cgpa numeric check(cgpa between 0 and 4), bio text not null default '', specialty text not null default '',
 created_at timestamptz not null default now()
);
create table if not exists careers (
 id text primary key, title text not null, category text not null, summary text not null,
 interests jsonb not null, skills jsonb not null, degrees jsonb not null default '[]',
 active boolean not null default true, source text not null,
 review_status text not null default 'Starter profile — expert review required', updated_at timestamptz not null default now()
);
create table if not exists settings (id integer primary key check(id=1), weights jsonb not null, updated_at timestamptz not null default now());
insert into settings(id,weights) values(1,'{"interest":0.5,"skills":0.35,"degree":0.15}') on conflict do nothing;
create table if not exists assessments (
 id uuid primary key, user_id uuid not null references profiles(id) on delete cascade,
 answers jsonb not null, scores jsonb not null, skills jsonb not null,
 recommendation_ids jsonb not null, weights jsonb not null, created_at timestamptz not null default now()
);
create index if not exists assessments_owner on assessments(user_id,created_at desc);
create table if not exists drafts (user_id uuid primary key references profiles(id) on delete cascade, data jsonb not null, updated_at timestamptz not null default now());
create table if not exists feedback (
 user_id uuid not null references profiles(id) on delete cascade, career_id text not null references careers(id),
 relevant boolean not null, rating integer check(rating between 1 and 5), primary key(user_id,career_id)
);
create table if not exists milestones (
 user_id uuid not null references profiles(id) on delete cascade, career_id text not null references careers(id),
 skill text not null, complete boolean not null default false, primary key(user_id,career_id,skill)
);
create table if not exists slots (
 id uuid primary key, counsellor_id uuid not null references profiles(id) on delete cascade,
 starts_at timestamptz not null, unique(counsellor_id,starts_at)
);
create table if not exists bookings (
 id uuid primary key, slot_id uuid not null references slots(id) on delete cascade,
 student_id uuid not null references profiles(id) on delete cascade,
 consent boolean not null default false, status text not null default 'booked' check(status in ('booked','cancelled')),
 created_at timestamptz not null default now()
);
create unique index if not exists one_booking_per_slot on bookings(slot_id) where status='booked';
create table if not exists session_notes (booking_id uuid primary key references bookings(id) on delete cascade, note text not null, updated_at timestamptz not null default now());
create table if not exists notifications (
 id uuid primary key, user_id uuid not null references profiles(id) on delete cascade,
 message text not null, read boolean not null default false, created_at timestamptz not null default now()
);
create table if not exists proposals (
 id uuid primary key, expert_id uuid not null references profiles(id) on delete cascade,
 career_id text not null references careers(id), summary text not null, source text not null, patch jsonb not null,
 status text not null default 'pending' check(status in ('pending','approved','rejected')),
 reviewed_by uuid references profiles(id) on delete set null, created_at timestamptz not null default now()
);
-- In Supabase, deleting Auth identity cascades through the complete application profile.
do $$ begin
 if to_regclass('auth.users') is not null and not exists(select 1 from pg_constraint where conname='profiles_auth_identity') then
  alter table profiles add constraint profiles_auth_identity foreign key(id) references auth.users(id) on delete cascade;
 end if;
end $$;
-- The browser has no direct Data API access. All app data goes through authenticated NestJS routes.
-- The server's PostgreSQL credential is privileged; API authorization remains mandatory.
do $$ declare t text; begin
 foreach t in array array['profiles','careers','settings','assessments','drafts','feedback','milestones','slots','bookings','session_notes','notifications','proposals'] loop
  execute format('alter table %I enable row level security',t);
  if exists(select 1 from pg_roles where rolname='anon') then execute format('revoke all on %I from anon',t); end if;
  if exists(select 1 from pg_roles where rolname='authenticated') then execute format('revoke all on %I from authenticated',t); end if;
 end loop;
end $$;
