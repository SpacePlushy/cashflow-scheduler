import { test, expect } from '@playwright/test';

const solverHeading = 'Solver Output';

test('user can solve default plan and see solver diagnostics', async ({ page }) => {
  await page.goto('/');

  const solveButton = page.getByRole('button', { name: /Solve Schedule/i });
  await expect(solveButton).toBeEnabled({ timeout: 20_000 });
  await expect(page.getByText(/Cashflow Scheduler/i)).toBeVisible();

  await solveButton.click();

  await expect(page.getByText(solverHeading)).toBeVisible();
  await expect(page.getByText(/Backend: CPSAT/i)).toBeVisible();
  await expect(page.getByRole('table')).toBeVisible();

  const firstRow = page.locator('table tbody tr').first();
  await expect(firstRow).toContainText('1');
  await expect(firstRow).toContainText('L');

  const solverMetadata = page.getByText(/Stage statuses/i);
  await expect(solverMetadata).toBeVisible();
});

test('user edits plan inputs and JSON before solving', async ({ page }) => {
  await page.goto('/');

  const startInput = page.getByLabel('Starting Balance ($)');
  await startInput.fill('250');

  await page.getByRole('button', { name: /Add Deposit/i }).click();
  const depositsSection = page.locator('section', { hasText: 'Deposits' }).first();
  await depositsSection.getByLabel('Day').last().fill('15');
  await depositsSection.getByLabel('Amount ($)').last().fill('123.45');

  const planJson = page.locator('textarea');
  await expect(planJson).toContainText('"start_balance": 250');
  await expect(planJson).toContainText('"day": 15');

  const parsed = JSON.parse(await planJson.inputValue());
  parsed.start_balance = 300;
  const updatedJson = JSON.stringify(parsed, null, 2);
  await planJson.fill(updatedJson);
  await page.getByRole('button', { name: /Apply Changes/i }).click();

  await expect(startInput).toHaveValue('300');

  const solveButton = page.getByRole('button', { name: /Solve Schedule/i });
  await expect(solveButton).toBeEnabled();
  await solveButton.click();

  const firstRow = page.locator('table tbody tr').first();
  await expect(firstRow).toContainText('$300.00');
  await expect(page.getByText(/Backend: CPSAT/i)).toBeVisible();
});

test('user updates bill amount and sees updated ledger', async ({ page }) => {
  await page.goto('/');

  const billsSection = page.locator('section', { hasText: 'Bills' }).first();
  const firstBillAmount = billsSection.getByLabel('Amount ($)').first();
  await firstBillAmount.fill('150');

  const solveButton = page.getByRole('button', { name: /Solve Schedule/i });
  await expect(solveButton).toBeEnabled();
  await solveButton.click();

  const day1Row = page.locator('table tbody tr').first();
  await expect(day1Row.locator('td').nth(5)).toHaveText('$150.00');
  await expect(page.getByText(/Backend: CPSAT/i)).toBeVisible();
});

test('user locks a shift via JSON and sees action applied', async ({ page }) => {
  await page.goto('/');

  const planJson = page.locator('textarea');
  const planData = JSON.parse(await planJson.inputValue());
  planData.actions[1] = 'SS';
  const updatedJson = JSON.stringify(planData, null, 2);
  await planJson.fill(updatedJson);
  await page.getByRole('button', { name: /Apply Changes/i }).click();

  const solveButton = page.getByRole('button', { name: /Solve Schedule/i });
  await expect(solveButton).toBeEnabled();
  await solveButton.click();

  const day2Row = page.locator('table tbody tr').nth(1);
  await expect(day2Row.locator('td').nth(3)).toHaveText('SS');
  await expect(page.getByText(/Backend: CPSAT/i)).toBeVisible();
});
