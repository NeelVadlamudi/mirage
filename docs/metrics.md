# Mirage — glance metrics

Audience: ops analyst / hiring manager. One screen. Numbers you can say out loud.

**Sample scale:** 3 clubs + 1 DC, 40 SKUs, check window 2026-09-09 → 2026-09-22 (14 days).  
Grain for floor metrics: **store × SKU × snapshot_date**.

Inventory is **synthetic**. Map pins use real publicly listed warehouse addresses for realism only. This demo is **not affiliated** with Costco, BJ’s, or Sam’s Club.

---

## 1. Gap rate

**Plain English:** Share of stocked SKUs that have nothing on the sales floor today.

**Formula:**  
`gap_rate = count(floor_qty = 0 AND is_in_assortment = 1) / count(is_in_assortment = 1)`

**Talk track:** “X% of our assortment is empty on the floor right now.”

**Dashboard cue:** Big % + spark of last 14 days. Flag when above the 15% gap ceiling.

**Next step:** Open the exception queue — each gap row carries an action label.

---

## 2. Phantom SKUs

**Plain English:** System still shows inventory, but the floor is empty. Book says yes. Shelf says no.

**Formula (flag):**  
`is_phantom = 1 when floor_qty = 0 AND system_on_hand_qty > 0`

**Store rollup:**  
`phantom_sku_count = count(distinct sku where is_phantom = 1)`

**Talk track:** “We have N SKUs the system thinks we own that shoppers cannot buy off the floor.”

**Action label:** `Recount / system fix`

**Dashboard cue:** Integer count + top offenders (SKU, category, book qty stuck).

---

## 3. Backroom rescue

**Plain English:** Floor empty, backroom stocked. Labor / replenishment miss, not a buy miss.

**Formulas:**  
- `floor_share = floor_qty / nullif(floor_qty + backroom_qty, 0)`  
- `backroom_share = 1 - floor_share`  
- **Rescue row:** `floor_qty = 0 AND backroom_qty > 0`

**Talk track:** “Y SKUs are dead on the floor with stock sitting in the backroom.”

**Action label:** `Floor pull from backroom`  
If also phantom: `Floor pull · recount`

**Dashboard cue:** Rescue count tile + shelf-pull panel for the selected rescue SKU.

---

## 4. Pure gap (no backroom, no book)

**Plain English:** Floor empty, nothing in backroom, system on-hand is zero. Need product, not a recount theater.

**Flag:** `is_shelf_gap = 1 AND is_phantom = 0 AND is_backroom_rescue = 0`

**Action label:** `Replenish / order`

---

## How the pieces fit

| Metric | Question | Implied action |
| --- | --- | --- |
| Gap rate | How bad is empty-shelf today? | Open the queue |
| Phantom SKUs | How much emptiness is a system lie? | Recount / system fix |
| Backroom rescue | Is stock just not on the floor? | Floor pull from backroom |
| Pure gap | Are we actually out? | Replenish / order |

---

## Map pins (glance context)

| Pin | City | Approx coords | Role |
| --- | --- | --- | --- |
| warehouse_1 | Everett, MA | 42.402137, -71.069774 | Club — floor KPIs |
| warehouse_2 | Dedham, MA | 42.231627, -71.176682 | Club — floor KPIs |
| warehouse_3 | Waltham, MA | 42.394360, -71.265464 | Club — floor KPIs |
| warehouse_4 | Avon, MA | 42.137378, -71.066062 | **Supply pin only — no floor KPIs** |

Chips / pins filter clubs by `store_id`. warehouse_4 does not run gap / phantom / rescue tiles.

### warehouse_4 DC day metrics (synthetic, check day 2026-09-22)

| Field | Value | Notes |
| --- | --- | --- |
| `outbound_cases_staged` | 1840 | Synthetic cases staged outbound that day |
| `late_asn_count` | 3 | Synthetic late ASN count that day |

These are **not** floor KPIs. Documented in `docs/board_data.json` → `dc`.

---

## Locked check — warehouse_1 · 2026-09-22

Gap **22.5%** (9 of 40) · Phantom **7** · Rescue **6**.
