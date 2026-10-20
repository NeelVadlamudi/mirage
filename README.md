# Mirage

**Live board:** [https://neelvadlamudi.github.io/mirage/](https://neelvadlamudi.github.io/mirage/)

Empty shelf. Full backroom. System still shows stock.

Mirage is a distribution and club inventory project. Pick a club and a day. See which shelves are empty, why, and what to do next. When a purchase order lands at the DC, see how many whole cases go to each club and whether one club should send stock to another. At the DC, track preventive maintenance cost, fleet coverage for peak weeks, and whether a lighting retrofit actually cut energy use after shipping volume is accounted for.

## Data note

All inventory, sales, work orders, and utility figures in this repository are synthetic. Map pins mark town centers, not stores. Not affiliated with any retailer. Clubs are Everett, Dedham, and Waltham. The DC is Avon. (Synthetic ids stay `warehouse_1`…`warehouse_4` in extracts.)

## Gap board

| Tile | Meaning | Next step |
| --- | --- | --- |
| **Empty shelves** | Share of assortment with nothing on the floor | Open the exception list |
| **Book is wrong** | Floor empty; system still shows on-hand | Recount / correct the book |
| **Stuck in backroom** | Floor empty; backroom has stock | Pull to the floor |
| **Actually out** | Floor empty; backroom empty; book is zero | Replenish / order |

Locked check day (**Everett**, 2026-09-22):

- Empty shelves: **22.5%** (9 of 40)
- Book is wrong: **7**
- Stuck in backroom: **6**

```bash
python3 scripts/verify_kpis.py
```

Expected: `ALL PASS — warehouse_1 @ 2026-09-22: 22.5% / 7 / 6`

Detail: [`docs/metrics.md`](docs/metrics.md).

## Allocation

PO-26092201 arrives at Avon with **98** cases (12 SKUs).

- **60** cases allocated to clubs (whole cases, by need)
- **38** held at the DC (no club need)
- **1** club-to-club transfer: Sticky Notes Value, 5 cases, Everett → Dedham
- Club-SKUs under 1 week of supply: **40 → 32**

Rules and decisions: [`docs/allocation.md`](docs/allocation.md).

```bash
python3 scripts/verify_allocation.py
```

Expected last line: `ALL PASS - PO 98 cases: 60 allocated, 38 held at DC; 1 transfer(s); club-SKUs under 1 week of supply 40 -> 32`

## Audit agent

An audit agent answers questions such as "Why is Paper Towels 12pk empty at Everett on 2026-09-22?" It compares the floor count, the backroom count and the system on-hand figure, names the case (the record is wrong, stock is in the backroom, or truly out), and proposes the next step: recount, pull to the floor, or reorder.

It never changes a record. A proposal waits in a queue until a person approves or rejects it, and each decision goes to an audit log with who decided and when.

Its 30-question eval recomputes every expected value from these CSVs, using the logic of `verify_kpis.py` and `verify_allocation.py`. It stops unless the check day still gives 22.5% / 7 / 6.

Eval scores, recorded answers, the review queue and one recorded audit: [audit page](https://neelvadlamudi.github.io/mirage/audit.html) (`docs/audit.html`, data in `docs/data/audit_*.json`).

- **Code** (`agent/`): a small agent loop and number checker (`loop.py`, `checker.py`), the tools (`tools.py`), the proposals and audit log (`state.py`), and the API (`api.py`, `routes.py`). It runs on Gemini Flash-Lite by default, or on Ollama with `AGENT_MODEL=ollama-local`.
- **Read-only tools:** `list_shelf_gaps(club, day)`, `get_sku_position(club, sku, day)`, `get_po_allocation(po)` and `get_weeks_of_supply(club, sku)`. They query a DuckDB copy of `data/` that is opened read-only (`agent/build_db.py`).
- **One write tool**, `propose_action(club, sku, action, reason)`. It only adds a row with status `waiting for approval` to a `proposals` table in a separate database (`MIRAGE_STATE_DB`). It writes nothing unless the action matches the case the read tools found for that club and SKU earlier in the run, and every number in the reason appears in those tool results.
- **Approval:** `POST /api/proposals/{id}/approve` and `/reject` need `X-API-Key: <ADMIN_API_KEY>` and the deciding person's name. A decision is final; a second one returns 409.
- **Limits:** `POST /api/mirage/ask` allows 4 a minute and 30 a day per address, 300 a day in total; proposals 3 a minute and 10 a day per address, 50 a day in total. Over the limit returns 429 with `Retry-After`. `RATE_LIMITS_ENABLED=false` turns them off for eval runs.
- **Eval** (`evals/`): 30 questions. CI runs both checks, the tests, and rescores the recorded run. The `audit eval` workflow runs it live on Gemini (needs the `GEMINI_API_KEY` repository secret).
- **Hosting:** `render.yaml` is a Render Blueprint for the API on the free plan (`GEMINI_API_KEY` is set in Render; `ADMIN_API_KEY` is generated). Proposals live in `/tmp` there, so they reset when the service restarts or sleeps. `/docs` is off in production.

```bash
pip install -r requirements.txt
pytest -q tests
uvicorn agent.api:app --port 8000                                        # the API
RATE_LIMITS_ENABLED=false python evals/run_evals.py --model gemini-3.5-flash-lite   # live, 30 questions
python evals/run_evals.py --model ollama --setting ollama-local
python scripts/record_audit.py   # one full audit: question, tool calls, proposal, approval, audit log
```

## Maintenance (Avon)

60 material-handling assets. 1,009 synthetic work orders with problem, cause, and remedy codes.

| Question | Result |
| --- | --- |
| Missed or late PM follow-up | Breakdown within 30 days **50.0%** vs **25.8%** after on-time PM. About **33** extra breakdowns and **$35.8K** / year. |
| Failure concentration | Reach trucks 6+ years old: **4.6x** battery failures per truck vs newer units (3 newer trucks in sample). |
| Peak fleet coverage | December need **20** order pickers vs fleet **18**. Short in **5** of the next 13 weeks. |
| LED retrofit | **15.1%** below volume-adjusted energy baseline. Payback **17.5** months. |

Methods and limits: [`docs/maintenance.md`](docs/maintenance.md).  
One-page report: [`docs/maintenance_report.pdf`](docs/maintenance_report.pdf).  
Operator guide: [`docs/maintenance_user_guide.md`](docs/maintenance_user_guide.md).

```bash
python3 scripts/verify_maintenance.py
```

## Open the board

https://neelvadlamudi.github.io/mirage/

Local:

```bash
cd docs && python3 -m http.server 8080
```

Then open http://localhost:8080/

## SQL and Tableau

Install: [`INSTALL.md`](INSTALL.md).  
Tableau extracts: `data/tableau/`. Build notes: [`docs/tableau-build.md`](docs/tableau-build.md).

## Screenshots

| View | File |
| --- | --- |
| Desktop | [`docs/screenshots/desktop_1440.png`](docs/screenshots/desktop_1440.png) |
| Phone | [`docs/screenshots/phone_390.png`](docs/screenshots/phone_390.png) |

## License

MIT. Copyright (c) 2026 Neel Vittal Bharath Vadlamudi. See [`LICENSE`](LICENSE).
