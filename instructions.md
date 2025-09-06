# 0) Cover Sheet & Quick Abstract

**Project:** 30‑Day Cash‑Flow Scheduler (Interactive, Resume‑From‑Any‑Day)
**Owner:** Frankie
**Goal:** Produce exact, constraint‑correct 30‑day schedules that (1) never go negative intra‑day, (2) pay all bills on due dates, (3) satisfy all scheduling/working rules, (4) land final day balance within a strict band, and (5) minimize workdays lexicographically with tie‑breakers.
**Key Feature:** “Resume from any day” by inserting a manual adjustment to match an edited end‑of‑day balance, then solving forward for the remaining days.
**Primary Solver:** Dynamic Programming (integer cents).
**Cross‑Verifier:** CP‑SAT (OR‑Tools) with sequential lexicographic solves.
**Platforms:** Linux / macOS, Python 3.11+.

---

# 1) Product Requirements Document (PRD)

## 1.1 Problem Statement

Plan daily work shifts and pay bills across a fixed 30‑day horizon with exact hard constraints and a lexicographic optimization objective. Allow a user to edit any day’s closing balance and re‑solve the remaining days without mutating historical ledger events.

## 1.2 Users

- **Primary:** Individual planner (Frankie).
- **Secondary:** Ops/finance‑minded users with similar constraints.

## 1.3 Core User Stories

- **US‑01:** As a user, I can **generate** a 30‑day schedule that satisfies all hard rules and achieves a final balance within a target band.
- **US‑02:** As a user, I can **edit** the end‑of‑day (EOD) balance for Day _d_. The system records a **Manual Adjustment** on Day _d_ and **re‑solves** days _d+1..30_.
- **US‑03:** As a user, I can **view** a markdown/CSV/JSON table (Section 1 format) and audit totals (Section 2) plus a validation checklist (Section 3).
- **US‑04:** As a user, I can **export** results (MD/CSV/JSON) and **diff** two solutions.
- **US‑05:** As a user, I can **see why** a particular shift choice was required (compact explanation).

## 1.4 Success Criteria

- Generates a feasible plan when one exists; otherwise returns a **minimal infeasibility certificate** (what to relax or how many extra workdays required).
- **Deterministic** output for a given input.
- Cross‑verified: DP’s lexicographic optimum matches CP‑SAT’s sequential‑lex optimum on canonical datasets.

## 1.5 Non‑Goals

- No cloud services, no persistent user auth, no graphics beyond terminal/TUI.
- No real‑time Amazon Flex integration.

---

# 2) System Requirements Specification (SRS)

## 2.1 Functional Requirements

- FR‑01: Solve full month (days 1–30) with **intra‑day order**: opening → deposits → shifts (gross − \$8 if any shift) → bills → closing.
- FR‑02: Enforce **hard constraints** (see §7 Validation Rules).
- FR‑03: Lexicographic objective:
  `( #work_days, back_to_back_count, |final − 490.50|, large_day_count, single_shift_preference )`
  where single‑shift preference penalizes M=1, L=2 (S=0, SS=0).
- FR‑04: Resume from day _d+1_: after inserting a manual adjustment on day _d_, seed DP with prefix state and re‑solve tail.
- FR‑05: Output Sections 1–3 exactly in markdown; optional JSON/CSV.
- FR‑06: CLI commands (see §6).
- FR‑07: Validator reports pass/fail with reasons.

## 2.2 Non‑Functional Requirements

- NFR‑01: **Correctness first** (integer cents; no floats).
- NFR‑02: **Determinism** across runs.
- NFR‑03: Performance: DP should finish within seconds for 30 days; resume solve typically **sub‑second** on modern hardware.
- NFR‑04: Test coverage: unit+property+regression; DP vs CP‑SAT cross‑check green.
- NFR‑05: Code quality: typed (mypy), linted (ruff), formatted (black).

---

# 3) Architecture & Design

## 3.1 Repository Layout

