import { type Locator, type Page, expect } from '@playwright/test';

/**
 * Page Object Model (POM) for Story 9.6:
 * Fast-Forward 24-Hour Time-Lapse Scheduler Status Board E2E
 * Web View: `/admin/scheduler-board`
 *
 * Encapsulates all DOM locators and user interactions so test specs read
 * like human user stories without raw CSS selector coupling.
 */
export class SchedulerDashboardPage {
  readonly page: Page;
  readonly clusterClock: Locator;
  readonly timeScrubber: Locator;
  readonly speed1xButton: Locator;
  readonly speed10xButton: Locator;
  readonly speed60xButton: Locator;
  readonly fastForwardTo2200Button: Locator;
  readonly advanceTo0600Button: Locator;
  readonly queuedColumn: Locator;
  readonly runningColumn: Locator;
  readonly completedColumn: Locator;
  readonly queuedCards: Locator;
  readonly runningCards: Locator;
  readonly completedOrEvictedCards: Locator;
  readonly nodeCards: Locator;
  readonly nodeStatusBadges: Locator;

  constructor(page: Page) {
    this.page = page;
    this.clusterClock = page.getByTestId('cluster-clock');
    this.timeScrubber = page.getByTestId('time-scrubber');
    this.speed1xButton = page.getByTestId('speed-1x');
    this.speed10xButton = page.getByTestId('speed-10x');
    this.speed60xButton = page.getByTestId('speed-60x');
    this.fastForwardTo2200Button = page.getByRole('button', { name: 'Fast-Forward to 22:00' });
    this.advanceTo0600Button = page.getByRole('button', { name: 'Advance to 06:00' });

    this.queuedColumn = page.getByTestId('column-queued');
    this.runningColumn = page.getByTestId('column-running');
    this.completedColumn = page.getByTestId('column-completed');

    this.queuedCards = this.queuedColumn.getByTestId('job-card');
    this.runningCards = this.runningColumn.getByTestId('job-card');
    this.completedOrEvictedCards = this.completedColumn.getByTestId('job-card');

    this.nodeCards = page.getByTestId('node-card');
    this.nodeStatusBadges = page.getByTestId('node-status-badge');
  }

  async goto(): Promise<void> {
    await this.page.goto('/admin/scheduler-board');
  }

  async seedBoardWithQueuedJobs(queuedJobsCount: number = 5): Promise<void> {
    await this.page.request.post('/api/v1/simulation/seed-board', {
      data: {
        initial_time: '2026-10-18T14:00:00-05:00',
        queued_jobs_count: queuedJobsCount,
      },
    });
    await this.goto();
  }

  async selectSpeedMultiplier(multiplier: 1 | 10 | 60): Promise<void> {
    if (multiplier === 1) await this.speed1xButton.click();
    if (multiplier === 10) await this.speed10xButton.click();
    if (multiplier === 60) await this.speed60xButton.click();
  }

  async clickFastForwardTo2200(): Promise<void> {
    await this.fastForwardTo2200Button.click();
  }

  async clickAdvanceTo0600(): Promise<void> {
    await this.advanceTo0600Button.click();
  }

  async assertSimulatedClockDisplays(expectedTime: string): Promise<void> {
    await expect(this.clusterClock).toHaveText(expectedTime);
  }

  async assertColumnCounts(queued: number, running: number, completedOrEvicted: number): Promise<void> {
    await expect(this.queuedCards).toHaveCount(queued);
    await expect(this.runningCards).toHaveCount(running);
    await expect(this.completedOrEvictedCards).toHaveCount(completedOrEvicted);
  }

  async assertAllNodesIdle(): Promise<void> {
    await expect(this.nodeCards).toHaveCount(32);
    const badges = await this.nodeStatusBadges.all();
    for (const badge of badges) {
      await expect(badge).toHaveText('IDLE');
    }
  }
}
