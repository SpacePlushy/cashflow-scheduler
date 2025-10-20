# Cash CLI Tool Documentation

The `cash` command-line tool is a convenience wrapper for the cashflow scheduler Python CLI. It automatically activates the virtual environment and provides easy access to all scheduling commands.

## Overview

The cash CLI tool helps you:
- Solve 30-day cash-flow schedules that meet financial constraints
- Adjust schedules by locking specific days
- Export schedules in multiple formats
- Verify solutions using different solver algorithms
- Generate visual calendar representations

## Installation

The `cash` script should be made executable after cloning the repository:

```bash
chmod +x cash
```

Ensure your Python virtual environment is set up:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Basic Usage

```bash
./cash [COMMAND] [OPTIONS] [ARGUMENTS]
```

All commands operate on a plan file (defaults to `plan.json` in the current directory).

## Commands

### `solve` - Generate Optimal Schedule

Finds the optimal work schedule that minimizes workdays while maintaining positive daily balances.

**Usage:**
```bash
./cash solve [PLAN_PATH] [OPTIONS]
```

**Options:**
- `--solver TEXT` - Choose solver backend: `cpsat` (default) or `dp`
  - `cpsat`: CP-SAT constraint programming solver (requires OR-Tools)
  - `dp`: Dynamic programming solver (always available)

**Examples:**
```bash
# Solve using default plan.json with CP-SAT
./cash solve

# Solve specific plan file
./cash solve my_plan.json

# Use DP solver instead
./cash solve --solver dp

# Solve different plan with DP
./cash solve plans/october.json --solver dp
```

**Output:**
- Displays the 30-day schedule with work/off assignments
- Shows daily ledger (opening balance, deposits, bills, closing balance)
- Reports validation results (non-negative balances, rent guard, target band)
- Shows objective metrics: (total_workdays, abs_diff_from_target)

---

### `show` - Display Schedule Without Validation

Shows the schedule output without running full validation checks. Useful for quick previews.

**Usage:**
```bash
./cash show [PLAN_PATH] [OPTIONS]
```

**Options:**
- `--solver TEXT` - Choose solver backend: `cpsat` (default) or `dp`

**Examples:**
```bash
# Quick preview of schedule
./cash show

# Preview with specific solver
./cash show --solver dp
```

---

### `set-eod` - Lock Days and Re-solve

Adjusts the plan to hit a specific end-of-day balance on a given day, locks days 1 through that day, and re-solves the remaining days.

**Usage:**
```bash
./cash set-eod DAY EOD_AMOUNT [PLAN_PATH] [OPTIONS]
```

**Arguments:**
- `DAY` (required) - Day index (1-30) to set the end-of-day balance for
- `EOD_AMOUNT` (required) - Desired end-of-day balance in dollars (e.g., 167.00)
- `PLAN_PATH` (optional) - Path to plan file (defaults to `plan.json`)

**Options:**
- `--save-plan TEXT` - Path to save the updated plan JSON with locked days
- `--calendar` - Also generate a calendar PNG to `~/Downloads/cashflow_calendar.png`
- `--solver TEXT` - Choose solver backend: `cpsat` (default) or `dp`

**Examples:**
```bash
# Set day 20 to close at $167.00
./cash set-eod 20 167.00

# Set day 15 EOD and save updated plan
./cash set-eod 15 250.50 --save-plan locked_plan.json

# Set EOD with calendar generation
./cash set-eod 10 150.00 --calendar

# Use specific plan and DP solver
./cash set-eod 20 167.00 my_plan.json --solver dp
```

**How it works:**
1. Solves the original plan
2. Locks actions for days 1 through DAY
3. Adds a manual adjustment on DAY to hit the target EOD balance
4. Re-solves days (DAY+1) through 30
5. Validates the new schedule

---

### `export` - Export Schedule to File

Exports the solved schedule to various formats for documentation or analysis.

**Usage:**
```bash
./cash export [PLAN_PATH] [OPTIONS]
```

