# Mirage

An inventory exception board that turns an empty shelf into a specific next action.

[Live board](https://neelvadlamudi.github.io/mirage/) · [Audit walkthrough](https://neelvadlamudi.github.io/mirage/audit.html) · [Portfolio](https://neelvadlamudi.github.io/neelresume/)

## Result and scope

In the synthetic Everett snapshot for **September 22, 2026**, **9 of 40 assortment SKUs had no stock on the sales floor: 22.5%**. Of those gaps, **7** still had positive system on-hand and **6** had stock in the backroom. Those groups overlap; they are not parts to add together.

The point is the action, not just the rate. Positive book stock calls for a recount. Backroom stock calls for a floor pull. When neither has stock, replenishment is the next question.

These figures come from the published [`data/board_data.json`](https://neelvadlamudi.github.io/mirage/data/board_data.json), whose `as_of` is `2026-09-22`, checked November 9, 2026. **All inventory, sales, work orders and utility data are synthetic.** Everett, Dedham and Waltham are scenario labels; map pins mark town centers, not real stores. The project is not affiliated with a retailer.

## Allocation without pretending every case is needed

The sample delivery brings **98 cases** to the Avon distribution center. The allocation sends **60** to clubs and holds **38** at the DC because the modeled club need does not use them. Club-SKU positions below **one week of supply fall from 40 to 32** in the scenario.

Allocations use whole cases. The board also identifies transfers between clubs rather than treating every shortage as a purchase. This is a scenario result, not evidence of savings at a real business. Inspect the [published allocation payload](https://neelvadlamudi.github.io/mirage/data/allocation_board.json) and [allocation rules](docs/allocation.md).

## A reviewable audit assistant

The assistant reads a DuckDB copy of the scenario and explains shelf gaps, inventory positions and allocation decisions. It can propose an action, but it does not change inventory records. Proposals wait for a person's approval or rejection in a separate state database.

The number checker compares numerical claims with tool results. The [audit page](https://neelvadlamudi.github.io/mirage/audit.html) exposes recorded answers and decisions, rather than asking the reader to trust an uninspected chat response:

- [Evaluation record](https://neelvadlamudi.github.io/mirage/data/audit_eval.json)
- [Recorded tool-call replay](https://neelvadlamudi.github.io/mirage/data/audit_replay.json)
- [Proposal queue](https://neelvadlamudi.github.io/mirage/data/audit_proposals.json)
- [Decision log](https://neelvadlamudi.github.io/mirage/data/audit_audit.json)

The public service uses temporary storage, so proposal history can reset when it restarts. This is a demonstration of the review flow, not a durable production audit system.

## Maintenance is a separate analysis

The Avon maintenance work covers preventive-maintenance follow-up, failure concentration, fleet coverage and a volume-adjusted energy baseline. These use the same synthetic-data boundary. Associations after missed maintenance are not causal estimates of what maintenance would prevent.

Read the [methods and limits](docs/maintenance.md), [report](docs/maintenance_report.pdf) and [operator guide](docs/maintenance_user_guide.md) before using those outputs.

## Reproduce the checks

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/verify_kpis.py
python scripts/verify_allocation.py
python scripts/verify_maintenance.py
pytest -q tests
```

The KPI check recomputes the fixed Everett snapshot. The allocation check reconciles cases received, assigned and held. See [metric definitions](docs/metrics.md) and [INSTALL.md](INSTALL.md) for SQL setup; Tableau extracts are in `data/tableau/`.

To view the static board locally:

```bash
cd docs
python3 -m http.server 8080
```

Open `http://localhost:8080/`. The static board and recorded audit do not require a running model service. Live questions require the separately configured API in `agent/`.

## Screenshots

[Desktop](https://neelvadlamudi.github.io/mirage/screenshots/desktop_1440.png) · [Phone](https://neelvadlamudi.github.io/mirage/screenshots/phone_390.png)

Published links use the Pages root: `data/` and `screenshots/`. The repository's `docs/` prefix is not part of those site URLs.

## License

[MIT](LICENSE).