```
cashflow/
  core/
    model.py         # Money utils (cents), dataclasses (Event, DayState, Plan)
    ledger.py        # Build day ledgers from events (opening→...→closing)
    validate.py      # Independent validator (no solver calls)
  engines/
    dp.py            # Primary DP solver (full month & resume-from-day)
    cpsat.py         # CP-SAT cross-verifier (OR-Tools), sequential lex solves
  io/
    render.py        # Markdown/CSV/JSON rendering
    store.py         # Load/save plan.json; schema checks
  cli.py             # Typer-based CLI commands
  tests/
    unit/            # Core unit tests
    property/        # Hypothesis-based property tests
    regression/      # Golden outputs & known fixtures
  pyproject.toml
  requirements.txt
  README.md
  LICENSE
  Makefile
```

## 3.2 Data Flow (Full Solve)

1. Load `plan.json` → event stream.
2. Build ledger day‑by‑day (deposits/bills/adjustments).
3. Run DP solver → `actions[1..30]` (each ∈ {O,S,M,L,SS}).
4. Produce Section 1–3 views; run validator; export.

## 3.3 Data Flow (Resume from Day _d+1_)

1. Compute actual closing for Day _d_; compare to user‑entered EOD.
2. Insert `Manual Adjustment` on Day _d_ equal to the difference.
3. Rebuild ledger through Day _d_; capture **seed state**:
   `(last_6_off_bits, bit_count, prev_worked, workdays_used, net_to_date, opening_{d+1})`.
4. Re‑solve **d+1..30** with DP using seeded state.

## 3.4 Core State for DP

- `bits` (int): last up to 6 days Off flags as a bit‑field (oldest→newest).
- `cnt` (0..6): how many bits are valid so far.
- `prevWorked` (0/1).
- `workUsed` (0..30).
- `netSoFar` (cents) **relative to Amazon work only**.

State value stores **cost tuple**: `(b2b, large_count, single_pen)` plus backpointers.

---

# 4) Data Model & File Formats

## 4.1 Event Types

- `deposit`: {day, amount}
- `bill`: {day, name, amount}
- `shift`: {day, code in \[O,S,M,L,SS]}
- `adjustment`: {day, amount, note} ← created by EOD override
- `meta`: target_end, band, rent_guard

## 4.2 Plan JSON (schema)

```json
{
  "start_balance": 90.50,
  "target_end": 490.50,
  "band": 25.00,
  "rent_guard": 1636.00,
  "deposits": [{"day":11,"amount":1021.00},{"day":25,"amount":1021.00}],
  "bills": [{"day":1,"name":"Auto Insurance","amount":177.00}, ...],
  "actions": [null, null, ..., null],  // 30 slots; null unless locked/prefilled
  "manual_adjustments": [],            // [{ "day": 12, "amount": +123.00, "note": "EOD override" }]
  "locks": [],                         // [{ "start": 1, "end": 12 }]
  "metadata": {"version":"1.0.0"}
}
```

