import { expect, test } from '@playwright/test';
import { E2E_DEMO_PASSWORD, E2E_DEMO_USERNAME } from '../playwright.env';

const tinyPng = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9p0NvwAAAABJRU5ErkJggg==',
  'base64'
);

test('login unlocks upload, persists across reload, and allows history access', async ({ page }) => {
  await page.goto('/extract');

  await expect(page.getByRole('button', { name: 'Guest mode' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Select File' })).toBeEnabled();

  await page.getByRole('button', { name: 'Guest mode' }).click();
  await page.locator('#username').fill(E2E_DEMO_USERNAME);
  await page.locator('#password').fill(E2E_DEMO_PASSWORD);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();

  await expect(page.getByText(E2E_DEMO_USERNAME)).toBeVisible();
  await expect(page.getByRole('button', { name: 'Select File' })).toBeEnabled();

  await page.reload();

  await expect(page.getByText(E2E_DEMO_USERNAME)).toBeVisible();
  await page.locator('input[type="file"]').setInputFiles({
    name: 'sample.png',
    mimeType: 'image/png',
    buffer: tinyPng,
  });

  await expect(page.getByText('File uploaded successfully')).toBeVisible();

  await page.goto('/history');

  await expect(page.getByRole('heading', { name: 'Processing History' })).toBeVisible();
  await expect(page.getByText(/^Jobs \(\d+\)$/)).toBeVisible();
  await expect(page.getByText('History is available after sign-in.')).toHaveCount(0);
});
