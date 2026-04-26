import { expect, test } from '@playwright/test';

test('history markdown rendering does not execute raw HTML payloads', async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem(
      'auth_token',
      JSON.stringify({
        access_token: 'fake-token',
        token_type: 'bearer',
        user: { id: 1, username: 'security-tester', is_admin: true },
      })
    );
    (window as Window & { __xssExecuted?: number }).__xssExecuted = 0;
  });

  const jobSummary = {
    job_id: 1,
    file_name: 'unsafe.md',
    file_type: 'document',
    status: 'success',
    provider: 'docling-local',
    model: 'transcription',
    schema_name: 'Transcription',
    created_at: new Date().toISOString(),
    processing_method: 'transcription',
  };

  const jobDetail = {
    ...jobSummary,
    result: '# Heading\n\n<img src=x onerror="window.__xssExecuted=1" />\n\nBody text',
  };

  await page.route('**/api/providers/**', async (route) => {
    await route.fulfill({ json: [] });
  });

  await page.route('**/api/jobs/?**', async (route) => {
    await route.fulfill({ json: [jobSummary] });
  });

  await page.route('**/api/jobs/1', async (route) => {
    await route.fulfill({ json: jobDetail });
  });

  await page.goto('/history');
  await page.getByText('unsafe.md').click();

  await expect(page.getByText('Extracted Data')).toBeVisible();
  await expect(page.locator('.prose img')).toHaveCount(0);

  await page.waitForTimeout(300);
  const executed = await page.evaluate(() => (window as Window & { __xssExecuted?: number }).__xssExecuted || 0);
  expect(executed).toBe(0);
});
