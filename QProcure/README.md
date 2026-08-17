# QProcure Backend

FastAPI + Supabase backend covering all 6 modules from the wireframe.
Email channel only (Resend) — WhatsApp not wired up yet.

## Setup

```bash
pip install -r requirements.txt --break-system-packages
cp .env.example .env   # fill in real Supabase + Resend keys
```

Run schema.sql in your Supabase SQL editor (project: `ccxcqxjfhbqnnzepwerr`) to create all tables.

```bash
python main.py
# runs on http://localhost:8002
```

Interactive docs at `http://localhost:8002/docs`.

## Endpoints by module

**Module 1 — Vendor directory** (`/vendors`)
- `GET /vendors?category=&region=&rating=` — list/filter vendors
- `POST /vendors` — add vendor
- `GET /vendors/{id}` — get one
- `DELETE /vendors/{id}`

**Module 2 — RFQ creation** (`/rfq`)
- `POST /rfq` — create RFQ with line items
- `GET /rfq?status=` — list RFQs
- `GET /rfq/{id}` — get RFQ + lines
- `PUT /rfq/{id}/status` — update status

**Module 3 — Vendor selection & dispatch** (`/dispatch`)
- `POST /dispatch` — send RFQ email (via Resend) to selected vendors, schedules a reminder timestamp
- `GET /dispatch/{rfq_id}` — dispatch status per vendor

**Module 4 — Response dashboard** (`/responses`)
- `POST /responses` — log a vendor's reply manually (price/MOQ/lead time), fallback if auto-poll misses something
- `POST /responses/poll-inbox` — checks the RFQ inbox via IMAP for new vendor replies, matches by RFQ number (from subject) + sender email (vendor directory), auto-inserts into `rfq_responses`
- `GET /responses/{rfq_id}` — full dashboard: response count, best price, per-vendor rows sorted cheapest-first

### How auto-polling works (`services/imap_service.py`)
1. Connects to the `rfq@bharyat.com` inbox over IMAP, scans unread mail.
2. Looks for "RFQ 1042" / "RFQ-1042" pattern in subject or body → matches to the `rfqs` table.
3. Matches sender's email to the `vendors` table.
4. Runs basic regex extraction for price / MOQ / lead time. Marked `needs_verify` if price extraction fails (e.g. price is in an attached PDF/image, or unusual phrasing) — you'll see these flagged in the dashboard for manual review.
5. Inserts into `rfq_responses`.

**To automate the polling** (so you don't have to hit the endpoint manually):
- Simplest: a cron job that calls `POST /responses/poll-inbox` every few minutes (e.g. via `cron` + `curl`, or a free scheduler like [cron-job.org](https://cron-job.org)).
- Or run `python services/imap_service.py` directly on a schedule if hosting allows background scripts (e.g. Render cron jobs).

**Extraction is regex-based for now** — works for clean replies like "Price: ₹42.50, MOQ: 500, Lead time: 3 weeks" but will miss messier phrasing or PDF attachments. Swap `extract_fields()` for an LLM call later if reply formats vary a lot.

**Module 5 — Vendor scorecard** (`/scorecard`)
- `GET /scorecard/{vendor_id}` — score + quote history
- `POST /scorecard/{vendor_id}/recalculate` — recompute after a closed RFQ (currently only response_rate is calculated live; on-time delivery, price-vs-reference, and compliance stars are placeholders pending PO tracking + QLens integration)

**Module 6 — Award & PO conversion** (`/award`)
- `POST /award` — record award decision + requested documents, marks RFQ as awarded
- `PUT /award/{award_id}/send-po` — mark PO as sent
- `GET /award/{rfq_id}` — get award for an RFQ

## Known gaps (by design, for this pass)

1. **Inbound email**: Resend only sends. Vendor replies currently go into `/responses` via manual paste. To automate, add IMAP polling or an inbound webhook (Postmark/Cloudflare Email Workers) later.
2. **Extraction/parsing**: no AI parsing yet — `extraction_status` is just a stub based on whether `price` was provided. Can plug in an LLM-based parser on top of `raw_email_body` next.
3. **Vendor scorecard**: only response_rate is live; delivery reliability and price-vs-AD-reference need PO delivery data and QLens price history respectively.
4. **PO document generation**: not included here — reuse the existing `document_parser` pattern from bharyat.com for actually generating the PO PDF/Word file.
