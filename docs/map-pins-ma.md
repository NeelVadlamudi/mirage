# Massachusetts map pins

Synthetic data for this project. Pins mark town centers, not stores. Not affiliated with any retailer.

The four pins are the town centers of Everett, Dedham, Waltham, and Avon, Massachusetts. We picked town centers so the map shows real geography without pointing at any company's building. Each point is in the town's central area, rounded to 4 decimals.

Board chips and map labels show the town short names. Under the hood the synthetic ids stay `warehouse_1` … `warehouse_4` so extracts and verify scripts keep working.

| Label | Town | Lat | Lon | Board role | Synthetic id |
| --- | --- | --- | --- | --- | --- |
| Everett | Everett, MA | 42.4084 | -71.0537 | Club floor KPIs | warehouse_1 |
| Dedham | Dedham, MA | 42.2418 | -71.1662 | Club floor KPIs | warehouse_2 |
| Waltham | Waltham, MA | 42.3765 | -71.2356 | Club floor KPIs | warehouse_3 |
| Avon | Avon, MA | 42.1306 | -71.0412 | **Supply only · no floor counts** | warehouse_4 |

### Avon treatment

- No gap rate / phantom / rescue tiles.
- Synthetic DC day metrics on check day 2026-09-22: **1840** outbound cases staged, **3** late ASNs.
- Chip / pin should read as supply context, not an unfinished club.
