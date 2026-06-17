-- ╔══════════════════════════════════════════════════════════════════════════╗
-- ║                    UniPilot — Supabase Schema                          ║
-- ║  Run this in your Supabase SQL editor to create all tables.            ║
-- ╚══════════════════════════════════════════════════════════════════════════╝

-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- ── Users ──────────────────────────────────────────────────────────────────────
create table if not exists users (
  id            uuid primary key default uuid_generate_v4(),
  firebase_uid  text unique not null,
  email         text unique not null,
  name          text,
  avatar_url    text,
  plan          text default 'free' check (plan in ('free','pro','enterprise')),
  created_at    timestamptz default now(),
  updated_at    timestamptz default now()
);

-- ── Student Profiles ───────────────────────────────────────────────────────────
create table if not exists profiles (
  id                  uuid primary key default uuid_generate_v4(),
  user_id             uuid references users(id) on delete cascade,
  country             text not null,
  intake_year         int  not null,
  intended_major      text not null,
  preferred_countries text[] default '{}',
  budget_range        text default 'any',
  created_at          timestamptz default now(),
  updated_at          timestamptz default now()
);

-- ── Academic Records ───────────────────────────────────────────────────────────
create table if not exists academic_records (
  id               uuid primary key default uuid_generate_v4(),
  profile_id       uuid references profiles(id) on delete cascade,
  curriculum       text not null,
  gpa              numeric(3,2),
  percentage       numeric(5,2),
  predicted_grades text,
  created_at       timestamptz default now()
);

-- ── Test Scores ────────────────────────────────────────────────────────────────
create table if not exists test_scores (
  id          uuid primary key default uuid_generate_v4(),
  profile_id  uuid references profiles(id) on delete cascade,
  test_type   text not null,   -- SAT, ACT, IELTS, TOEFL, Duolingo, JEE, BITSAT, AP
  score       numeric,
  subject     text,            -- for AP scores
  test_date   date,
  created_at  timestamptz default now()
);

-- ── Extracurriculars ───────────────────────────────────────────────────────────
create table if not exists extracurriculars (
  id               uuid primary key default uuid_generate_v4(),
  profile_id       uuid references profiles(id) on delete cascade,
  category         text not null,
  title            text not null,
  description      text,
  duration         text,
  impact           text,
  awards           text,
  leadership_level text default 'None',
  created_at       timestamptz default now(),
  updated_at       timestamptz default now()
);

-- ── Universities ───────────────────────────────────────────────────────────────
create table if not exists universities (
  id               uuid primary key default uuid_generate_v4(),
  slug             text unique not null,   -- e.g. 'mit', 'stanford'
  name             text not null,
  short_name       text,
  country          text,
  country_code     char(2),
  city             text,
  ranking          int,
  acceptance_rate  numeric(5,2),
  total_enrollment int,
  type             text check (type in ('Public','Private')),
  research_output  text,
  website_url      text,
  logo_url         text,
  tags             text[] default '{}',
  created_at       timestamptz default now(),
  updated_at       timestamptz default now()
);

-- ── Programs ───────────────────────────────────────────────────────────────────
create table if not exists programs (
  id                   uuid primary key default uuid_generate_v4(),
  university_id        uuid references universities(id) on delete cascade,
  name                 text not null,
  degree               text,
  major                text,
  tuition_usd          numeric(10,2),
  duration_years       int,
  portfolio_required   boolean default false,
  research_required    boolean default false,
  min_gpa              numeric(3,2),
  min_sat              int,
  min_act              int,
  min_ielts            numeric(3,1),
  min_toefl            int,
  notes                text,
  created_at           timestamptz default now(),
  updated_at           timestamptz default now()
);

-- ── Deadlines ─────────────────────────────────────────────────────────────────
create table if not exists deadlines (
  id            uuid primary key default uuid_generate_v4(),
  program_id    uuid references programs(id) on delete cascade,
  type          text not null check (type in ('Early Action','Early Decision','Regular Decision','International')),
  deadline_date date not null,
  intake_year   int not null,
  created_at    timestamptz default now()
);

