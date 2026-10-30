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
  /**
   * Create a DOM element with optional text content and attributes.
   * @param {string} tag - HTML tag name.
   * @param {string} [text] - Text content.
   * @param {Object<string,string>} [attrs] - Attribute key-value pairs.
   * @returns {HTMLElement}
   */
  function el(tag, text, attrs = {}) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
    return node;
  }

  /** @param {string} text - Underscore-separated text to title-case. */
  const titleCase = (text) => text.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());

  /**
   * Format a monetary amount using the browser's Intl API.
   * @param {number} amount
   * @param {string} currency - ISO 4217 currency code.
   * @returns {string}
   */
  function money(amount, currency) {
    try {
      return new Intl.NumberFormat(undefined, { style: "currency", currency }).format(amount);
    } catch {
      return `${amount.toFixed(2)} ${currency}`;
    }
  }

  /**
   * Calculate the number of days from today until the given ISO date.
   * @param {string} isoDate - Date string in YYYY-MM-DD format.
   * @returns {number}
   */
  function daysUntil(isoDate) {
    const [year, month, day] = isoDate.split("-").map(Number);
    const event = new Date(year, month - 1, day);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return Math.round((event - today) / 86400000);
  }

  // ── Segmented Controls ────────────────────────────────────────────────
  // Sync segmented radio buttons → hidden <select> for form submission.
  /**
   * Wire a set of radio buttons to keep a hidden <select> in sync.
   * @param {string} radioName - Name attribute shared by the radio inputs.
   * @param {string} selectId - ID of the hidden select element.
   */
  function setupSegmentedControl(radioName, selectId) {
    const radios = Array.from(document.querySelectorAll(`input[name="${radioName}"]`));
    const hiddenSelect = document.getElementById(selectId);
    radios.forEach((radio, index) => {
      radio.addEventListener("change", () => {
        if (radio.checked) hiddenSelect.value = radio.value;
      });
      radio.addEventListener("keydown", (e) => {
        let nextIndex = null;
        if (e.key === "ArrowRight" || e.key === "ArrowDown") {
          e.preventDefault();
          nextIndex = (index + 1) % radios.length;
        } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
          e.preventDefault();
          nextIndex = (index - 1 + radios.length) % radios.length;
        }
        if (nextIndex !== null) {
          radios[nextIndex].checked = true;
          radios[nextIndex].focus();
          hiddenSelect.value = radios[nextIndex].value;
        }
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
    document.querySelectorAll(".currency-chip").forEach((c) => {
      c.classList.remove("active");
      c.setAttribute("aria-pressed", "false");
    });
    chip.classList.add("active");
    chip.setAttribute("aria-pressed", "true");
    updatePerGuest();
  });
  // Sync manual currency typing with chips.
  currencyInput.addEventListener("input", () => {
    const val = currencyInput.value.toUpperCase();
    document.querySelectorAll(".currency-chip").forEach((c) => {
      const active = c.dataset.currency === val;
      c.classList.toggle("active", active);
      c.setAttribute("aria-pressed", active ? "true" : "false");
    });
  });

  // ── Per-Guest Live Preview ────────────────────────────────────────────
  /** Update the per-guest cost preview below the budget field. */
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
  /**
   * Create a bento-grid tile (section) with a heading and body.
   * @param {string} variant - CSS class variant for styling.
   * @param {string} title - Section heading text.
   * @param {HTMLElement} body - Rendered content element.
   * @returns {HTMLElement}
   */
  function tile(variant, title, body) {
    const id = `tile-${title.toLowerCase().replace(/\W+/g, "-")}`;
    const wrapper = el("section", undefined, { class: `tile ${variant}`, "aria-labelledby": id });
    wrapper.append(el("h3", title, { id }), body);
    return wrapper;
  }

  // ── Summary Widget (Hero Card) ────────────────────────────────────────
  /** Build the hero summary card body. */
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
  /** Build the warnings list or a success message. */
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
  /** Build the budget breakdown bar chart and table. */
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
  /** Build the interactive vendor checklist with progress tracking. */
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
  /** Build the ordered timeline list. */
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
  /** Build the ideas card grid. */
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
  /** Render all result tiles into the results container. */
  function render(plan) {
    const grid = el("div", undefined, { class: "bento", role: "region", "aria-label": "Event Strategy Breakdown" });
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
  /** Read and normalise form data into an API-ready payload. */
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

  /** Map an HTTP error status to a user-friendly message. */
  function errorMessage(status, data) {
    if (status === 422 && typeof data.detail === "string") return data.detail;
    if (status === 422) return "Please check the highlighted fields and try again.";
    return "We could not build your plan right now. Please try again shortly.";
  }

  /** Toggle the form's busy state and disable the submit button. */
  function setBusy(busy) {
    submitButton.disabled = busy;
    form.setAttribute("aria-busy", String(busy));
  }

  // ── Validation Helpers ────────────────────────────────────────────────
  const fieldsToValidate = [
    { input: document.getElementById("name"), error: document.getElementById("name-error"), name: "Event name" },
    { input: document.getElementById("event_date"), error: document.getElementById("date-error"), name: "Event date" },
    { input: document.getElementById("guest_count"), error: document.getElementById("guest-error"), name: "Number of guests" },
    { input: document.getElementById("budget"), error: document.getElementById("budget-error"), name: "Total budget" },
    { input: document.getElementById("currency"), error: document.getElementById("currency-error"), name: "Currency code" },
  ];

  fieldsToValidate.forEach(({ input, error }) => {
    if (!input || !error) return;
    input.addEventListener("input", () => {
      if (input.validity.valid) {
        input.removeAttribute("aria-invalid");
        error.textContent = "";
      }
    });
  });

  function validateAllFields() {
    let firstInvalid = null;
    fieldsToValidate.forEach(({ input, error, name }) => {
      if (!input || !error) return;
      if (!input.checkValidity()) {
        input.setAttribute("aria-invalid", "true");
        if (input.validity.valueMissing) {
          error.textContent = `${name} is required.`;
        } else if (input.validity.rangeUnderflow) {
          error.textContent = `${name} must be at least ${input.min}.`;
        } else if (input.validity.rangeOverflow) {
          error.textContent = `${name} cannot exceed ${input.max}.`;
        } else if (input.validity.patternMismatch) {
          error.textContent = `${name} must be a 3-letter currency code (e.g., USD, EUR).`;
        } else {
          error.textContent = input.validationMessage;
        }
        if (!firstInvalid) firstInvalid = input;
      } else {
        input.removeAttribute("aria-invalid");
        error.textContent = "";
      }
    });
    return firstInvalid;
  }

  // ── Form Submission ───────────────────────────────────────────────────
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const invalidInput = validateAllFields();
    if (invalidInput) {
      invalidInput.focus();
      return;
    }

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
