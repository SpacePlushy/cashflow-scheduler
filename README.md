# Cashflow Scheduler

A 30-day cash-flow scheduler that optimizes work schedules to meet financial constraints using constraint programming (CP-SAT via OR-Tools) and dynamic programming (DP).

## Quick Start

```bash
# Setup
make setup-dev      # Install package in editable mode

# Solve a plan
./cash solve plan.json

# Run web interface
make web-dev        # Start dev server at http://localhost:3000

# Run tests
make test
```

## Project Structure

```
.
├── cashflow/               # Core Python package
│   ├── core/              # Domain models and validation
│   ├── engines/           # DP and CP-SAT solvers
│   ├── io/               # I/O, rendering, and data persistence
│   ├── cli.py            # CLI entry point
│   └── tests/            # Comprehensive test suite
│
├── api/                   # FastAPI serverless API
│   └── index.py          # Main API endpoints
│
├── verify_service/        # Standalone verification service
│   └── app.py           # Cross-verification endpoint
│
├── web/                  # Next.js 15 frontend
│   ├── src/
│   │   ├── app/         # App router pages
│   │   ├── components/  # React components
│   │   └── lib/        # Types and utilities
│   └── package.json
│
├── scripts/              # Development utilities
│   ├── dev_run_all.sh   # Run all services locally
│   └── smoke.mjs        # Integration tests
│
├── docs/                 # Documentation
│   ├── development/     # Development guides
│   ├── deployment/      # Deployment instructions
│   ├── security/        # Security documentation
│   └── project-phases/  # Project history
│
├── plan.json            # Example plan file
├── requirements.txt     # Python dependencies
├── Makefile            # Common development tasks
└── cash                # CLI wrapper script
```

## Key Features

- **Dual Solver Architecture**: Dynamic Programming (primary) and CP-SAT (verification)
- **Constraint Enforcement**: Maintains positive daily balances with financial guardrails
- **Web Interface**: Modern React frontend with real-time solving
- **CLI Tool**: Full-featured command-line interface
- **API Service**: RESTful API for integration

## Core Concepts

### Plan
Defines financial constraints and schedule requirements:
- Start/target balances
- Daily bills and deposits
- Rent guard threshold
- Band tolerance for final balance

### Schedule
Optimized 30-day work schedule that:
- Minimizes total workdays
- Spreads work evenly (minimizes back-to-back pairs)
- Maintains positive daily balances
- Meets target end balance

### Constraints
- **Day 1**: Always work (business rule)
- **Off-Off Window**: At least one consecutive pair of off-days every 7 days
- **Daily Balance**: Never negative after bills
- **Rent Guard**: Day 30 pre-rent balance must exceed threshold
- **Final Band**: Closing balance within target ± band

## Development

```bash
# Code quality
make lint          # Run linters
make format        # Auto-format code
make type          # Type checking

# Testing
pytest -v          # Verbose tests
pytest -k test_name  # Specific test

# Local development
scripts/dev_run_all.sh  # Start all services

# Documentation
# See docs/development/QUICKSTART.txt for detailed setup
```

## CLI Usage

```bash
# Basic solving
cash solve plan.json

# Choose solver
cash solve --solver dp plan.json     # Dynamic programming
cash solve --solver cpsat plan.json  # CP-SAT

# Lock days and re-solve
cash set-eod 10 500.00 plan.json    # Lock days 1-10, set balance to $500

# Export results
cash export plan.json --format md    # Markdown
cash export plan.json --format csv   # CSV

# Generate calendar visualization
cash calendar plan.json              # PNG calendar
```

## API Endpoints

- `POST /solve` - Solve a plan
- `POST /set_eod` - Lock days and re-solve
- `POST /export` - Export results
- `POST /verify` - Cross-verify solvers

## Deployment

- **Frontend**: Vercel (Next.js)
- **API**: Vercel Serverless Functions
- **Verify Service**: Fly.io (Docker)

See `docs/deployment/` for detailed deployment instructions.

## Testing

The project includes comprehensive testing:
- Unit tests for core logic
- Property-based tests with Hypothesis
- Integration tests for API/UI
- Regression tests for known scenarios

## License

[Add your license here]

## Contributing

[Add contribution guidelines]