**JSON Schema (excerpt, draft‑2020‑12):**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": [
    "start_balance",
    "target_end",
    "band",
    "rent_guard",
    "deposits",
    "bills",
    "actions"
  ],
  "properties": {
    "start_balance": { "type": "number", "minimum": 0 },
    "target_end": { "type": "number", "minimum": 0 },
    "band": { "type": "number", "minimum": 0 },
    "rent_guard": { "type": "number", "minimum": 0 },
    "deposits": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["day", "amount"],
        "properties": {
          "day": { "type": "integer", "minimum": 1, "maximum": 30 },
          "amount": { "type": "number" }
        }
      }
    },
    "bills": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["day", "name", "amount"],
        "properties": {
          "day": { "type": "integer", "minimum": 1, "maximum": 30 },
          "name": { "type": "string" },
          "amount": { "type": "number" }
        }
      }
    },
    "actions": {
      "type": "array",
      "minItems": 30,
      "maxItems": 30,
      "items": {
        "type": ["string", "null"],
        "enum": ["O", "S", "M", "L", "SS", null]
      }
    },
    "manual_adjustments": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["day", "amount"],
        "properties": {
          "day": { "type": "integer", "minimum": 1, "maximum": 30 },
          "amount": { "type": "number" },
          "note": { "type": "string" }
        }
      }
    },
    "locks": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["start", "end"],
        "properties": {
          "start": { "type": "integer", "minimum": 1, "maximum": 30 },
          "end": { "type": "integer", "minimum": 1, "maximum": 30 }
        }
      }
    }
  }
}
```

---

# 5) Algorithms

## 5.1 DP (Primary)

- **Actions per day:** `A = {'O','S','M','L','SS'}` (Day 1: `{'L'}`).
- **Net per action (cents):** `O=0, S=5600, M=6750, L=8650, SS=12000`.
- **Transition feasibility (per day `t`):**

  1. **7‑day Off‑Off Rule:** In any rolling 7‑day window ending at `t`, there must exist at least one `Off,Off` pair. Enforced by checking the current 7‑vector derived from `(bits,cnt)` plus today’s Off flag.
  2. **Non‑negativity:** `closing_t >= 0` after applying deposits, shift net, and bills for day `t`.
  3. **Rent guard (Day 30):** `pre_rent_balance >= rent_guard` after deposits & shifts (before paying rent).
  4. **Shift pairing:** Two‑shift days allowed **only as SS**; Large cannot be in a two‑shift day; max two shifts per day.
  5. **Day 1 Large:** Day 1 action must be `L`.

- **Objective cost per step:**

  - `workdays += (action != 'O')`
  - `b2b += (prevWorked and action != 'O')`
  - `large_days += (action == 'L')`
  - `single_pen += 1 if action=='M' else 2 if action=='L' else 0` (SS, S, O give 0)

- **Global selection:** After Day 30, select states with **final balance within target band** and minimum **lexicographic tuple**:

  ```
  (workdays, b2b, abs(final - target_end), large_days, single_pen)
  ```

- **Lower/upper pruning:**
  Let `K` be the target workdays being searched (start from bound, increment only if needed).
  At day `t`, with `net_so_far` and `work_used`:

  - Max additional net = `(K - work_used) * 12000`.
  - If `net_so_far + max_additional_net < MIN_NET`, prune.
  - If `net_so_far > MAX_NET`, prune.

### Pseudocode (resume‑capable)

```
DP[0] = { (bits=0,cnt=0,prevW=0,work=0,net=0) : cost=(0,0,0) }

for day in 1..30:
  for each state in DP[day-1]:
    for a in allowed(day):
       if work+worked(a) > K: continue
       if !rolling_off_off_ok(bits,cnt,a,day): continue
       net_new = net + NET[a]
       if net_new > MAX_NET: continue
       if net_new + 12000*(K - (work+worked(a))) < MIN_NET: continue
       closing = opening(day) + deposits(day) + net_new - bills(day)
       if closing < 0: continue
       if day==30 and (opening30 + deposits30 + NET[a]) < RENT_GUARD: continue
       cost' = update_cost(cost,a,prevW)
       state' = update_state(bits,cnt,a,work,net_new)
       keep best (lexicographic) cost' for state'
```

## 5.2 CP‑SAT (Cross‑Verification)

- One‑hot daily vars: `x[t,action] ∈ {0,1}`.
- Workday: `w[t] = 1 - x[t,'O']`.
- B2B count: sum `b2b = Σ_t (w[t]*w[t+1])` (linearize with auxiliary vars).
- Off‑Off in each 7‑day window: introduce `off[t] = x[t,'O']`; require `Σ_i z[i] ≥ 1` where `z[i] ≤ off[i]` and `z[i] ≤ off[i+1]` and `z[i] ≥ off[i]+off[i+1]-1`.
- Day 1 `x[1,'L']=1`. Day 30 pre‑rent guard via linear balance constraints.
- **Sequential lexicographic solving:**
  Solve 1: minimize `Σ w[t]`.
  Add equality; Solve 2: minimize `b2b`.
  Add equality; Solve 3: minimize `abs(final-target)` (linearized).
  Add equality; Solve 4: minimize `Σ x[t,'L']`.
  Add equality; Solve 5: minimize single‑shift penalty sum.

---

# 6) CLI & Program Interfaces

## 6.1 CLI (Typer)

```
cash solve                       # full-month solve (prints table + validation)
cash show                        # print table only
cash export --format md --out out.md
cash set-eod <day> <amt>         # set EOD on <day> and re-solve tail
cash verify                      # DP vs CP-SAT cross-check (sequential lex)

