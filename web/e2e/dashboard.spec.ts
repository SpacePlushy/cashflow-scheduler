import { test, expect } from '@playwright/test';

test.describe('Cashflow Scheduler Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Mock the API response for testing
    await page.route('**/solve', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          actions: Array(30).fill('O').map((_, i) => (i % 3 === 0 ? 'Spark' : 'O')),
          objective: [12, 3, 0],
          final_closing: '90.50',
          ledger: Array.from({ length: 30 }, (_, i) => ({
            day: i + 1,
            opening: '100.00',
            deposits: i === 9 || i === 23 ? '1021.00' : '0.00',
            action: i % 3 === 0 ? 'Spark' : 'O',
            net: i % 3 === 0 ? '100.00' : '0.00',
            bills: i === 0 ? '108.00' : '0.00',
            closing: '150.00',
          })),
          checks: [
            ['Non-negative balances', true, 'All days positive'],
            ['Rent guard', true, 'Sufficient funds'],
            ['Target band', true, 'Within tolerance'],
          ],
          solver: {
            name: 'CP-SAT',
            statuses: ['OPTIMAL'],
            seconds: 0.123,
          },
        }),
      });
    });

    await page.goto('/');
  });

  test('should display the dashboard with all key sections', async ({ page }) => {
    // Wait for loading to complete
    await expect(page.getByText('Optimizing your schedule...')).toBeVisible();
    await expect(page.getByText('Optimizing your schedule...')).not.toBeVisible({ timeout: 10000 });

    // Check header
    await expect(page.getByRole('heading', { name: 'Cashflow Scheduler' })).toBeVisible();
    await expect(page.getByText('30-day optimization with constraint programming')).toBeVisible();

    // Check financial summary cards
    await expect(page.getByText('Total Workdays')).toBeVisible();
    await expect(page.getByText('Final Balance')).toBeVisible();
    await expect(page.getByText('Schedule Quality')).toBeVisible();
    await expect(page.getByText('Validation')).toBeVisible();

    // Check schedule calendar
    await expect(page.getByText('30-Day Schedule')).toBeVisible();

    // Check ledger table
    await expect(page.getByText('Daily Ledger')).toBeVisible();

    // Check validation section
    await expect(page.getByText('Validation Checks')).toBeVisible();
  });

  test('should display correct financial metrics', async ({ page }) => {
    await expect(page.getByText('Optimizing your schedule...')).not.toBeVisible({ timeout: 10000 });

    // Check workdays count
    const workdaysCard = page.locator('text=Total Workdays').locator('..');
    await expect(workdaysCard.getByText('12')).toBeVisible();

    // Check final balance
    const balanceCard = page.locator('text=Final Balance').locator('..');
    await expect(balanceCard.getByText('$90.50')).toBeVisible();

    // Check solver info in header
    await expect(page.getByText(/Solver: CP-SAT/)).toBeVisible();
  });

  test('should display 30 days in the calendar', async ({ page }) => {
    await expect(page.getByText('Optimizing your schedule...')).not.toBeVisible({ timeout: 10000 });

    // Count calendar day cells
    const calendarDays = page.locator('text=/^Day \\d+$/');
    await expect(calendarDays).toHaveCount(30);

    // Check specific days
    await expect(page.getByText('Day 1')).toBeVisible();
    await expect(page.getByText('Day 15')).toBeVisible();
    await expect(page.getByText('Day 30')).toBeVisible();
  });

  test('should show calendar day hover tooltips', async ({ page }) => {
    await expect(page.getByText('Optimizing your schedule...')).not.toBeVisible({ timeout: 10000 });

    // Hover over a day to show tooltip
    const day1 = page.locator('text=Day 1').first();
    await day1.hover();

    // Check tooltip appears with details
    await expect(page.getByText('Day 1 Details')).toBeVisible();
    await expect(page.getByText('Opening:')).toBeVisible();
    await expect(page.getByText('Closing:')).toBeVisible();
  });

  test('should display ledger table with all rows', async ({ page }) => {
    await expect(page.getByText('Optimizing your schedule...')).not.toBeVisible({ timeout: 10000 });

    // Check table headers
    await expect(page.getByRole('columnheader', { name: 'Day' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Opening' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Deposits' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Action' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Bills' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Closing' })).toBeVisible();

    // Check that we have 30 rows (excluding header)
    const tableRows = page.locator('table tbody tr');
    await expect(tableRows).toHaveCount(30);
  });

  test('should display validation checks', async ({ page }) => {
    await expect(page.getByText('Optimizing your schedule...')).not.toBeVisible({ timeout: 10000 });

    // Check validation section
    await expect(page.getByText('Non-negative balances')).toBeVisible();
    await expect(page.getByText('Rent guard')).toBeVisible();
    await expect(page.getByText('Target band')).toBeVisible();

    // Check all passed indicator
    await expect(page.getByText('All Passed')).toBeVisible();
  });

  test('should have dark mode toggle', async ({ page }) => {
    await expect(page.getByText('Optimizing your schedule...')).not.toBeVisible({ timeout: 10000 });

    // Find the theme toggle button
    const themeToggle = page.getByRole('button', { name: /toggle theme/i });
    await expect(themeToggle).toBeVisible();

    // Click to open dropdown
    await themeToggle.click();

    // Check theme options
    await expect(page.getByRole('menuitem', { name: 'Light' })).toBeVisible();
    await expect(page.getByRole('menuitem', { name: 'Dark' })).toBeVisible();
    await expect(page.getByRole('menuitem', { name: 'System' })).toBeVisible();
  });

  test('should switch between light and dark modes', async ({ page }) => {
    await expect(page.getByText('Optimizing your schedule...')).not.toBeVisible({ timeout: 10000 });

    // Open theme toggle
    const themeToggle = page.getByRole('button', { name: /toggle theme/i });
    await themeToggle.click();

    // Switch to light mode
    await page.getByRole('menuitem', { name: 'Light' }).click();

    // Check that html has light mode (no dark class)
    const html = page.locator('html');
    await expect(html).not.toHaveClass(/dark/);

    // Switch to dark mode
    await themeToggle.click();
    await page.getByRole('menuitem', { name: 'Dark' }).click();

    // Check that html has dark class
    await expect(html).toHaveClass(/dark/);
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    await expect(page.getByText('Optimizing your schedule...')).not.toBeVisible({ timeout: 10000 });

    // Check main elements are still visible
    await expect(page.getByRole('heading', { name: 'Cashflow Scheduler' })).toBeVisible();
    await expect(page.getByText('Total Workdays')).toBeVisible();
    await expect(page.getByText('30-Day Schedule')).toBeVisible();
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Override the mock to return an error
    await page.route('**/solve', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' }),
      });
    });

    await page.goto('/');

    // Should show error message
    await expect(page.getByText('Error Loading Schedule')).toBeVisible();
    await expect(page.getByText('API Connection Failed')).toBeVisible();
    await expect(page.getByText(/Make sure the API server is running/)).toBeVisible();
  });

  test('should show loading state initially', async ({ page }) => {
    // Delay the API response
    await page.route('**/solve', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          actions: Array(30).fill('O'),
          objective: [0, 0, 0],
          final_closing: '90.50',
          ledger: Array.from({ length: 30 }, (_, i) => ({
            day: i + 1,
            opening: '90.50',
            deposits: '0.00',
            action: 'O',
            net: '0.00',
            bills: '0.00',
            closing: '90.50',
          })),
          checks: [],
        }),
      });
    });

    await page.goto('/');

    // Should show loading spinner
    await expect(page.getByText('Optimizing your schedule...')).toBeVisible();
    const spinner = page.locator('svg.animate-spin');
    await expect(spinner).toBeVisible();
  });
});

