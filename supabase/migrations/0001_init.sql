-- India TT-buy tracker initial schema
-- Tables: banks, rates
-- View:   latest_rates (most recent row per bank/currency/rate_type)
-- RLS:    public read on banks and rates; writes restricted to service role

create extension if not exists "pgcrypto";

create table if not exists public.banks (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    slug text not null unique,
    source_url text not null,
    parser_type text not null check (parser_type in ('html', 'pdf', 'html_dynamic')),
    enabled boolean not null default true,
    created_at timestamptz not null default now()
);

create table if not exists public.rates (
    id bigserial primary key,
    bank_id uuid not null references public.banks(id) on delete cascade,
    currency text not null,
    rate_type text not null,
    rate_value numeric(12, 4) not null,
    effective_date date not null,
    scraped_at timestamptz not null default now(),
    source_url text,
    source_title text,
    parser_version text,
    source_status text,
    notes text,
    created_at timestamptz not null default now(),
    constraint rates_unique_per_day unique (bank_id, currency, rate_type, effective_date)
);

create index if not exists rates_currency_type_date_idx
    on public.rates (currency, rate_type, effective_date desc);

create index if not exists rates_bank_date_idx
    on public.rates (bank_id, effective_date desc);

-- Latest rate per (bank, currency, rate_type)
create or replace view public.latest_rates as
select distinct on (r.bank_id, r.currency, r.rate_type)
    r.id,
    r.bank_id,
    b.slug         as bank_slug,
    b.name         as bank_name,
    r.currency,
    r.rate_type,
    r.rate_value,
    r.effective_date,
    r.scraped_at,
    r.source_url,
    r.source_title,
    r.parser_version,
    r.source_status,
    r.notes
from public.rates r
join public.banks b on b.id = r.bank_id
order by r.bank_id, r.currency, r.rate_type, r.effective_date desc, r.scraped_at desc;

-- Row level security
alter table public.banks enable row level security;
alter table public.rates enable row level security;

drop policy if exists "banks are publicly readable" on public.banks;
create policy "banks are publicly readable"
    on public.banks for select
    to anon, authenticated
    using (true);

drop policy if exists "rates are publicly readable" on public.rates;
create policy "rates are publicly readable"
    on public.rates for select
    to anon, authenticated
    using (true);

-- Seed bank metadata. Keep slugs stable; parsers look themselves up by slug.
insert into public.banks (name, slug, source_url, parser_type, enabled) values
    ('Axis Bank',              'axis',        'https://application.axis.bank.in/WebForms/currency-convert-forex/index.aspx',                                            'html_dynamic', true),
    ('State Bank of India',    'sbi',         'https://sbi.co.in/documents/16012/1400784/FOREX_CARD_RATES.pdf',                                                          'pdf',          true),
    ('HDFC Bank',              'hdfc',        'https://v.hdfcbank.com/content/dam/hdfc-aem-microsites/singapore-site/rates/forex-card-rates.pdf',                        'pdf',          true),
    ('ICICI Bank',             'icici',       'https://instantforex.icicibank.com/instantforex/forms/MicroCardRateView.aspx',                                            'html_dynamic', true),
    ('Bank of Baroda',         'bob',         'https://www.bankofbaroda.in/business-banking/treasury/forex-card-rates',                                                  'html',         true),
    ('Canara Bank',            'canara',      'https://canarabank.com/pages/forex-card-rates',                                                                            'html',         true),
    ('Punjab National Bank',   'pnb',         'https://www.pnbindia.in/downloadprocess.aspx?fid=A+rrvZeJc+PIaxfEqVTIQQ%3D%3D',                                            'pdf',          true),
    ('Union Bank of India',    'union',       'https://www.unionbankofindia.bank.in/pdf/foreign-exchange-card-rates-applicable-to-various-forex-transactions.pdf',       'pdf',          true),
    ('Indian Overseas Bank',   'iob',         'https://www.iob.bank.in/en/forex-rates',                                                                                 'html',         true),
    ('IDFC FIRST Bank',        'idfc',        'https://www.idfcfirst.bank.in/forex-rates-teletransfer',                                                                 'html_dynamic', true),
    ('Kotak Mahindra Bank',    'kotak',       'https://www.kotak.bank.in/en/rates/forex-rates.html',                                                                    'html_dynamic', true)
on conflict (slug) do update set
    name        = excluded.name,
    source_url  = excluded.source_url,
    parser_type = excluded.parser_type;