# Future ideas (not all implemented):
# cash go <day>                   # move focus to day
# cash solve --from <day>         # resume solve from day
# cash pareto --max 5             # list Pareto/lex ties
# cash why <day>                  # explain local choice

# Global flags (future)
# --forbid-large-after-day1
# --target <amt> --band <amt>
# --engine dp|cpsat
```

## 6.2 Python Interfaces

```python
# engines/dp.py
def solve(plan) -> Schedule: ...
def solve_from(plan, start_day: int, seed_state: SeedState) -> Schedule: ...

# engines/cpsat.py
def verify_lex_optimal(plan, schedule_dp) -> VerificationReport: ...

# core/ledger.py
def build_ledger(plan) -> List[DayLedger]: ...
def apply_manual_adjustment(plan, day:int, new_eod:Decimal) -> None: ...
def seed_state(plan, up_to_day:int) -> SeedState: ...

# core/validate.py
def validate(plan, schedule) -> ValidationReport: ...
```

---

# 7) Validation Rules (Hard Constraints)

- **Balance non‑negative at all times** (after each day’s close).
- **All bills paid on their due dates**.
- **Final Day‑30 closing balance** ∈ `[490.50 ± 25.00]`.
- **Day 1** must begin with **Large**.
- **Max 2 shifts/day;** two‑shift days are **Small + Small** only.
- **Large** scheduled alone (never paired); at most one Large per day.
- **Work‑day cost**: if any shift worked that day, subtract exactly **\$8.00** once.
- **Off day** = zero shifts, zero work cost.
- **Every rolling 7‑day window** (windows \[1–7] … \[24–30]) contains at least **one “Off, Off” pair** (two consecutive Off days).
- **Day‑30 rent guard:** after deposits and shifts on Day 30 (before rent), balance ≥ **\$1,636**.
- **Intra‑day evaluation order**: Opening → Deposits → Shifts (gross−\$8 if worked) → Bills → Closing.

---

# 8) Test Plan

## 8.1 Unit Tests

- Money utils: cents conversion, no rounding drift.
- Ledger build: deterministic openings/closings with manual adjustments.
- Off‑Off detector across boundary windows.

## 8.2 Property Tests (Hypothesis)

- Randomized deposits/bills within bounded ranges:

  - If solver returns schedule → `validate()` is True.
  - Otherwise returns infeasibility message with **tight bound** (required net vs horizon).

## 8.3 Regression Tests

- Canonical dataset (the one you supplied) → assert:

  - Objectives tuple equals `(19, 11, $0.97, 3, 0)` for the strict lexicographic optimum.
  - Section 1–3 markdown matches golden (allowing whitespace tolerance).

## 8.4 Cross‑Verification

- `cash verify`: run DP, then CP‑SAT sequential objectives; assert equality. On mismatch, dump full artifacts.

## 8.5 Acceptance Tests (Scripts)

- **AT‑01:** Full solve prints Section 1 table with no negative balances and all checks `[x]`.
- **AT‑02:** `set-eod 12 1286.01` then `solve --from 13` → feasible tail, checks pass.
- **AT‑03:** Force infeasibility (reduce band severely) → solver returns certificate: minimal extra workdays or increased band needed.

---

# 9) Project Plan (Week)

**Day 1 (today):**

- Create repo structure (§3.1).
- Port current solver into `engines/dp.py`; isolate money & ledger.
- Implement `validate.py`.
- Commands: `solve`, `show`, `export`.
- Tests: basic unit + one regression.

**Day 2:**

- Implement manual adjustment + recompute prefix.
- Seeded DP `solve_from()`; CLI: `go`, `set-eod`, `solve --from`.
- Tests: resume scenarios, Off‑Off across boundary.

**Day 3:**

- Build CP‑SAT model; add `verify` command.
- Regression: ensure CP‑SAT matches DP on canonical case.

**Day 4:**

- `pareto` (collect a small frontier of lex‑ties) and `why` (local counterfactual).
- Tests for explanations: ensure they name the first constraint that breaks.

**Day 5:**

- Polish rendering; CSV/JSON exports; error messages; guardrails.
- Add `--forbid-large-after-day1`, `--target`, `--band`.

**Day 6–7:**

- Property tests (Hypothesis); CI (GitHub Actions) with lint, type‑check, tests.
- Documentation: README, Developer Guide, Troubleshooting.

---

# 10) Dev Environment & Setup

## 10.1 Requirements

- Python **3.11+**
- (Optional) OR‑Tools **9.10+** for CP‑SAT.
- pipx or venv; make; git.

## 10.2 Install

```bash
git clone <repo>
cd cashflow
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

