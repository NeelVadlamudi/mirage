# Massachusetts map pins

Public labels: `warehouse_1` … `warehouse_4`.

Coordinates = real publicly listed warehouse addresses in MA, used **only for map pins**.  
Demo inventory is synthetic. Demo is **not affiliated** with Costco, BJ’s, or Sam’s Club.

User-facing `map_label` / chip copy: **street address only** (plus “supply pin only” on warehouse_4). No retailer brand on chips or in public pin tables.

| Label | City | Street | Lat | Lon | Board role |
| --- | --- | --- | --- | --- | --- |
| warehouse_1 | Everett, MA | 2 Mystic View Rd | 42.402137 | -71.069774 | Club floor KPIs |
| warehouse_2 | Dedham, MA | 200 Legacy Blvd | 42.231627 | -71.176682 | Club floor KPIs |
| warehouse_3 | Waltham, MA | 71 Second Ave | 42.394360 | -71.265464 | Club floor KPIs |
| warehouse_4 | Avon, MA | 120 Stockwell Dr | 42.137378 | -71.066062 | **Supply pin only — no floor KPIs** |

### warehouse_4 treatment

- No gap rate / phantom / rescue tiles.
- Synthetic DC day metrics on check day 2026-09-22: **1840** outbound cases staged, **3** late ASNs.
- Chip / pin should read as supply context, not an unfinished club.
