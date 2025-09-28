# Cashflow Scheduler – Shadcn UI Redesign Plan

## Objectives
- Rebuild the Next.js front-end (`web/`) using shadcn/ui while preserving solver/validator workflows.
- Establish a reusable design system (tokens, components, patterns) aligned with product brand.
- Improve onboarding and comprehension for cashflow planning through clearer content and interaction flows.
- Maintain accessibility, responsiveness, and performance benchmarks while enabling future feature velocity.

## Scope & Constraints
- In scope: visual redesign, navigation architecture, shared layout primitives, state management adjustments, UI copy refresh, and component QA.
- Out of scope: solver logic changes, API surface modifications beyond UI needs, and non-web clients.
- Tech stack constraints: Next.js app router, Tailwind CSS, shadcn/ui registry, integer-cent money rules, existing API contracts (`/solve`, `/set_eod`, `/export`).

## Foundation Setup
1. Baseline shadcn integration
   - Run `npx shadcn@latest init` within `web/`.
   - Configure registry directory (`components/ui`) and alias for imports.
   - Audit Tailwind config for missing plugins (typography, animate) and enable `tailwind.config.ts` tokens.
2. Design tokens & theming
   - Define base color palette (light/dark) reflecting brand.
   - Set typography scale, spacing ramp, radii, shadows, motion durations.
   - Document token usage for Figma ↔ code parity.
3. Global providers & layout shell
   - Add `ThemeProvider`, `TooltipProvider`, and toaster in root layout.
   - Implement responsive page chrome (sidebar + top nav) using shadcn `Sidebar`, `Sheet`, `Breadcrumb`, `UserNav` patterns.

## Information Architecture
- Confirm sitemap: Dashboard → Plan Builder → History/Exports → Verification.
- Map existing routes to new structure, consolidating redundant pages.
- Introduce guard rails for unauthenticated flows (future login) but keep current assumption of trusted local use.

## Component Strategy
- Catalogue current UI elements; document replacement using shadcn primitives:
  - Buttons, inputs, selects, checkbox/radio → `Button`, `Input`, `Select`, `Checkbox`, `RadioGroup`.
  - Table-like schedule visualization → `Table`, `ScrollArea`, `Badge` for statuses.
  - Dialog flows for plan editing → `Dialog`, `Form`, `Tabs` (if multi-step).
  - Notifications → `Toast` + `useToast` hook.
  - Loading & empty states → `Skeleton`, `Empty` pattern with icons.
- Create domain components:
  - `PlanSummaryCard` for net cash timeline metrics.
  - `DayScheduleList` to show daily obligations & shifts.
  - `VerificationStatus` widget combining DP + CP-SAT results.
  - `EodOverrideForm` wrapping `/set_eod` interactions with validation.
- Establish barrel exports and story files (Storybook or Ladle) for each domain component.

## Data & State Management
- Align Next.js server actions or API routes with existing FastAPI endpoints (continue fetching via REST).
- Introduce lightweight client-side store (Zustand or React context) for plan state and solver responses.
- Implement optimistic updates for plan adjustments; fallback to server data on failure.
- Ensure integer-cent handling across components (formatters in `cashflow/core/money.py` mirrored via shared utility exported to web bundle or reimplemented carefully without floats).

## Content & UX Enhancements
- Refresh copy to explain DP vs CP-SAT verification, constraints, and next steps for users.
- Provide inline help via `HoverCard` or `Popover` for complex fields (e.g., shift nets, end-of-day overrides).
- Add guided empty states and first-run prompts to orient new users.
- Improve responsive design: stack panels on mobile, ensure interactive elements meet touch targets.

## Accessibility & Performance
- Enforce keyboard navigation and proper aria labeling (shadcn components ship with Radix primitives).
- Run automated checks (axe, Lighthouse) per milestone.
- Lazy-load heavy visualizations or advanced tables; prefer streaming for large plan exports.
- Monitor bundle size using Next.js analyzer; tree-shake unused icons/components.

## Phased Delivery
1. **Phase 0 – Planning & Tokens (Week 1)**
   - Finalize sitemap, wireframes, token definitions, and component list.
   - Set up shadcn registry and update Tailwind + global providers.
2. **Phase 1 – Application Shell (Week 2)**
   - Implement global layout, navigation, theme toggle, and basic dashboard skeleton.
   - Migrate fundamental primitives (buttons, inputs, typography).
3. **Phase 2 – Core Workflows (Weeks 3-4)**
   - Rebuild Plan Builder page with new components and optimistic interactions.
   - Integrate verification view and export workflows.
   - Ensure API error handling and toasts.
4. **Phase 3 – Enhancements & Polish (Week 5)**
   - Add onboarding flows, contextual help, responsive refinements.
   - Run accessibility/performance audits and address findings.
5. **Phase 4 – Launch Prep (Week 6)**
   - Cross-browser QA, stakeholder review, documentation updates (README, AGENTS, product notes).
   - Prepare release notes and deploy strategy.

## Testing & QA Plan
- Unit tests for utility functions (formatters, state selectors).
- Component visual regression coverage via Storybook snapshots or Playwright component testing.
- End-to-end smoke tests covering solve → verify → export loop.
- Manual regression checklist for plan import/export and EOD override flows.
- Maintain `make test`, `make lint`, `make type`, and `make verify` green before merges.

## Risks & Mitigation
- **Design drift vs solver behavior**: keep validator rules exposed in UI copy; pair with backend engineers.
- **Accessibility regressions**: integrate automated linting (`eslint-plugin-jsx-a11y`), schedule manual keyboard testing.
- **Performance regressions**: leverage Next.js dynamic imports, monitor `web/.next` bundle stats.
- **API contract changes**: document any required adjustments and coordinate with FastAPI team before implementation.

## Next Steps
1. Socialize plan with product/design stakeholders for sign-off.
2. Create detailed component checklist and break into GitHub issues.
3. Begin Phase 0 tasks on `redesign/shadcn-ui` branch, landing tokens and registry setup.