-- ── Scholarships ───────────────────────────────────────────────────────────────
create table if not exists scholarships (
  id                 uuid primary key default uuid_generate_v4(),
  program_id         uuid references programs(id) on delete cascade,
  name               text not null,
  amount             numeric(12,2),
  currency           char(3) default 'USD',
  eligibility        text[] default '{}',
  deadline           date,
  renewable          boolean default false,
  description        text,
  created_at         timestamptz default now()
);

-- ── University Matches (saved per student) ─────────────────────────────────────
create table if not exists university_matches (
  id              uuid primary key default uuid_generate_v4(),
  profile_id      uuid references profiles(id) on delete cascade,
  university_id   uuid references universities(id),
  program_id      uuid references programs(id),
  tier            text check (tier in ('Reach','Target','Likely')),
  match_score     int,
  outlook         text,
  is_saved        boolean default false,
  is_applying     boolean default false,
  created_at      timestamptz default now(),
  updated_at      timestamptz default now(),
  unique (profile_id, program_id)
);

-- ── Roadmaps ───────────────────────────────────────────────────────────────────
create table if not exists roadmaps (
  id          uuid primary key default uuid_generate_v4(),
  profile_id  uuid references profiles(id) on delete cascade,
  generated_at timestamptz default now(),
  months_data  jsonb not null default '[]',   -- full roadmap JSON
  updated_at   timestamptz default now()
);

-- ── Tasks ─────────────────────────────────────────────────────────────────────
create table if not exists tasks (
  id                      uuid primary key default uuid_generate_v4(),
  roadmap_id              uuid references roadmaps(id) on delete cascade,
  profile_id              uuid references profiles(id) on delete cascade,
  month                   text not null,
  title                   text not null,
  description             text,
  why                     text,
  category                text,
  difficulty              text check (difficulty in ('Easy','Medium','Hard')),
  estimated_hours         int,
  profile_gain            numeric(3,2),
  universities_impacted   text[] default '{}',
  status                  text default 'todo' check (status in ('todo','in_progress','done')),
  due_date                date,
  created_at              timestamptz default now(),
  updated_at              timestamptz default now()
);

-- ── Gap Analysis Results ───────────────────────────────────────────────────────
create table if not exists gap_analyses (
  id                     uuid primary key default uuid_generate_v4(),
  profile_id             uuid references profiles(id) on delete cascade,
  university_id          uuid references universities(id),
  admission_likelihood   numeric(5,2),
  key_insight            text,
  gaps_json              jsonb default '[]',
  ai_recommendations     text[] default '{}',
  generated_at           timestamptz default now()
);

-- ── AI Reports ────────────────────────────────────────────────────────────────
create table if not exists ai_reports (
  id               uuid primary key default uuid_generate_v4(),
  profile_id       uuid references profiles(id) on delete cascade,
  overall_score    numeric(4,2),
  dimension_scores jsonb default '{}',
  strengths        text[] default '{}',
  weaknesses       text[] default '{}',
  opportunities    text[] default '{}',
  ai_narrative     text,
  generated_at     timestamptz default now()
);

-- ── Progress Updates ──────────────────────────────────────────────────────────
create table if not exists progress_updates (
  id               uuid primary key default uuid_generate_v4(),
  profile_id       uuid references profiles(id) on delete cascade,
  update_type      text not null,   -- 'extracurricular_added', 'score_updated', 'task_completed'
  description      text,
  score_delta      numeric(4,2),
  metadata         jsonb default '{}',
  created_at       timestamptz default now()
);

-- ── Admin: Acceptance Data ────────────────────────────────────────────────────
create table if not exists acceptance_data (
  id              uuid primary key default uuid_generate_v4(),
  university_id   uuid references universities(id),
  intake_year     int not null,
  total_applied   int,
  total_admitted  int,
  acceptance_rate numeric(5,2),
  median_gpa      numeric(3,2),
  median_sat      int,
  median_act      int,
  source_url      text,
  created_at      timestamptz default now()
);

-- ── Row Level Security ────────────────────────────────────────────────────────
alter table users               enable row level security;
alter table profiles            enable row level security;
alter table academic_records    enable row level security;
alter table test_scores         enable row level security;
alter table extracurriculars    enable row level security;
alter table university_matches  enable row level security;
alter table roadmaps            enable row level security;
alter table tasks               enable row level security;
alter table gap_analyses        enable row level security;
alter table ai_reports          enable row level security;
alter table progress_updates    enable row level security;