**requirements.txt**

```
typer>=0.12
rich>=13.7
pydantic>=2.5
orjson>=3.10
hypothesis>=6.100
pytest>=8.2
mypy>=1.10
ruff>=0.5
black>=24.4
ortools>=9.10 ; platform_system!="Darwin" or platform_machine!="arm64"
ortools>=9.8  ; platform_system=="Darwin" and platform_machine=="arm64"
```

_(CP‑SAT is optional; if not installed, `cash verify` is disabled.)_

## 10.3 Run

```bash
python -m cashflow.cli solve
python -m cashflow.cli show --focus 10-18
python -m cashflow.cli set-eod 12 1286.01
python -m cashflow.cli solve --from 13
python -m cashflow.cli export --format md --out schedule.md
python -m pytest -q
```

---

# 11) Build, Release, & CI

**Makefile**

```makefile
.PHONY: setup lint type test format verify
setup: ; pip install -r requirements.txt
lint: ; ruff check cashflow && black --check cashflow
type: ; mypy cashflow
test: ; pytest -q
format: ; black cashflow && ruff check cashflow --fix
verify: ; python -m cashflow.cli verify
```

**GitHub Actions (ci.yml, excerpt)**

```yaml
name: ci
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt
      - run: ruff check cashflow
      - run: black --check cashflow
      - run: mypy cashflow
      - run: pytest -q
```

**Versioning:** Semantic versioning `MAJOR.MINOR.PATCH`.
**Release:** Tag on main; publish build artifacts (wheel) if needed.

---

# 12) Observability & Logging

- Logging levels: INFO (high‑level steps), DEBUG (DP pruning counts, first failing constraint per day for diagnostics), ERROR (infeasibility explanations).
- `--log debug` flag to print a compact **Feasibility Log** (opening→deposits→net→bills→closing per day).

---

# 13) Risks & Mitigations

| Risk                                    | Impact             | Mitigation                                                                            |
| --------------------------------------- | ------------------ | ------------------------------------------------------------------------------------- |
| OR‑Tools install issues on macOS arm64  | Blocks verify step | Make CP‑SAT optional; pin known‑good versions; provide brew guidance                  |
| Off‑Off rule misapplied across boundary | Invalid schedules  | Single source of truth in validator; dedicated tests covering windows \[1–7]…\[24–30] |
| Rounding/float drift                    | Incorrect balances | Integer cents only                                                                    |
| Resume seed errors                      | Impossible tails   | Ledger recompute + unit tests for seed-state serialization                            |
| Performance regressions                 | Slow solves        | Profiling hooks; DP state cap by strong pruning                                       |

---

# 14) Security & Privacy