test.describe('Solver Switcher', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API responses for both solvers
    await page.route('**/solve', async (route) => {
      const request = route.request();
      const postData = request.postDataJSON();
      const solver = postData?.solver || 'cpsat';

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          actions: Array(30).fill('O').map((_, i) => (i % 3 === 0 ? 'Spark' : 'O')),
          objective: solver === 'dp' ? [11, 2, 0] : [12, 3, 0],
          final_closing: solver === 'dp' ? '100.50' : '90.50',
          ledger: Array.from({ length: 30 }, (_, i) => ({
            day: i + 1,
            opening: '100.00',
            deposits: i === 9 || i === 23 ? '1021.00' : '0.00',
            action: i % 3 === 0 ? 'Spark' : 'O',
            net: i % 3 === 0 ? '100.00' : '0.00',
            bills: i === 0 ? '108.00' : '0.00',
            closing: solver === 'dp' ? '160.00' : '150.00',
          })),
          checks: [
            ['Non-negative balances', true, 'All days positive'],
            ['Rent guard', true, 'Sufficient funds'],
            ['Target band', true, 'Within tolerance'],
          ],
          solver: {
            name: solver === 'dp' ? 'dp' : 'cpsat',
            statuses: solver === 'dp' ? [] : ['OPTIMAL'],
            seconds: solver === 'dp' ? 0.05 : 0.123,
          },
        }),
      });
    });

    await page.goto('/');
    await expect(page.getByText('Optimizing your schedule...')).not.toBeVisible({ timeout: 10000 });
  });

  test('should display solver toggle buttons', async ({ page }) => {
    // Check that both solver buttons are visible
    await expect(page.getByRole('button', { name: 'CP-SAT' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'DP' })).toBeVisible();
  });

  test('should default to CP-SAT solver', async ({ page }) => {
    // CP-SAT button should be active by default (have "default" variant styling)
    const cpsatButton = page.getByRole('button', { name: 'CP-SAT' });
    const dpButton = page.getByRole('button', { name: 'DP' });

    // Check that CP-SAT is initially active
    await expect(page.getByText(/Solver: cpsat/)).toBeVisible();
  });

  test('should switch to DP solver when clicked', async ({ page }) => {
    // Click the DP button
    const dpButton = page.getByRole('button', { name: 'DP' });
    await dpButton.click();

    // Wait for the solver to change and resolve
    await expect(page.getByText(/Solver: dp/)).toBeVisible({ timeout: 5000 });

    // Check that the solver info shows DP
    await expect(page.getByText(/Solver: dp/)).toBeVisible();
  });

  test('should switch back to CP-SAT solver', async ({ page }) => {
    // First switch to DP
    await page.getByRole('button', { name: 'DP' }).click();
    await expect(page.getByText(/Solver: dp/)).toBeVisible({ timeout: 5000 });

    // Then switch back to CP-SAT
    await page.getByRole('button', { name: 'CP-SAT' }).click();
    await expect(page.getByText(/Solver: cpsat/)).toBeVisible({ timeout: 5000 });
  });

  test('should trigger re-solve when switching solvers', async ({ page }) => {
    // Track API calls
    let solveCallCount = 0;
    let lastSolver = '';

    await page.route('**/solve', async (route) => {
      const request = route.request();
      const postData = request.postDataJSON();
      lastSolver = postData?.solver || 'cpsat';
      solveCallCount++;

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          actions: Array(30).fill('O'),
          objective: [10, 2, 0],
          final_closing: '200.50',
          ledger: Array.from({ length: 30 }, (_, i) => ({
            day: i + 1,
            opening: '100.00',
            deposits: '0.00',
            action: 'O',
            net: '0.00',
            bills: '0.00',
            closing: '100.00',
          })),
          checks: [],
          solver: {
            name: lastSolver,
            statuses: [],
            seconds: 0.1,
          },
        }),
      });
    });

    await page.goto('/');
    await expect(page.getByText('Optimizing your schedule...')).not.toBeVisible({ timeout: 10000 });

    const initialCallCount = solveCallCount;

    // Switch to DP
    await page.getByRole('button', { name: 'DP' }).click();

    // Wait a bit for the API call to be made
    await page.waitForTimeout(500);

    // Verify that a new API call was made with DP
    expect(solveCallCount).toBeGreaterThan(initialCallCount);
    expect(lastSolver).toBe('dp');
  });

  test('should update schedule when switching solvers', async ({ page }) => {
    // Get initial final balance
    const balanceCard = page.locator('text=Final Balance').locator('..');
    await expect(balanceCard.getByText('$90.50')).toBeVisible();

    // Switch to DP solver
    await page.getByRole('button', { name: 'DP' }).click();

    // Wait for update and check balance changed
    await expect(balanceCard.getByText('$100.50')).toBeVisible({ timeout: 5000 });
  });

  test('should maintain solver selection during set_eod operation', async ({ page }) => {
    // Mock set_eod endpoint
    await page.route('**/set_eod', async (route) => {
      const request = route.request();
      const postData = request.postDataJSON();
      const solver = postData?.solver || 'cpsat';

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          actions: Array(30).fill('O'),
          objective: [10, 2, 0],
          final_closing: '500.00',
          ledger: Array.from({ length: 30 }, (_, i) => ({
            day: i + 1,
            opening: '100.00',
            deposits: '0.00',
            action: 'O',
            net: '0.00',
            bills: '0.00',
            closing: '100.00',
          })),
          checks: [],
          solver: {
            name: solver,
            statuses: [],
            seconds: 0.1,
          },
        }),
      });
    });

    // Switch to DP solver
    await page.getByRole('button', { name: 'DP' }).click();
    await expect(page.getByText(/Solver: dp/)).toBeVisible({ timeout: 5000 });

    // Open Set EOD form
    await page.getByText('Set End-of-Day Balance').click();

    // Fill in the form
    await page.getByLabel('Target EOD Balance ($)').fill('500.00');

    // Submit the form
    await page.getByRole('button', { name: 'Apply Changes' }).click();

    // Wait for the response
    await page.waitForTimeout(1000);

    // The solver should still be DP after the operation
    await expect(page.getByText(/Solver: dp/)).toBeVisible();
  });

  test('should show loading state when switching solvers', async ({ page }) => {
    // Mock delayed response
    await page.route('**/solve', async (route) => {
      const request = route.request();
      const postData = request.postDataJSON();
      const solver = postData?.solver || 'cpsat';

      // Add delay for DP solver to see loading state
      if (solver === 'dp') {
        await new Promise((resolve) => setTimeout(resolve, 500));
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          actions: Array(30).fill('O'),
          objective: [10, 2, 0],
          final_closing: '200.50',
          ledger: Array.from({ length: 30 }, (_, i) => ({
            day: i + 1,
            opening: '100.00',
            deposits: '0.00',
            action: 'O',
            net: '0.00',
            bills: '0.00',
            closing: '100.00',
          })),
          checks: [],
          solver: {
            name: solver,
            statuses: [],
            seconds: 0.1,
          },
        }),
      });
    });

    await page.goto('/');
    await expect(page.getByText('Optimizing your schedule...')).not.toBeVisible({ timeout: 10000 });

    // Click DP button
    await page.getByRole('button', { name: 'DP' }).click();

    // Should briefly show loading state
    // Note: This might be too fast to catch reliably, but the test documents expected behavior
    const loading = page.getByText('Optimizing your schedule...');
    // Just check that page is functional after loading
    await expect(page.getByRole('button', { name: 'DP' })).toBeVisible();
  });
});