**Options:**
- `--format TEXT` - Output format: `md` (markdown), `csv`, or `json` (default: `md`)
- `--out TEXT` - Output file path (default: `schedule.md`)
- `--solver TEXT` - Choose solver backend: `cpsat` (default) or `dp`

**Examples:**
```bash
# Export to markdown (default)
./cash export

# Export to CSV
./cash export --format csv --out my_schedule.csv

# Export to JSON with custom output path
./cash export --format json --out results/october.json

# Export specific plan to markdown
./cash export plans/november.json --out docs/november.md
```

**Output Formats:**
- **Markdown (md)**: Human-readable table with daily ledger and summary
- **CSV**: Comma-separated values for spreadsheet import
- **JSON**: Machine-readable format with full schedule data

---

### `verify` - Cross-Verify Solver Results

Runs both DP and CP-SAT solvers and compares their results to ensure correctness.

**Usage:**
```bash
./cash verify [PLAN_PATH]
```

**Examples:**
```bash
# Verify default plan
./cash verify

# Verify specific plan
./cash verify my_plan.json
```

**Output:**
- Compares objectives from both solvers
- Reports whether solutions match
- Shows differences in actions if solutions differ
- Useful for debugging and validating solver implementations

**Note:** Requires OR-Tools to be installed for CP-SAT solver.

---

### `calendar` - Generate Visual Calendar

Creates a high-resolution PNG calendar visualization of the schedule, suitable for desktop wallpapers.

**Usage:**
```bash
./cash calendar [PLAN_PATH] [OPTIONS]
```

**Options:**
- `--out TEXT` - Output PNG path (default: `~/Downloads/cashflow_calendar.png`)
- `--width INTEGER` - Image width in pixels (default: 3840)
- `--height INTEGER` - Image height in pixels (default: 2160)
- `--theme TEXT` - Color theme: `dark` or `light` (default: `dark`)
- `--4k` - Force 3840x2160 resolution (overrides --width and --height)

**Examples:**
```bash
# Generate 4K dark theme calendar
./cash calendar

# Generate light theme calendar
./cash calendar --theme light

# Custom resolution
./cash calendar --width 1920 --height 1080

# Custom output path
./cash calendar --out ~/Desktop/my_schedule.png

# 4K with custom output
./cash calendar --4k --out wallpapers/october.png
```

**Output:**
- High-resolution PNG with daily schedule grid
- Color-coded work/off days
- Shows balances, deposits, and bills
- Designed for visual planning and desktop backgrounds

---

## Plan File Format

The cash CLI operates on JSON plan files with the following structure:

```json
{
  "start_balance": 90.50,
  "target_end": 490.50,
  "band": 25.0,
  "rent_guard": 1636.0,
  "deposits": [
    {"day": 11, "amount": 1021.0}
  ],
  "bills": [
    {"day": 1, "name": "Auto Insurance", "amount": 177.0},
    {"day": 30, "name": "Rent", "amount": 1636.0}
  ],
  "actions": [null, null, ...],
  "manual_adjustments": [
    {"day": 15, "amount": -50.0, "note": "correction"}
  ]
}
```

### Key Fields:
- `start_balance`: Starting cash balance (Day 0 closing)
- `target_end`: Desired ending balance on Day 30
- `band`: Acceptable deviation from target (±band)
- `rent_guard`: Minimum balance required before Day 30 rent payment
- `deposits`: Income items by day
- `bills`: Expenses by day with descriptions
- `actions`: Pre-locked actions (null = solver decides, "O" = off, "Spark" = work)
- `manual_adjustments`: One-time cash corrections

---

## Understanding the Output

### Schedule Display

```
Day Action  Opening  Deposits  Net  Bills  Closing
  1   Spark   $90.50    $0.00  $100.00  $177.00   $13.50
  2   O       $13.50    $0.00    $0.00    $0.00   $13.50
  3   Spark   $13.50    $0.00  $100.00    $0.00  $113.50
...
```