- Local, offline. No PII beyond amounts and dates.
- No telemetry by default.
- License dependencies: OR‑Tools (Apache‑2.0), others permissive.

---

# 15) Maintenance & Ownership

- **CODEOWNERS:** assign core/ and engines/ to the lead engineer.
- **Definition of Done:**

  - `validate()` green, regression tests green, `verify` matches DP=CP‑SAT, README updated.

---

# 16) Appendices

## 16.1 Section 1/2/3 Output Contract (Markdown)

- **Exactly**: the table columns and checklist lines from your spec; renderer must match names and order.

## 16.2 Example `plan.json` (canonical dataset)

```json
{
  "start_balance": 90.5,
  "target_end": 490.5,
  "band": 25.0,
  "rent_guard": 1636.0,
  "deposits": [
    { "day": 11, "amount": 1021.0 },
    { "day": 25, "amount": 1021.0 }
  ],
  "bills": [
    { "day": 1, "name": "Auto Insurance", "amount": 177.0 },
    { "day": 2, "name": "YouTube Premium", "amount": 8.0 },
    { "day": 5, "name": "Groceries", "amount": 112.5 },
    { "day": 5, "name": "Weed", "amount": 20.0 },
    { "day": 8, "name": "Paramount Plus", "amount": 12.0 },
    { "day": 8, "name": "iPad AppleCare", "amount": 8.49 },
    { "day": 10, "name": "Streaming Svcs", "amount": 230.0 },
    { "day": 11, "name": "Cat Food", "amount": 40.0 },
    { "day": 12, "name": "Groceries", "amount": 112.5 },
    { "day": 12, "name": "Weed", "amount": 20.0 },
    { "day": 14, "name": "iPad AppleCare", "amount": 8.49 },
    { "day": 16, "name": "Cat Food", "amount": 40.0 },
    { "day": 17, "name": "Car Payment", "amount": 463.0 },
    { "day": 19, "name": "Groceries", "amount": 112.5 },
    { "day": 19, "name": "Weed", "amount": 20.0 },
    { "day": 22, "name": "Cell Phone", "amount": 177.0 },
    { "day": 23, "name": "Cat Food", "amount": 40.0 },
    { "day": 24, "name": "AI Subscription", "amount": 220.0 },
    { "day": 25, "name": "Electric", "amount": 139.0 },
    { "day": 25, "name": "Ring Subscription", "amount": 10.0 },
    { "day": 26, "name": "Groceries", "amount": 112.5 },
    { "day": 26, "name": "Weed", "amount": 20.0 },
    { "day": 28, "name": "iPhone AppleCare", "amount": 13.49 },
    { "day": 29, "name": "Internet", "amount": 30.0 },
    { "day": 29, "name": "Cat Food", "amount": 40.0 },
    { "day": 30, "name": "Rent", "amount": 1636.0 }
  ],
  "actions": [
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null
  ],
  "manual_adjustments": [],
  "locks": [],
  "metadata": { "version": "1.0.0" }
}
```

## 16.3 Coding Standards

- **Types:** Python typing; `mypy --strict`.
- **Style:** black, ruff (E/F/W/I), docstrings on public funcs.
- **Commits:** Conventional Commits (feat:, fix:, perf:, refactor:, test:, docs:).

## 16.4 Troubleshooting

- **CP‑SAT not found:** install OR‑Tools or run `cash verify --engine dp-only`.
- **“Infeasible” after EOD edit:** read the printed certificate; try increasing band or allowing an extra workday; consider removing `--forbid-large-after-day1`.

---

## Hand‑off Summary

- This packet contains: PRD, SRS, Architecture, Data model, Algorithm specs, CLI/API spec, Validation rules, Test plan, Project plan, Dev setup, CI, Risks, and appendices.
- An engineer can start with **Day 1 tasks** (§9), use the **Example plan** (§16.2), and aim for green **acceptance tests** (§8.5).
- The final deliverable is a deterministic CLI with exact math, resume‑from‑any‑day editing, and cross‑verified solutions.
