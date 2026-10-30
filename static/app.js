"use strict";

(() => {
  const form = document.getElementById("plan-form");
  const submitButton = document.getElementById("submit-button");
  const statusEl = document.getElementById("status");
  const resultsEl = document.getElementById("results");
  const dateInput = document.getElementById("event_date");
  const guestInput = document.getElementById("guest_count");
  const budgetInput = document.getElementById("budget");
  const currencyInput = document.getElementById("currency");
  const perGuestPreview = document.getElementById("per-guest-preview");

  // Blues from the editorial anchor to pale tints, with two warm neutrals for contrast.
  const PALETTE = ["#226192", "#3A7AB0", "#5B92C2", "#84B0D4", "#B3CDE3", "#B9A886", "#8E7D62", "#5E5140"];

  // ── Date minimum ──────────────────────────────────────────────────────
  dateInput.min = new Date().toLocaleDateString("en-CA");

  // ── Helpers ───────────────────────────────────────────────────────────
  // All server data is inserted with textContent, never innerHTML, to prevent XSS.
  function el(tag, text, attrs = {}) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
    return node;
  }

  const titleCase = (text) => text.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());

  function money(amount, currency) {
    try {
      return new Intl.NumberFormat(undefined, { style: "currency", currency }).format(amount);
    } catch {
      return `${amount.toFixed(2)} ${currency}`;
    }
  }

  function daysUntil(isoDate) {
    const [year, month, day] = isoDate.split("-").map(Number);
    const event = new Date(year, month - 1, day);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return Math.round((event - today) / 86400000);
  }

  // ── Segmented Controls ────────────────────────────────────────────────
  // Sync segmented radio buttons → hidden <select> for form submission.
  function setupSegmentedControl(radioName, selectId) {
    const radios = document.querySelectorAll(`input[name="${radioName}"]`);
    const hiddenSelect = document.getElementById(selectId);
    radios.forEach((radio) => {
      radio.addEventListener("change", () => {
        if (radio.checked) hiddenSelect.value = radio.value;
      });
    });
  }
  setupSegmentedControl("event_type_seg", "event_type");
  setupSegmentedControl("venue_seg", "venue");

  // ── Guest Stepper ─────────────────────────────────────────────────────
  document.getElementById("guest-minus").addEventListener("click", () => {
    const val = parseInt(guestInput.value, 10) || 0;
    if (val > 1) guestInput.value = val - 1;
    updatePerGuest();
  });
  document.getElementById("guest-plus").addEventListener("click", () => {
    const val = parseInt(guestInput.value, 10) || 0;
    if (val < 2000) guestInput.value = val + 1;
    updatePerGuest();
  });

  // ── Currency Chips ────────────────────────────────────────────────────
  document.getElementById("currency-chips").addEventListener("click", (e) => {
    const chip = e.target.closest(".currency-chip");
    if (!chip) return;
    currencyInput.value = chip.dataset.currency;
    document.querySelectorAll(".currency-chip").forEach((c) => c.classList.remove("active"));
    chip.classList.add("active");
    updatePerGuest();
  });
  // Sync manual currency typing with chips.
  currencyInput.addEventListener("input", () => {
    const val = currencyInput.value.toUpperCase();
    document.querySelectorAll(".currency-chip").forEach((c) => {
      c.classList.toggle("active", c.dataset.currency === val);
    });
  });

  // ── Per-Guest Live Preview ────────────────────────────────────────────
  function updatePerGuest() {
    const guests = parseInt(guestInput.value, 10);
    const budget = parseFloat(budgetInput.value);
    const curr = currencyInput.value.toUpperCase();
    if (guests > 0 && budget > 0 && curr.length === 3) {
      perGuestPreview.textContent = `≈ ${money(budget / guests, curr)} per guest`;
    } else {
      perGuestPreview.textContent = "";
    }
  }
  guestInput.addEventListener("input", updatePerGuest);
  budgetInput.addEventListener("input", updatePerGuest);

  // ── Preset Demos ──────────────────────────────────────────────────────
  const PRESETS = {
    wedding: { event_type: "wedding", name: "Sarah & James", guest_count: 100, budget: 25000, currency: "USD", venue: "mixed" },
    birthday: { event_type: "birthday", name: "Maya's 30th", guest_count: 30, budget: 3000, currency: "USD", venue: "indoor" },
    community: { event_type: "community", name: "Autumn Street Fair", guest_count: 200, budget: 8000, currency: "USD", venue: "outdoor" },
  };

  document.querySelectorAll(".preset-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const data = PRESETS[chip.dataset.preset];
      if (!data) return;

      // Set hidden select + segmented control
      document.getElementById("event_type").value = data.event_type;
      document.querySelectorAll('input[name="event_type_seg"]').forEach((r) => {
        r.checked = r.value === data.event_type;
      });
      document.getElementById("name").value = data.name;

      // Set event date to 6 months from now
      const future = new Date();
      future.setMonth(future.getMonth() + 6);
      document.getElementById("event_date").value = future.toLocaleDateString("en-CA");

      guestInput.value = data.guest_count;
      budgetInput.value = data.budget;
      currencyInput.value = data.currency;

      // Sync currency chips
      document.querySelectorAll(".currency-chip").forEach((c) => {
        c.classList.toggle("active", c.dataset.currency === data.currency);
      });

      // Set venue select + segmented control
      document.getElementById("venue").value = data.venue;
      document.querySelectorAll('input[name="venue_seg"]').forEach((r) => {
        r.checked = r.value === data.venue;
      });

      updatePerGuest();
    });
  });

  // ── Tile Builder ──────────────────────────────────────────────────────
  function tile(variant, title, body) {
    const id = `tile-${title.toLowerCase().replace(/\W+/g, "-")}`;
    const wrapper = el("section", undefined, { class: `tile ${variant}`, "aria-labelledby": id });
    wrapper.append(el("h3", title, { id }), body);
    return wrapper;
  }

  // ── Summary Widget (Hero Card) ────────────────────────────────────────
  function summaryBody(plan) {
    const days = daysUntil(plan.event_date);
    const wrap = el("div");

    // Event type badge
    const typeLabels = { wedding: "💍 Wedding", birthday: "🎂 Birthday", community: "🎪 Community" };
    const badge = el("span", typeLabels[plan.event_type] || titleCase(plan.event_type), { class: "summary-badge" });
    wrap.append(badge);

    wrap.append(el("p", plan.event_name, { class: "summary-name" }));
    if (days > 0) {
      wrap.append(el("p", String(days), { class: "summary-days" }), el("p", days === 1 ? "day to go" : "days to go", { class: "summary-label" }));
    } else if (days === 0) {
      wrap.append(el("p", "Today", { class: "summary-days" }), el("p", "It's event day!", { class: "summary-label" }));
    }
    wrap.append(
      el("p", `Total budget: ${money(plan.budget_total, plan.currency)}`, { class: "summary-meta" }),
      el("p", `${plan.vendors.length} vendor items · ${plan.timeline.length} milestones`, { class: "summary-meta" }),
    );
    return wrap;
  }

  // ── Warnings Widget ───────────────────────────────────────────────────
  function warningsBody(warnings) {
    const wrap = el("div");
    if (!warnings.length) {
      const ok = el("p", "✓ Everything looks good!", { class: "no-warnings" });
      wrap.append(ok);
      return wrap;
    }
    const badge = el("span", undefined, { class: "warning-badge" });
    badge.append(
      document.createTextNode(`${warnings.length} ${warnings.length === 1 ? "notice" : "notices"}`)
    );
    wrap.append(badge);

    const ul = el("ul", undefined, { class: "warning-list" });
    for (const warning of warnings) ul.append(el("li", warning));
    wrap.append(ul);
    return wrap;
  }

  // ── Budget Widget ─────────────────────────────────────────────────────
  function budgetBody(plan) {
    const wrap = el("div");

    const bar = el("div", undefined, { class: "budget-bar", "aria-hidden": "true" });
    plan.budget.forEach((line, index) => {
      const segment = el("span", undefined, { class: "budget-seg" });
      segment.style.flexGrow = String(line.share);
      segment.style.background = PALETTE[index % PALETTE.length];
      bar.append(segment);
    });

    const table = el("table");
    table.append(el("caption", "Split of your budget"));
    const thead = el("thead");
    const headRow = el("tr");
    for (const heading of ["Category", "Share", "Amount"]) {
      headRow.append(el("th", heading, { scope: "col" }));
    }
    thead.append(headRow);

    const tbody = el("tbody");
    plan.budget.forEach((line, index) => {
      const row = el("tr");
      const label = el("th", undefined, { scope: "row" });
      const swatch = el("span", undefined, { class: "swatch", "aria-hidden": "true" });
      swatch.style.background = PALETTE[index % PALETTE.length];
      label.append(swatch, document.createTextNode(titleCase(line.category)));
      row.append(
        label,
        el("td", `${Math.round(line.share * 100)}%`),
        el("td", money(line.amount, plan.currency)),
      );
      tbody.append(row);
    });

    table.append(thead, tbody);
    wrap.append(bar, table);
    return wrap;
  }

  // ── Vendor Checklist Widget ───────────────────────────────────────────
  function checklist(items) {
    const wrap = el("div");

    // Progress counter
    const progressWrap = el("div", undefined, { class: "checklist-progress" });
    const progressText = el("span", `0 of ${items.length} completed`);
    const progressBar = el("div", undefined, { class: "checklist-progress-bar" });
    const progressFill = el("div", undefined, { class: "checklist-progress-fill" });
    progressBar.append(progressFill);
    progressWrap.append(progressText, progressBar);
    wrap.append(progressWrap);

    const ul = el("ul", undefined, { class: "checklist" });
    items.forEach((item, index) => {
      const id = `vendor-${index}`;
      const li = el("li");
      const checkbox = el("input", undefined, { type: "checkbox", id });
      const label = el("label", item, { for: id });

      // Checkbox interaction: toggle checked style + update counter.
      checkbox.addEventListener("change", () => {
        li.classList.toggle("checked", checkbox.checked);
        const checked = ul.querySelectorAll("input:checked").length;
        progressText.textContent = `${checked} of ${items.length} completed`;
        progressFill.style.width = `${(checked / items.length) * 100}%`;
      });

      li.append(checkbox, label);
      ul.append(li);
    });
    wrap.append(ul);
    return wrap;
  }

  // ── Timeline Widget ───────────────────────────────────────────────────
  function timeline(tasks) {
    const ol = el("ol", undefined, { class: "timeline" });
    for (const task of tasks) {
      const li = el("li");
      li.append(el("time", task.due, { datetime: task.due }), el("span", task.title));
      ol.append(li);
    }
    return ol;
  }

  // ── Ideas Widget ──────────────────────────────────────────────────────
  function ideasBody(ideas, source) {
    const wrap = el("div");
    wrap.append(
      el(
        "p",
        source === "ai"
          ? "Tailored to your event."
          : "AI ideas were unavailable, so these are general suggestions.",
        { class: "hint" },
      ),
    );
    ideas.forEach((idea, index) => {
      const card = el("article", undefined, { class: index % 2 ? "idea idea-sand" : "idea idea-blue" });
      card.append(el("h4", idea.title), el("p", idea.description));
      wrap.append(card);
    });
    return wrap;
  }

  // ── Render Results ────────────────────────────────────────────────────
  function render(plan) {
    const grid = el("div", undefined, { class: "bento" });
    grid.append(
      tile("tile-summary", "Overview", summaryBody(plan)),
      tile("tile-warnings", "Things to check", warningsBody(plan.warnings)),
      tile("tile-budget", "Budget", budgetBody(plan)),
      tile("tile-vendors", "Vendor checklist", checklist(plan.vendors)),
      tile("tile-timeline", "Timeline", timeline(plan.timeline)),
      tile("tile-ideas", "Ideas", ideasBody(plan.ideas, plan.ideas_source)),
    );
    resultsEl.replaceChildren(grid);
    resultsEl.focus();
  }

  // ── Read Form Data ────────────────────────────────────────────────────
  function readForm() {
    const data = new FormData(form);
    return {
      event_type: data.get("event_type"),
      name: data.get("name"),
      event_date: data.get("event_date"),
      guest_count: Number(data.get("guest_count")),
      budget: Number(data.get("budget")),
      currency: String(data.get("currency")).toUpperCase(),
      venue: data.get("venue"),
      notes: data.get("notes") || "",
    };
  }

  function errorMessage(status, data) {
    if (status === 422 && typeof data.detail === "string") return data.detail;
    if (status === 422) return "Please check the highlighted fields and try again.";
    return "We could not build your plan right now. Please try again shortly.";
  }

  function setBusy(busy) {
    submitButton.disabled = busy;
    form.setAttribute("aria-busy", String(busy));
  }

  // ── Form Submission ───────────────────────────────────────────────────
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!form.reportValidity()) return;

    setBusy(true);
    statusEl.textContent = "Building your plan…";
    try {
      const response = await fetch("/api/plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(readForm()),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(errorMessage(response.status, data));
      render(data);
      statusEl.textContent = "Your plan is ready.";
    } catch (error) {
      statusEl.textContent = error.message;
    } finally {
      setBusy(false);
    }
  });
})();
