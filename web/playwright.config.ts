import { defineConfig } from '@playwright/test';

const reuse = process.env.CI ? false : true;

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL: 'http://localhost:3000',
    headless: true,
  },
  webServer: [
    {
      command: 'bash -lc "cd .. && python3 -m uvicorn api.index:app --host 127.0.0.1 --port 8000"',
      port: 8000,
      reuseExistingServer: reuse,
      timeout: 120_000,
    },
    {
      command:
        'bash -lc "npm run build && NEXT_PUBLIC_SOLVER_API_URL=http://127.0.0.1:8000 npm run start"',
      port: 3000,
      reuseExistingServer: reuse,
      timeout: 180_000,
    },
  ],
});
