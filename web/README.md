# Cashflow Scheduler - Modern Web Frontend

A beautiful, dark-mode-first Next.js 15 application for visualizing and optimizing 30-day cash flow schedules using constraint programming.

## Features

### UI Components

- **Financial Summary Dashboard** - Key metrics at a glance:
  - Total workdays required
  - Final balance with target diff
  - Schedule quality (back-to-back work pairs)
  - Validation status

- **30-Day Calendar Grid** - Interactive schedule visualization:
  - Color-coded work/off days
  - Balance indicators with color coding
  - Deposit badges
  - Detailed hover tooltips showing daily breakdowns

- **Daily Ledger Table** - Complete financial breakdown:
  - Scrollable table with 30-day history
  - Color-coded balances and transactions
  - Bills and deposits highlighted

- **Validation Checks** - Real-time constraint verification

### Modern Tech Stack

- **Next.js 15** with App Router and React 19
- **Tailwind CSS v4** for utility-first styling
- **shadcn/ui** for beautiful, accessible components
- **next-themes** for seamless dark/light mode switching
- **TypeScript** for type safety
- **Playwright** for comprehensive E2E testing

## Getting Started

```bash
npm install
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000)

## Testing

```bash
npm run test:e2e        # Run E2E tests
npm run test:e2e:ui     # Run with Playwright UI
```

## License

Same as parent project
