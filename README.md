# Event Planning Assistant

A planning assistant for weddings, birthdays and community events. Enter the basics
and it returns a budget split, a dated task timeline, a vendor checklist, warnings
based on the context, and personalised ideas.

Ideas come from an LLM (Claude) when an API key is configured. Without one, or if the
model call fails, the app falls back to built-in templates, so the planner always works.

## Run it

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-...        # optional; omit to use template ideas
export PLANNER_MODEL=claude-haiku-5-5  # optional
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. API docs are at `/docs`.

## Test

```bash
python -m pytest -q                          # quick run
python -m pytest --cov=app --cov-report=term-missing  # with coverage
```

Current suite: **64 tests, 96 % line coverage** across all modules.

## Design

| Layer | File | Responsibility |
|---|---|---|
| Models | `app/models.py` | Validated input (Pydantic, `extra="forbid"`) and output shapes |
| Budget | `app/budget.py` | Category shares per event type; Decimal arithmetic; contingency absorbs rounding; per-guest check |
| Timeline | `app/timeline.py` | Milestones scheduled back from the event date; compressed when lead time is short |
| Vendors | `app/vendors.py` | Base checklist plus conditional items (outdoor, large guest count, shuttles) |
| Ideas | `app/ideas.py` | LLM prompt, strict output parsing, SHA-256–keyed TTL cache, template fallback |
| LLM client | `app/llm.py` | Small `TextGenerator` protocol, so the provider can be swapped or faked in tests |
| Planner | `app/planner.py` | Decision rules that turn the request context into warnings; assembles the plan |
| API | `app/main.py` | FastAPI routes, security headers, rate limiting, dependency injection via `create_app` |
| UI | `static/` | Plain HTML, CSS and JS; no build step, no third-party scripts |

## Architecture

```
User ──▶ GET /          ──▶ Static HTML/CSS/JS
     ──▶ POST /api/plan ──▶ Rate limiter (10 req/min per IP)
                             │
                             ▼
                         Pydantic validation (extra="forbid")
                             │
                             ├─▶ budget.allocate()  ──▶ Decimal-precise splits
                             ├─▶ timeline.build()   ──▶ compressed schedule
                             ├─▶ vendors.checklist() ──▶ context-aware items
                             ├─▶ planner.warnings()  ──▶ decision rules
                             └─▶ ideas.generate()    ──▶ TTL cache ──▶ LLM / templates
                                                               │
                                                          Plan JSON ──▶ UI renders bento grid
```

## Security

- **Content Security Policy**: `default-src 'self'`; no inline scripts or styles allowed.
  `frame-ancestors 'none'` blocks framing; `X-Content-Type-Options: nosniff` prevents MIME sniffing.
- **Rate limiting**: The `/api/plan` endpoint is capped at 10 requests per minute per client IP
  via slowapi, protecting against cost-exhaustion attacks on the LLM and compute overload.
- **Input validation**: Pydantic with `extra="forbid"` rejects unknown fields. Budget, dates, guest
  counts and text lengths are all bounded. Control characters are scrubbed from strings.
- **XSS-free rendering**: The client uses `document.createElement` and `textContent` exclusively;
  no `innerHTML`, `eval`, or third-party scripts.
- **Prompt injection defense**: User-supplied notes are wrapped in `<event_details>` tags and
  sanitised (angle brackets escaped). The system prompt instructs the model to treat the block
  as untrusted data. LLM output is parsed as strict JSON; prose responses are discarded.
- **Secret hygiene**: The API key field uses `repr=False` on the dataclass, so it never appears
  in logs, tracebacks, or debug output.

## Efficiency

- **LLM response cache**: A SHA-256–keyed TTL cache (128 entries, 5 minutes) deduplicates
  identical LLM calls, delivering 0 ms responses for repeated configurations.
- **Decimal budget arithmetic**: `decimal.Decimal` is used for budget allocation, eliminating
  IEEE 754 floating-point rounding drift.
- **Minimal asset footprint**: The full page weighs under 40 KB (HTML + CSS + JS) with no
  frameworks, bundlers, or external dependencies loaded in the browser.

## Accessibility

- **Semantic HTML5**: Single `<h1>`, logical heading hierarchy, `<main>`, `<fieldset>`/`<legend>`,
  and `<article>` for idea cards.
- **Skip navigation**: A `.skip-link` jumps directly to `#main`.
- **ARIA attributes**: `aria-live="polite"` on the per-guest preview, `role="status"` on the
  form status message, `aria-busy` on the form during submission, `aria-controls` on stepper
  buttons, `aria-hidden` and `tabindex="-1"` on hidden proxy selects.
- **Motion safety**: Comprehensive `@media (prefers-reduced-motion: reduce)` rules disable
  all transitions, animations and transforms.

## Test coverage

| Test file | Module tested | Tests |
|---|---|---|
| `test_api.py` | API routes, security headers, input validation | 15 |
| `test_budget.py` | Allocation sums, drift absorption, per-guest warning | 9 |
| `test_ideas.py` | JSON parsing, code fences, prompt escaping, LLM fallback | 8 |
| `test_timeline.py` | Compression, rush notes, sorting, past-date rejection | 6 |
| `test_vendors.py` | Every conditional branch in the vendor checklist | 12 |
| `test_planner.py` | Context warnings, orchestration, multi-warning combination | 12 |

## Limitations

These are known and deliberate:

- **No authentication** and **no HTTPS** are built in. Put the app behind a reverse proxy (nginx, Cloudflare) that enforces both before exposing it publicly.
- **No persistence.** Plans are not saved. A natural next step is a plan store with per-user access control.
- **Currency** is not converted. The app uses the code the user enters.
- **Template ideas** are generic. The LLM path produces the personalised ideas.
- **Timeline offsets** are sensible defaults, not legal or contractual deadlines. Permit lead times vary by locality.