-- Users can only access their own data
create policy "Users: own data" on users
  for all using (firebase_uid = current_setting('app.firebase_uid', true));

create policy "Profiles: own data" on profiles
  for all using (
    user_id = (
      select id from users
      where firebase_uid = current_setting('app.firebase_uid', true)
    )
  );

-- Universities and programs are public read
create policy "Universities: public read" on universities for select using (true);
create policy "Programs: public read"     on programs     for select using (true);
create policy "Deadlines: public read"    on deadlines    for select using (true);
create policy "Scholarships: public read" on scholarships for select using (true);

-- ── Indexes ────────────────────────────────────────────────────────────────────
create index if not exists idx_profiles_user_id         on profiles(user_id);
create index if not exists idx_academic_records_profile on academic_records(profile_id);
create index if not exists idx_test_scores_profile      on test_scores(profile_id);
create index if not exists idx_extracurriculars_profile on extracurriculars(profile_id);
create index if not exists idx_uni_matches_profile      on university_matches(profile_id);
create index if not exists idx_tasks_profile            on tasks(profile_id);
create index if not exists idx_tasks_status             on tasks(status);
create index if not exists idx_universities_ranking     on universities(ranking);
create index if not exists idx_universities_country     on universities(country);
create index if not exists idx_programs_major           on programs(major);
create index if not exists idx_deadlines_date           on deadlines(deadline_date);

-- ── Seed: insert sample universities ──────────────────────────────────────────
insert into universities (slug, name, short_name, country, country_code, city, ranking, acceptance_rate, type, research_output, website_url, tags) values
  ('mit',      'Massachusetts Institute of Technology', 'MIT',         'United States', 'US', 'Cambridge, MA',  1,   4.0,  'Private', 'Very High', 'https://mit.edu',         array['STEM','Research','Tech','Top-3']),
  ('stanford', 'Stanford University',                  'Stanford',    'United States', 'US', 'Stanford, CA',   3,   4.0,  'Private', 'Very High', 'https://stanford.edu',    array['STEM','Research','Entrepreneurship','Top-5']),
  ('cmu',      'Carnegie Mellon University',           'CMU',         'United States', 'US', 'Pittsburgh, PA', 25,  11.0, 'Private', 'Very High', 'https://cmu.edu',         array['CS','AI','Robotics','Tech']),
  ('gatech',   'Georgia Institute of Technology',      'Georgia Tech','United States', 'US', 'Atlanta, GA',    33,  17.0, 'Public',  'Very High', 'https://gatech.edu',      array['Engineering','CS','AI','Affordable']),
  ('ucb',      'University of California, Berkeley',  'UC Berkeley', 'United States', 'US', 'Berkeley, CA',   30,  14.0, 'Public',  'Very High', 'https://berkeley.edu',    array['CS','Research','Public Ivy','West Coast']),
  ('imperial', 'Imperial College London',             'Imperial',    'United Kingdom','GB', 'London',          8,   14.0, 'Public',  'Very High', 'https://imperial.ac.uk',  array['Engineering','STEM','London','Top-10']),
  ('waterloo', 'University of Waterloo',              'Waterloo',    'Canada',         'CA', 'Waterloo, ON',   149, 53.0, 'Public',  'High',      'https://uwaterloo.ca',    array['CS','Co-op','Affordable','Canada']),
  ('nus',      'National University of Singapore',    'NUS',         'Singapore',      'SG', 'Singapore',      19,  8.0,  'Public',  'Very High', 'https://nus.edu.sg',      array['Asia','Research','Affordable','Top-20']),
  ('toronto',  'University of Toronto',               'U of T',      'Canada',         'CA', 'Toronto, ON',    25,  43.0, 'Public',  'Very High', 'https://utoronto.ca',     array['Research','Canada','CS','AI']),
  ('tum',      'Technical University of Munich',      'TU Munich',   'Germany',        'DE', 'Munich',          37,  8.0,  'Public',  'Very High', 'https://tum.de',          array['Engineering','Europe','Affordable','Research'])
on conflict (slug) do nothing;
