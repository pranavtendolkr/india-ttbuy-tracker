# india-ttbuy-tracker

A small public dashboard that tracks historical **inward remittance TT-buy
rates** from major Indian banks. The TT-buy rate is what banks apply when USD
is wired in (e.g. from a US brokerage or bank account) and converted to INR on
credit, so it directly affects how many rupees you receive.

- **Frontend**: Next.js (static export) on **Cloudflare Pages**, reading
  directly from Supabase with the public anon key.
- **Database**: **Supabase Postgres** (free tier).
- **Scraping/parsing**: Python parsers (one per bank) run by a daily
  **GitHub Actions** scheduled workflow.
- **Hosting**: free tiers everywhere; no separate backend server.

USD only for v1. The schema records `currency` and `rate_type` per row so
extending to other currencies later is a metadata change, not a migration.

---

## Repo layout

```
.
├── frontend/                  Next.js 14 (static export) dashboard
│   ├── src/app/               Routes
│   ├── src/components/        Chart, table, controls
│   └── src/lib/               Supabase client, queries, helpers
├── ingestion/                 Python ingestion package
│   ├── parsers/               One module per bank
│   ├── common/                http / pdf / normalize / supabase helpers
│   ├── tests/                 pytest + fixtures (no network)
│   └── run.py                 Daily orchestrator
├── supabase/migrations/       SQL schema + seed
└── .github/workflows/         daily ingest + PR tests
```

---

## 1. Set up Supabase

1. Create a new project at <https://supabase.com> (free tier is enough).
2. In the SQL Editor, run [`supabase/migrations/0001_init.sql`](supabase/migrations/0001_init.sql).
   This creates the `banks` and `rates` tables, the unique constraint, the
   `latest_rates` view, public-read RLS policies, and seeds the bank metadata.
3. From **Project Settings → API**, copy:
   - `Project URL` → use as `SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_URL`
   - `anon public` key → use as `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `service_role` key → use as `SUPABASE_SERVICE_ROLE_KEY`
     (only used by the GitHub Action; never ship to the browser).

To re-seed banks later, just re-run the migration; the `INSERT ... ON CONFLICT
(slug) DO UPDATE` keeps it idempotent.

---

## 2. Set up GitHub Actions

In the repo settings, add the following **Repository secrets**:

| Name                         | Value                          |
| ---------------------------- | ------------------------------ |
| `SUPABASE_URL`               | your project URL               |
| `SUPABASE_SERVICE_ROLE_KEY`  | service-role key from Supabase |

Two workflows are included:

- [`.github/workflows/ingest.yml`](.github/workflows/ingest.yml) runs daily at
  **18:00 IST** (`30 12 * * *` UTC) and on `workflow_dispatch`. It loads
  enabled banks from Supabase, runs each parser in isolation, and upserts
  rates. A failed bank does not fail the whole run unless every bank fails.
- [`.github/workflows/test.yml`](.github/workflows/test.yml) runs `pytest`
  on PRs that touch `ingestion/`.

Trigger an initial ingestion manually from the **Actions** tab → *Daily
ingestion* → *Run workflow* to seed historical data.

### Debug mode

Run the workflow with `debug = true` to write the raw fetched payloads of any
parser that fails or returns no data into `ingestion/_debug/`, which is then
uploaded as a workflow artifact (retained 7 days). This is the easiest way to
diagnose a broken parser without re-running locally.

---

## 3. Run the frontend locally

```bash
cd frontend
cp .env.example .env.local   # fill in NEXT_PUBLIC_* values
npm install
npm run dev
```

Open <http://localhost:3000>. The dashboard fetches directly from Supabase
using the anon key, so make sure the migration has been run and at least one
ingestion has populated `rates`.

To produce the static export for Cloudflare Pages:

```bash
npm run build
# Output: frontend/out
```

---

## 4. Deploy to Cloudflare Pages

1. In Cloudflare → **Workers & Pages** → *Create application* → *Pages* →
   *Connect to Git*. Pick this repo.
2. Build settings:
   - **Framework preset**: Next.js (Static HTML Export)
   - **Build command**: `npm run build`
   - **Build output directory**: `out`
   - **Root directory**: `frontend`
   - **Node version**: 20 (set under *Settings → Environment variables*
     after the first deploy if the auto-detected version is older).
3. **Environment variables** (Production *and* Preview):
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
4. Trigger the first deployment. Subsequent pushes to `main` redeploy
   automatically.

### Custom domain

In the Pages project → **Custom domains** → *Set up a custom domain*. If your
DNS is already on Cloudflare, the CNAME is created automatically. Otherwise,
add the CNAME record Cloudflare suggests at your DNS provider. Allow a few
minutes for the certificate to issue.

---

## 5. Run the ingestion locally

You don't need to run ingestion locally — GitHub Actions handles it daily —
but for parser development:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r ingestion/requirements.txt

export SUPABASE_URL=...
export SUPABASE_SERVICE_ROLE_KEY=...
python -m ingestion.run
```

Run only the tests (no network, no Supabase needed):

```bash
pytest -q ingestion/tests
```

---

## Adding a new bank

1. Add a row to the seed `INSERT` in `supabase/migrations/0001_init.sql`
   (or insert directly in Supabase) with a unique `slug`.
2. Create `ingestion/parsers/<slug>.py` subclassing
   [`BankParser`](ingestion/parsers/base.py). Set `BANK_SLUG`, `SOURCE_URL`,
   and bump `PARSER_VERSION` whenever the parsing logic changes.
3. Register the class in [`ingestion/parsers/__init__.py`](ingestion/parsers/__init__.py).
4. Add a test fixture under `ingestion/tests/fixtures/<slug>/` and a
   `test_<slug>.py`.
5. Open a PR — the test workflow will run automatically.

The frontend has no per-bank code; it picks up new enabled banks
automatically from the `banks` table.

---

## Adding a new currency

The schema already stores `currency` per row. To extend beyond USD:

1. Update `CURRENCY_ALIASES` in
   [`ingestion/common/normalize.py`](ingestion/common/normalize.py) with the
   spellings each bank uses.
2. Update each parser to emit additional `ParsedRate` rows for that
   currency (most existing parsers stop at the first USD row; relax that
   loop).
3. Add the currency to the `<select>` in
   [`frontend/src/components/Controls.tsx`](frontend/src/components/Controls.tsx).

---

## Data semantics & caveats

- A row is only emitted when the source explicitly labels the column as
  inward remittance / TT buying. Forex card / cash / travel-card rates are
  excluded.
- `effective_date` is parsed from the document header where possible. If we
  cannot find one, we record today's IST date and set
  `source_status = 'date_inferred'` so it can be filtered later.
- The unique constraint `(bank_id, currency, rate_type, effective_date)`
  makes ingestion idempotent: re-running on the same day overwrites the row
  rather than duplicating it.
- Missing days for a bank are not back-filled — they show up as gaps in the
  chart.
- This site is informational only. Always confirm the rate with your bank
  before initiating a transfer.

## Useful commands

```bash
# Run all parsers against live sources without writing to Supabase.
# Saves raw payloads under ingestion/_debug/ for inspection.
python -m ingestion.tools.dryrun

# Just one or two parsers
python -m ingestion.tools.dryrun sbi iob
```
