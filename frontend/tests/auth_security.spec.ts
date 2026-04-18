import { test, expect } from '@playwright/test';

test.describe('Advanced Auth & Security', () => {

	test('admin user sees management modules', async ({ page }) => {
		// 1. Log in as ADMIN
		await page.goto('/login');
		await page.waitForTimeout(2000); // Hydration wait
		
		await page.fill('input[type="email"]', 'admin@solshare.com');
		await page.fill('input[type="password"]', 'admin1234');
		await page.getByRole('button', { name: /sign in/i }).click();

		// 2. Verify Dashboard redirect and heading
		await page.waitForURL('**/dashboard', { timeout: 15000 });
		await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();

		// 3. Admin MUST see these links (wait for profile load)
		await expect(page.getByRole('link', { name: 'Buildings' })).toBeVisible({ timeout: 15000 });
		await expect(page.getByRole('link', { name: 'Admin Panel' })).toBeVisible();
		await expect(page.getByRole('link', { name: 'Settings' })).toBeVisible();
		
		console.log("Admin RBAC verified successfully!");
	});

	test('token hijacking defense - garbage tokens are rejected', async ({ page }) => {
		// 1. Go to root (will redirect to login)
		await page.goto('/login');
		await page.waitForTimeout(2000);

		// 2. Manually inject a fake hacker token into localStorage
		await page.evaluate(() => {
			localStorage.setItem('access_token', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.fake-payload');
		});

		// 3. Try to visit the dashboard
		await page.goto('/dashboard');
		
		// 4. The app should detect the invalid token, clear it, and stay on /login
		await page.waitForTimeout(2000);
		await expect(page).toHaveURL(/\/login/);
		
		const token = await page.evaluate(() => localStorage.getItem('access_token'));
		expect(token).toBeNull(); // It should have been wiped by our +layout.svelte logic
		
		console.log("Token hijacking defense verified!");
	});

	test('logout is permanent - no back door via back button', async ({ page }) => {
		// 1. Log in regularly
		await page.goto('/login');
		await page.waitForTimeout(2000);
		await page.fill('input[type="email"]', 'resident1@solshare.com');
		await page.fill('input[type="password"]', 'resident123');
		await page.getByRole('button', { name: /sign in/i }).click();

		await page.waitForURL('**/dashboard', { timeout: 15000 });
		await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();

		// 2. Log out
		await page.getByRole('button').filter({ has: page.locator('svg.lucide-log-out') }).first().click();
		await expect(page).toHaveURL(/\/login/);

		// 3. Try to go BACK in browser history
		await page.goBack();
		
		// 4. Even if it "flashes" the old page, the onMount in +layout.svelte 
		// should immediately detect no token and pull us back to /login
		await page.waitForTimeout(2000);
		await expect(page).toHaveURL(/\/login/);
		
		console.log("Logout security verified!");
	});
});
