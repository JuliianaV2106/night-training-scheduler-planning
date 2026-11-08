import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E Configuration for Module 9: Night Training Scheduler (Flow E)
 * - Forensic Visual Tracing enabled (`trace: 'on-first-retry'` + `'on'` to guarantee trace.zip generation)
 * - Zero hardcoded timeouts (`waitForTimeout` forbidden)
 */
export default defineConfig({
  testDir: './test/e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 1,
  workers: 1,
  reporter: [['list'], ['html', { open: 'never', outputFolder: 'playwright-report' }]],
  outputDir: './test-results',
  use: {
    baseURL: process.env.BASE_URL || 'http://127.0.0.1:8000',
    trace: 'on',
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: 'wsl -e bash -c "PYTHONPATH=.:planning/detailed-design/schemas .venv/bin/uvicorn api.app:app --host 127.0.0.1 --port 8000"',
    url: 'http://127.0.0.1:8000/health',
    reuseExistingServer: true,
    timeout: 30000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
