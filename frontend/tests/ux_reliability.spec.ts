import { test, expect } from '@playwright/test';

test.describe('UX & Reliability Suits', () => {

	test('unauthenticated user is redirected to login', async ({ page }) => {
		await page.goto('/dashboard');
		await page.waitForTimeout(2000); // Wait for auth check
		await expect(page).toHaveURL(/\/login/);
	});

	test('resident user does not see administrative links', async ({ page }) => {
		await page.goto('/login');
		await page.waitForTimeout(2000); // Hydration
		await page.fill('input[type="email"]', 'resident1@solshare.com');
		await page.fill('input[type="password"]', 'resident123');
		await page.getByRole('button', { name: /sign in/i }).click();

		// Wait for dashboard to load
		await page.waitForURL('**/dashboard', { timeout: 15000 });
		await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();

		// Verify 'Buildings' and 'Admin Panel' are NOT visible
		await expect(page.locator('aside').filter({ hasText: 'Buildings' })).not.toBeVisible();
		await expect(page.locator('aside').filter({ hasText: 'Admin Panel' })).not.toBeVisible();
	});

	test('mobile menu is visible on small screens', async ({ page }) => {
		await page.setViewportSize({ width: 375, height: 667 });
		
		await page.goto('/login');
		await page.waitForTimeout(2000); // Hydration
		await page.fill('input[type="email"]', 'resident1@solshare.com');
		await page.fill('input[type="password"]', 'resident123');
		await page.getByRole('button', { name: /sign in/i }).click();

		// Wait for dashboard
		await page.waitForURL('**/dashboard', { timeout: 15000 });

		// Click the hamburger menu button specifically by its icon
		const mobileMenuBtn = page.locator('button svg.lucide-menu').locator('..');
		await expect(mobileMenuBtn).toBeVisible();
		await mobileMenuBtn.click();

		// Wait for the drawer animation to finish
		await page.waitForTimeout(500);

		// Specifically target the mobile aside (it has the md:hidden class)
		const mobileDrawer = page.locator('aside.md\\:hidden');
		await expect(mobileDrawer).toBeVisible();
		await expect(mobileDrawer.locator('text=SolShare')).toBeVisible();
	});
});
