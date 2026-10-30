# Event Planning Assistant

An intelligent, full-stack event planning web application engineered for weddings, birthdays, and community gatherings. Enter core event parameters (guest count, budget, location type, date, special themes/needs) and receive a comprehensive event strategy: an exact budget breakdown, milestone timeline with adaptive schedule compression, context-aware vendor checklist, critical risk warnings, and tailored creative ideas.

---

## 1. Chosen Vertical

**Vertical: Intelligent Event Management & Logistics Planning**

Planning personal and community events is notoriously fragmented: organizers struggle with unrealistic budget allocations, compressed timelines, overlooked vendor dependencies, and generic theme ideas. 

This application bridges logistical rigor with generative creativity by delivering:
- **Weddings:** High-touch guest experience, comprehensive vendor contracts, accessible amenities, and delicate budget distribution (catering, venue, photography).
- **Birthdays:** Focus on entertainment, milestones, personalized activities, and balanced party supplies.
- **Community Events:** Permit lead times, public safety checks, volunteer coordination, and municipal compliance.

---

## 2. Approach and Logic

The system follows a **deterministic-core + probabilistic-enhancement** architecture:

```
                                  [ User Request ]
                                         │
                                         ▼
                            [ Pydantic Strict Validation ]
                           (extra="forbid", bounded ranges)
                                         │
                 ┌───────────────────────┼──────────────────────┐
                 ▼                       ▼                      ▼
       [ Budget Allocator ]    [ Adaptive Timeline ]   [ Vendor Checklist ]
       • Decimal precision     • Backward scheduling   • Base requirements
       • Category shares       • Lead-time compression • Contextual rules
       • Rounding absorption   • Rush date detection     (outdoors, shuttles)
                 │                       │                      │
                 └───────────────────────┼──────────────────────┘
                                         ▼
                             [ Risk & Decision Engine ]
                             • Budget per guest thresholds
                             • Weather & outdoor permit checks
                             • Lead time vs. milestone feasibility
                                         │
                                         ▼
                             [ Creative Idea Engine ]
                             • SHA-256 Keyed TTL Cache
                             • Prompt-injected sandbox
                             • LLM (Claude) with strict JSON output
                             • Deterministic template fallback
                                         │
                                         ▼
                             [ iOS Bento Grid UI ]
```

### Core Algorithmic Logic

1. **Decimal-Precise Budget Engine (`app/budget.py`)**
   - Floating-point calculations introduce IEEE 754 drift. All arithmetic uses Python's `decimal.Decimal`.
   - Category allocations are calculated using tailored percentage distributions per event type.
   - Any fractional cents created by division are mathematically absorbed by the **Contingency** category, guaranteeing that $\sum \text{Allocations} \equiv \text{Total Budget}$ to the penny.

2. **Adaptive Timeline Compression (`app/timeline.py`)**
   - Milestones are scheduled backward from the event date based on ideal standard lead times (e.g., booking venue 180 days prior).
   - If the user books with a shorter lead time (e.g., 45 days out), the engine dynamically **compresses** milestone intervals proportionately without scheduling tasks in the past.
   - Urgent tasks falling within 7 days of planning trigger explicit rush indicators.

3. **Contextual Vendor Evaluation (`app/vendors.py`)**
   - Generates essential vendor categories (venue, caterer, decor).
   - Dynamically injects conditional dependencies:
     - `Outdoors` or `Both` $\rightarrow$ Weather backup plan, portable restrooms, power generator, municipal permits.
     - `Guests > 75` with `Outdoors` $\rightarrow$ Shuttle/parking coordination.
     - `Special needs/accessibility` mentioned in preferences $\rightarrow$ Step-free route audit, accessible seating, quiet break zones.

4. **Rules & Warning Engine (`app/planner.py`)**
   - Assesses budget-per-guest feasibility: warns if per-guest spend drops below realistic industry baselines ($40/guest for weddings, $15 for birthdays, $5 for community fairs).
   - Detects extreme timelines: warns if an event is planned under 14 days in advance.
   - Flags missing wet-weather backups for outdoor events.

