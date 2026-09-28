/* Mirage frost glance board — loads board_data + allocation_board */
(() => {
  const PLATES = {
    warehouse_1: { src: "./plates/bay.jpg", alt: "Everett, Massachusetts" },
    warehouse_2: { src: "./plates/harbor.jpg", alt: "Dedham, Massachusetts" },
    warehouse_3: { src: "./plates/west.jpg", alt: "Waltham, Massachusetts" },
    warehouse_4: { src: "./plates/avon.jpg", alt: "Avon, Massachusetts" },
  };
  const WH_LABEL = {
    warehouse_1: "Everett",
    warehouse_2: "Dedham",
    warehouse_3: "Waltham",
    warehouse_4: "Avon",
  };
  const SUPPLY = {
    id: "warehouse_4",
    city: "Avon, MA",
    cases_staged: 1840,
    late_truck_notices: 3,
    day_note: "synthetic DC day",
    badge: "Supply only · no floor counts",
  };
  const WH_META = {
    warehouse_1: { city: "Everett, MA", kind: "Floor" },
    warehouse_2: { city: "Dedham, MA", kind: "Floor" },
    warehouse_3: { city: "Waltham, MA", kind: "Floor" },
    warehouse_4: { city: "Avon, MA", kind: "Supply" },
  };
  const FLOOR_IDS = ["warehouse_1", "warehouse_2", "warehouse_3"];

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

  const state = {
    clubId: "warehouse_1",
    board: null,
    alloc: null,
    tipsOn: false,
    tipDismissed: false,
    selectedSku: null,
  };

  function pct(n) {
    const v = Math.round(n * 1000) / 10;
    return Number.isInteger(v) ? String(v) : v.toFixed(1);
  }
  function int(n) {
    return String(Math.round(Number(n) || 0));
  }

  function setPlate(id) {
    const plate = PLATES[id] || PLATES.warehouse_1;
    const img = $("[data-plate-img]");
    const cap = $("[data-plate-cap]");
    if (img) {
      img.src = plate.src;
      img.alt = plate.alt;
    }
    if (cap) cap.textContent = WH_LABEL[id] || id;
  }

  function renderSwitcher() {
    $$("[data-wh]").forEach((btn) => {
      const id = btn.getAttribute("data-wh");
      const on = id === state.clubId;
      btn.setAttribute("aria-pressed", on ? "true" : "false");
    });
  }

  function sparkPath(values) {
    if (!values || !values.length) return "";
    const w = 240, h = 48, pad = 2;
    const max = Math.max(...values, 0.01);
    const step = w / Math.max(values.length - 1, 1);
    return values
      .map((v, i) => {
        const x = i * step;
        const y = h - pad - (v / max) * (h - pad * 2);
        return `${i === 0 ? "M" : "L"}${x.toFixed(1)} ${y.toFixed(1)}`;
      })
      .join(" ");
  }

  function renderFloor(club) {
    const kpi = club.kpi;
    const over = kpi.gap_rate > kpi.gap_ceiling;
    const gapEl = $("[data-kpi-gap]");
    if (gapEl) gapEl.classList.toggle("is-hot", !!over);

    const setText = (sel, val) => { const el = $(sel); if (el) el.textContent = val; };
    const gapRateEl = $("[data-gap-rate]");
    if (gapRateEl) gapRateEl.innerHTML = formatNumHtml(pct(kpi.gap_rate));
    const gapFoot = $("[data-gap-foot]");
    if (gapFoot) {
      gapFoot.innerHTML =
        `<span class="mini-num">${int(kpi.gap_sku_count)}</span> of ` +
        `<span class="mini-num">${int(kpi.assortment_sku_count)}</span> · ceiling ` +
        `<span class="mini-num">${pct(kpi.gap_ceiling)}</span>%`;
    }
    setText("[data-phantom]", int(kpi.phantom_sku_count));
    setText("[data-rescue]", int(kpi.backroom_rescue_sku_count));

    const rows0 = club.exceptions || [];
    let pull = club.shelf_pull;
    if (state.selectedSku) {
      const picked = rows0.find((r) => String(r.sku_id) === String(state.selectedSku));
      if (picked) {
        pull = {
          sku_id: picked.sku_id,
          sku_name: picked.sku_name,
          backroom_qty: picked.backroom_qty,
          system_on_hand_qty: picked.system_on_hand_qty,
        };
      }
    }
    setText("[data-pull-sku]", String(pull.sku_id));
    setText("[data-pull-name]", pull.sku_name);
    setText("[data-pull-qty]", int(pull.backroom_qty));
    setText("[data-pull-book]", int(pull.system_on_hand_qty));
    const share =
      pull.system_on_hand_qty > 0
        ? Math.min(100, (pull.backroom_qty / pull.system_on_hand_qty) * 100)
        : pull.backroom_qty > 0
          ? 100
          : 0;
    const fill = $("[data-pull-fill]");
    if (fill) fill.style.width = `${share}%`;

    const spark = $("[data-spark]");
    if (spark) {
      const d = sparkPath(club.spark);
      spark.setAttribute("d", d);
      const last = club.spark[club.spark.length - 1] || 0;
      const max = Math.max(...club.spark, 0.01);
      const cy = 48 - 2 - (last / max) * 44;
      const mark = $("[data-spark-mark]");
      if (mark) {
        mark.setAttribute("cx", "240");
        mark.setAttribute("cy", cy.toFixed(2));
      }
    }

    // Aisles
    const gaps = club.gaps_by_category || [];
    const maxGap = Math.max(...gaps.map((g) => g.gap_sku_count), 1);
    const aisles = $("[data-aisles]");
    aisles.innerHTML = gaps
      .map((g) => {
        const hot = g.gap_sku_count === maxGap && maxGap > 1;
        const w = (g.gap_sku_count / maxGap) * 100;
        return `<div class="aisle">
          <span class="aisle-name">${escapeHtml(g.category)}</span>
          <span class="aisle-n${hot ? " is-hot" : ""}">${int(g.gap_sku_count)}</span>
          <span class="aisle-track"><span class="aisle-fill${hot ? " is-hot" : ""}" style="width:${w}%"></span></span>
        </div>`;
      })
      .join("");

    // Work table — all open rows, no inner scroll
    const rows = club.exceptions || [];
    $("[data-open-count]").textContent = int(rows.length);
    if (!state.selectedSku && rows[0]) state.selectedSku = String(rows[0].sku_id);
    const body = $("[data-work-body]");
    body.innerHTML = rows
      .map((e) => {
        const id = String(e.sku_id);
        const on = id === state.selectedSku;
        const dots = [];
        if (e.is_phantom) dots.push('<span class="dot dot-red" aria-hidden="true"></span>');
        if (e.is_backroom_rescue) dots.push('<span class="dot dot-green" aria-hidden="true"></span>');
        if (e.exception_type === "true_out" && !dots.length) {
          dots.push('<span class="dot" style="background:var(--text-faint)" aria-hidden="true"></span>');
        }
        return `<button type="button" class="work-row${on ? " is-on" : ""}" data-sku="${id}" role="row" aria-pressed="${on}">
          <span class="sku-main" role="cell">
            <span class="sku-dots">${dots.join("")}</span>
            <span class="sku-name">${escapeHtml(e.sku_name)}</span>
            <span class="sku-num">${id}</span>
          </span>
          <span class="sku-aisle" role="cell"><span class="field-k">Aisle</span>${escapeHtml(e.category)}</span>
          <span class="qty${e.system_on_hand_qty === 0 ? " is-zero" : ""}" role="cell"><span class="field-k">Book</span>${int(e.system_on_hand_qty)}</span>
          <span class="qty${e.backroom_qty === 0 ? " is-zero" : ""}" role="cell"><span class="field-k">Backroom</span>${int(e.backroom_qty)}</span>
          <span class="action-cell" role="cell"><span class="field-k">Action</span>${escapeHtml(e.action_label)}</span>
        </button>`;
      })
      .join("");

    body.querySelectorAll("[data-sku]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.selectedSku = btn.getAttribute("data-sku");
        const ex = rows.find((r) => String(r.sku_id) === state.selectedSku);
        if (ex) {
          $("[data-pull-sku]").textContent = String(ex.sku_id);
          $("[data-pull-name]").textContent = ex.sku_name;
          $("[data-pull-qty]").textContent = int(ex.backroom_qty);
          $("[data-pull-book]").textContent = int(ex.system_on_hand_qty);
          const sh =
            ex.system_on_hand_qty > 0
              ? Math.min(100, (ex.backroom_qty / Math.max(ex.system_on_hand_qty, 1)) * 100)
              : ex.backroom_qty > 0
                ? 100
                : 0;
          $("[data-pull-fill]").style.width = `${sh}%`;
        }
        renderFloor(club);
      });
    });

    const live = $("[data-live]");
    if (live) {
      live.textContent =
        `${club.chip_label || WH_LABEL[state.clubId] || club.store_name}, empty shelves ${pct(kpi.gap_rate)}%, ` +
        `${int(kpi.gap_sku_count)} of ${int(kpi.assortment_sku_count)}, ` +
        `book-is-wrong ${int(kpi.phantom_sku_count)}, ` +
        `stuck-in-backroom ${int(kpi.backroom_rescue_sku_count)}, ` +
        `${int(kpi.open_exceptions)} open exceptions.`;
    }
  }

  function renderSupply() {
    $("[data-supply-cases]").textContent = int(SUPPLY.cases_staged);
    $("[data-supply-late]").textContent = int(SUPPLY.late_truck_notices);
    const live = $("[data-live]");
    if (live) {
      live.textContent =
        "Avon, supply only, no floor counts. " +
        `${SUPPLY.cases_staged} cases staged · ${SUPPLY.late_truck_notices} late truck notices.`;
    }
  }

  function renderAlloc() {
    const a = state.alloc;
    if (!a) return;
    $("[data-truck-sub]").textContent = a.po_summary.plain;
    $("[data-truck-po]").textContent = a.po_summary.po_id;
    const tiles = $("[data-truck-tiles]");
    tiles.innerHTML = (a.po_summary.tiles || [])
      .map((t) => {
        // Apply on-board rename: Clubs short on stock → Clubs short
        const text = String(t).replace(/^Clubs short on stock/, "Clubs short");
        return `<div class="truck-tile"><span>${escapeHtml(text)}</span></div>`;
      })
      .join("");

    const rows = $("[data-alloc-rows]");
    rows.innerHTML = (a.po_rows || [])
      .map(
        (r) => `<div class="alloc-row" role="row">
        <span class="alloc-sku">${escapeHtml(r.sku_name)}</span>
        <span>${int(r.warehouse_1)}</span>
        <span>${int(r.warehouse_2)}</span>
        <span>${int(r.warehouse_3)}</span>
        <span class="${r.held_at_dc > 0 ? "is-hold" : ""}">${int(r.held_at_dc)}</span>
      </div>`
      )
      .join("");

    const xfer = (a.transfers || [])[0];
    const xferBox = $("[data-xfer]");
    if (xfer && xferBox) {
      xferBox.innerHTML = `
        <h3 class="xfer-title">Move between clubs</h3>
        <div class="xfer-row">
          <span>${escapeHtml(xfer.sku_name)}</span>
          <span class="xfer-route">${escapeHtml(xfer.from)} → ${escapeHtml(xfer.to)} · ${int(xfer.cases)} cases</span>
          <span class="xfer-action">${escapeHtml(xfer.action)}</span>
        </div>
        <p class="xfer-ba">${escapeHtml(
          String(a.before_after.plain).replace(/^Clubs short on stock/, "Clubs short")
        )}</p>`;
    }
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function formatNumHtml(s) {
    const str = String(s);
    const i = str.indexOf(".");
    if (i < 0) return escapeHtml(str);
    return (
      escapeHtml(str.slice(0, i)) +
      '<span class="num-dot">.</span>' +
      escapeHtml(str.slice(i + 1))
    );
  }

  function showTip() {
    const tip = $("[data-tip]");
    if (!tip) return;
    const on = state.tipsOn && !state.tipDismissed;
    tip.classList.toggle("is-on", on);
    if (!on) return;
    const isSupply = state.clubId === "warehouse_4";
    const body = $("[data-tip-body]");
    if (isSupply) {
      body.textContent =
        "Avon is supply only — no floor counts. Truck plan below is DC-wide and does not change with the club switcher.";
    } else {
      body.textContent =
        "Work the table top to bottom. Pull first clears empty shelves fastest. Today's truck plan is DC-wide — not filtered by this club.";
    }
  }

  function selectWarehouse(id) {
    state.clubId = id;
    state.selectedSku = null;
    state.tipDismissed = false;
    const isSupply = id === "warehouse_4";
    const app = document.querySelector(".app");
    if (app) app.classList.toggle("is-supply", isSupply);
    setPlate(id);
    renderSwitcher();
    if (!state.board) {
      const live = $("[data-live]");
      if (live) live.textContent = "Loading board data…";
      return;
    }
    if (isSupply) {
      renderSupply();
    } else {
      const club = state.board.clubs[id];
      if (club) renderFloor(club);
    }
    showTip();
  }

  function bind() {
    if (state._bound) return;
    state._bound = true;
    $$("[data-wh]").forEach((btn) => {
      btn.addEventListener("click", () => selectWarehouse(btn.getAttribute("data-wh")));
    });
    const tipsBtn = $("[data-tips-toggle]");
    if (tipsBtn) {
      tipsBtn.addEventListener("click", () => {
        state.tipsOn = !state.tipsOn;
        state.tipDismissed = false;
        tipsBtn.setAttribute("aria-pressed", state.tipsOn ? "true" : "false");
        tipsBtn.textContent = state.tipsOn ? "Tips on" : "Tips off";
        showTip();
      });
    }
    const dismiss = $("[data-tip-dismiss]");
    if (dismiss) {
      dismiss.addEventListener("click", () => {
        state.tipDismissed = true;
        showTip();
      });
    }
  }

  async function load() {
    bind(); // wire clicks even if JSON is still loading or fails
    try {
    const [board, alloc] = await Promise.all([
      fetch("./data/board_data.json").then((r) => {
        if (!r.ok) throw new Error("board_data " + r.status);
        return r.json();
      }),
      fetch("./data/allocation_board.json").then((r) => {
        if (!r.ok) throw new Error("allocation_board " + r.status);
        return r.json();
      }),
    ]);
    state.board = board;
    state.alloc = alloc;

    const asOf = $("[data-as-of]");
    if (asOf) {
      asOf.setAttribute("datetime", `${board.as_of}T06:00:00`);
      asOf.textContent = `Snapshot · ${board.as_of} 06:00`;
    }

    // Fill switcher city meta from pins / board
    (board.pins || []).forEach((p) => {
      const meta = $(`[data-wh-meta="${p.store_name}"]`);
      if (meta) {
        const kind = p.format_type === "crossdock" ? "Supply" : "Floor";
        meta.textContent = `${kind} · ${p.city}`;
      }
    });

    renderAlloc();
    const whParam = new URLSearchParams(location.search).get("wh");
    if (whParam && (FLOOR_IDS.includes(whParam) || whParam === "warehouse_4")) {
      state.clubId = whParam;
    }
    selectWarehouse(state.clubId);
    } catch (err) {
      console.error(err);
      const live = $("[data-live]");
      if (live) live.textContent = "Board load error: " + err.message;
      // Keep buttons clickable; selectWarehouse no-ops until data is present
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", load);
  } else {
    load();
  }
})();
