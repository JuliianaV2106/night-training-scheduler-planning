import { test, expect } from '@playwright/test';
import { SchedulerDashboardPage } from './pages/SchedulerDashboardPage';

/**
 * Flow E: Playwright E2E with Page Object Model & Forensic Visual Traces
 * Module 9: Night Training Scheduler
 * Story 9.6: Fast-Forward 24-Hour Time-Lapse Scheduler Status Board E2E
 *
 * BDD Scenario:
 *   Scenario: Operator time-warps cluster and observes automated night window execution
 *     Given the operator is on the Scheduler Kanban Board at simulated time "14:00" with 5 queued jobs
 *     When the operator clicks "Fast-Forward to 22:00"
 *     Then the clock displays "22:00" and the 5 job cards transition from "Queued" to "Running"
 *     When the operator advances time to "06:00"
 *     Then cards transition to "Completed" or "Evicted" and node cards show "IDLE"
 */
test.describe('Story 9.6: Fast-Forward 24-Hour Time-Lapse Scheduler Status Board E2E', () => {
  test('Operator time-warps cluster and observes automated night window execution', async ({ page }) => {
    const dashboard = new SchedulerDashboardPage(page);

    // Given the operator is on the Scheduler Kanban Board at simulated time "14:00" with 5 queued jobs
    await dashboard.seedBoardWithQueuedJobs(5);
    await dashboard.assertSimulatedClockDisplays('14:00');
    await dashboard.assertColumnCounts(5, 0, 0);

    // Verify speed multiplier controls (1x, 10x, 60x) and time scrubber visibility via POM
    await expect(dashboard.timeScrubber).toBeVisible();
    await dashboard.selectSpeedMultiplier(60);
    await expect(dashboard.speed60xButton).toHaveClass(/active/);

    // When the operator clicks "Fast-Forward to 22:00"
    await dashboard.clickFastForwardTo2200();

    // Then the clock displays "22:00" and the 5 job cards transition from "Queued" to "Running"
    await dashboard.assertSimulatedClockDisplays('22:00');
    await dashboard.assertColumnCounts(0, 5, 0);

    // When the operator advances time to "06:00"
    await dashboard.clickAdvanceTo0600();

    // Then cards transition to "Completed" or "Evicted" and node cards show "IDLE"
    await dashboard.assertSimulatedClockDisplays('06:00');
    await dashboard.assertColumnCounts(0, 0, 5);
    await dashboard.assertAllNodesIdle();
  });
});