5. **LLM Synthesis & Fallback Resilience (`app/ideas.py` & `app/llm.py`)**
   - Formulates tailored themes, interactive activities, and personalized touches via Anthropic Claude.
   - Guarded by a SHA-256 hash-keyed in-memory TTL cache (128 entries, 300s expiration) for 0ms repeated responses.
   - If an API key is not supplied, rate limits are reached, or network fails, the system **automatically falls back to curated deterministic templates**, guaranteeing 100% uptime.

---

## 3. How the Solution Works

### Backend (FastAPI)
- **API Endpoint:** `POST /api/plan` receives validated event criteria and returns a structured JSON payload.
- **Security Middlewares:** 
  - Strict Content Security Policy (`default-src 'self'`).
  - Rate limiting via `slowapi` (10 requests/minute per client IP) prevents resource exhaustion.
  - Sanitization of user input text blocks to prevent prompt injection.
  - `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`.
- **Zero Third-Party Frontend Dependencies:** The backend serves plain HTML5/CSS3/Vanilla JS with zero external CDNs, completely CSP-compliant.

### Frontend (iOS Bento Grid Design System)
- **Aesthetic:** Modern Apple-inspired Bento Grid with Deep Editorial Blue (`#226192` multi-stop gradient) cards on a Warm Ivory (`#EAE6DE`) base canvas.
- **Micro-Interactions:** Custom spring physics transitions, interactive checklists, budget percentage visualization bars, and live per-guest cost preview.
- **Accessibility (a11y):** Full keyboard navigation, screen-reader live regions (`aria-live="polite"`), WCAG AAA color contrast, semantic form fieldsets, and `prefers-reduced-motion` support.

---

## 4. Key Assumptions Made

1. **Lead Time Flexibility:**
   - Permitting, venue availability, and vendor booking windows are modeled as adaptable timelines. In real-world municipal settings, permits may have strict statutory minimums that cannot be compressed.
2. **Currency Uniformity:**
   - The user selects a currency code (e.g., USD, EUR, GBP, INR). The system calculates splits accurately within that unit, assuming single-currency budgeting without multi-currency exchange conversion.
3. **Budget Proportions as Benchmarks:**
   - The category percentages (catering ~30%, venue ~15-20%, decor ~10-15%) are based on standard event planning industry averages. Actual local market rates and individual priorities may shift these ratios.
4. **Guest Count as Fixed Variable:**
   - Calculations treat the entered guest count as confirmed attendees. Realistic drop-off rates (RSVP attrition) are not deducted automatically, though the 10% contingency buffer accommodates minor headcount shifts.
5. **Stateless Operations:**
   - The app operates as an instant, privacy-first planning tool without database persistence. Plans are consumed immediately or exported/printed from the client.

---

## 5. Getting Started

### Local Setup
```bash
# Clone the repository
git clone https://github.com/Yuvaakhil18/GENAI_Event_Planner.git
cd GENAI_Event_Planner

# Install dependencies
pip install -r requirements.txt

# (Optional) Provide Claude API key for live LLM suggestions
export ANTHROPIC_API_KEY=sk-ant-...

# Run development server
uvicorn app.main:app --reload
```
Access the application at [http://127.0.0.1:8000](http://127.0.0.1:8000). Interactive Swagger documentation is available at `/docs`.

### Running Tests & Quality Verification
```bash
# Run complete test suite (79 unit and integration tests)
pytest

# Run tests with 100% statement coverage report
pytest --cov=app --cov-report=term-missing
```

---

## 6. Deployment (Vercel)

The repository is configured for serverless deployment on Vercel:
- `vercel.json`: Directs static assets to Vercel CDN and routes API calls to the ASGI handler.
- `api/index.py`: Serverless ASGI entrypoint for Python runtime.

To deploy:
1. Import the repository in [vercel.com](https://vercel.com).
2. Set `ANTHROPIC_API_KEY` in **Settings → Environment Variables** (optional).
3. Deploy!
