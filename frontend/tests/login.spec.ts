import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
	test('user can log in as a resident', async ({ page }) => {
		console.log("Navigating to login page...");
		await page.goto('/login', { waitUntil: 'domcontentloaded' });
		
		console.log("Waiting for hydration...");
		await page.waitForTimeout(1000); // Wait for Svelte JS to hydrate
		
		console.log("Waiting for email input...");
		await page.waitForSelector('input[type="email"]');
		
		console.log("Filling form...");
		await page.fill('input[type="email"]', 'resident1@solshare.com');
		await page.fill('input[type="password"]', 'resident123');

		console.log("Clicking Sign In...");
		await page.getByRole('button', { name: /sign in/i }).click();

		console.log("Waiting for dashboard to load...");
		await expect(page.locator('h1', { hasText: 'Dashboard' })).toBeVisible({ timeout: 15000 });
		await expect(page.locator('h2', { hasText: 'Energy Overview' })).toBeVisible();
		console.log("Login successful!");
	});

	test('shows error with wrong credentials', async ({ page }) => {
		await page.goto('/login', { waitUntil: 'domcontentloaded' });
		await page.waitForSelector('input[type="email"]');

		await page.fill('input[type="email"]', 'wrong@email.com');
		await page.fill('input[type="password"]', 'badpassword');
		await page.getByRole('button', { name: /sign in/i }).click();

		// The login shouldn't redirect
		await page.waitForTimeout(2000);
		expect(page.url()).toContain('/login');
	});
});

