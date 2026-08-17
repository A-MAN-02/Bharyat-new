-- ============================================================
-- QProcure schema (Supabase / Postgres)
-- Covers: Vendor directory, RFQ creation, Dispatch, Responses,
--         Vendor scorecard, Award/PO conversion
-- ============================================================

-- ---------- Module 1: Vendor directory ----------
create table if not exists vendors (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  category text,                    -- e.g. MCU, Passive, Connector
  region text,                      -- e.g. India, SG, China
  email text not null,
  rating text check (rating in ('A','B','C')) default 'C',  -- auto-computed later
  created_at timestamptz default now()
);

-- ---------- Module 2: RFQ creation ----------
create table if not exists rfqs (
  id uuid primary key default gen_random_uuid(),
  rfq_number text unique not null,       -- e.g. RFQ-1042
  title text,
  template text default 'standard_component_rfq',
  status text check (status in ('draft','dispatched','closed','awarded')) default 'draft',
  created_by text,                       -- Bharyat user (Arpita / Saurav)
  created_at timestamptz default now()
);

create table if not exists rfq_lines (
  id uuid primary key default gen_random_uuid(),
  rfq_id uuid references rfqs(id) on delete cascade,
  part_number text not null,
  qty integer not null,
  target_price numeric,
  notes text
);

-- ---------- Module 3: Vendor selection & dispatch ----------
create table if not exists rfq_dispatch (
  id uuid primary key default gen_random_uuid(),
  rfq_id uuid references rfqs(id) on delete cascade,
  vendor_id uuid references vendors(id) on delete cascade,
  channel text check (channel in ('email','whatsapp')) default 'email', -- whatsapp unused for now
  sent_at timestamptz,
  reminder_at timestamptz,           -- e.g. now() + interval '48 hours'
  status text check (status in ('pending','sent','failed')) default 'pending',
  resend_email_id text                -- id returned by Resend for tracking
);

-- ---------- Module 4: RFQ responses / dashboard ----------
create table if not exists rfq_responses (
  id uuid primary key default gen_random_uuid(),
  rfq_id uuid references rfqs(id) on delete cascade,
  vendor_id uuid references vendors(id) on delete cascade,
  raw_email_body text,               -- pasted / fetched reply, for parsing
  price numeric,
  moq integer,
  lead_time_weeks numeric,
  extraction_status text check (extraction_status in ('auto_parsed','needs_verify','unread')) default 'unread',
  responded_at timestamptz default now()
);

-- ---------- Module 5: Vendor scorecard ----------
-- Derived/aggregated view, recalculated after every closed RFQ.
create table if not exists vendor_scores (
  vendor_id uuid primary key references vendors(id) on delete cascade,
  response_rate numeric,
  avg_response_hours numeric,
  on_time_delivery_pct numeric,
  price_vs_ref_pct numeric,
  responsiveness_stars integer,
  price_competitiveness_stars integer,
  delivery_reliability_stars integer,
  compliance_stars integer,          -- from QLens, placeholder for now
  updated_at timestamptz default now()
);

-- ---------- Module 6: Award & PO conversion ----------
create table if not exists awards (
  id uuid primary key default gen_random_uuid(),
  rfq_id uuid references rfqs(id) on delete cascade,
  vendor_id uuid references vendors(id) on delete cascade,
  response_id uuid references rfq_responses(id),
  justification text check (justification in ('lowest_price','best_rating','fastest_lead_time')),
  justification_note text,
  requested_documents jsonb default '[]',  -- e.g. ["Certificate of origin","RoHS declaration"]
  po_status text check (po_status in ('draft','sent')) default 'draft',
  po_number text,
  created_at timestamptz default now()
);

create index if not exists idx_rfq_lines_rfq on rfq_lines(rfq_id);
create index if not exists idx_dispatch_rfq on rfq_dispatch(rfq_id);
create index if not exists idx_responses_rfq on rfq_responses(rfq_id);