- **Day**: Day number (1-30)
- **Action**: Work type ("Spark" = $100 earned, "O" = off day)
- **Opening**: Balance at start of day
- **Deposits**: Scheduled income for the day
- **Net**: Earnings from work action
- **Bills**: Expenses due this day
- **Closing**: End-of-day balance (must be ≥ $0)

### Objective Metrics

The solver optimizes lexicographically:
1. **Minimize total workdays**: Fewer days worked is better
2. **Minimize |diff from target|**: Get as close to target balance as possible

Format: `Objective: (workdays, abs_diff_cents)`

Example: `(14, 0)` means 14 workdays, $0.00 difference from target

### Validation Checks

- **Non-Negative Closings**: All daily closing balances ≥ $0
- **Rent Guard**: Day 30 balance before rent ≥ rent_guard threshold
- **Target Band**: Final closing balance within [target - band, target + band]

---

## Solver Comparison

### CP-SAT (Default)
- Uses Google OR-Tools constraint programming
- Guarantees optimal solutions
- Slower for complex plans
- Requires OR-Tools installation
- Best for verification and exact solutions

### DP (Dynamic Programming)
- Pure Python implementation
- Always available (no external dependencies)
- Faster for most practical plans
- Optimizes with state space pruning
- Best for production use and embedded scenarios

**Recommendation**: Use CP-SAT for verification, DP for daily use.

---

## Common Workflows

### Daily Planning
```bash
# Solve current plan
./cash solve

# Export to markdown for review
./cash export --out today.md
```

### Adjusting Mid-Month
```bash
# Lock first 15 days at target balance
./cash set-eod 15 250.00 --save-plan updated_plan.json

# Re-solve with locked days
./cash solve updated_plan.json
```

### Creating Documentation
```bash
# Export to multiple formats
./cash export --format md --out schedule.md
./cash export --format csv --out schedule.csv
./cash export --format json --out schedule.json

# Generate visual calendar
./cash calendar --theme light --out schedule.png
```

### Debugging/Verification
```bash
# Cross-check both solvers
./cash verify

# Compare solver performance
time ./cash solve --solver dp
time ./cash solve --solver cpsat
```

---

## Troubleshooting

### "OR-Tools not installed" Error
If using `--solver cpsat` and getting OR-Tools errors:
```bash
pip install ortools
```

Or use the DP solver instead:
```bash
./cash solve --solver dp
```

### "Virtual environment not found" Error
Ensure the virtual environment is created:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Permission Denied
Make sure the cash script is executable:
```bash
chmod +x cash
```

### Infeasible Plan
If the solver reports "INFEASIBLE":
- Check that deposits are sufficient for bills
- Verify rent_guard threshold is achievable
- Ensure target_end is realistic given constraints
- Try widening the band tolerance

---

## Advanced Usage

### Scripting with Cash

```bash
#!/bin/bash
# Monthly planning script

for month in plans/*.json; do
  echo "Solving $month..."
  ./cash solve "$month" --solver dp
  ./cash export "$month" --format md --out "results/$(basename $month .json).md"
done
```

### Batch Verification

```bash
# Verify all plans in a directory
for plan in plans/*.json; do
  echo "Verifying $plan..."
  ./cash verify "$plan" || echo "FAILED: $plan"
done
```

### Calendar Generation Pipeline

```bash
# Generate calendars for multiple themes
./cash calendar --theme dark --out calendar_dark.png
./cash calendar --theme light --out calendar_light.png
```

---

## Related Documentation

- [QUICKSTART.txt](QUICKSTART.txt) - Quick start guide for the entire system
- [CPSAT-README.md](CPSAT-README.md) - CP-SAT solver deep dive
- [CLAUDE.md](CLAUDE.md) - Full project documentation
- [schedule.md](schedule.md) - Example schedule output

---

## Getting Help

```bash
# General help
./cash --help

# Command-specific help
./cash solve --help
./cash set-eod --help
./cash export --help
./cash verify --help
./cash calendar --help
```

For issues or questions, refer to the project repository or main documentation.
