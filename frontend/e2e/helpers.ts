import type { Page } from '@playwright/test';

export const MOCK_USER = {
    id: 1,
    name: 'Admin Test',
    email: 'admin@test.com',
    role_name: 'admin',
    status: 'active',
    phone_number: '0912345678',
    avatar_url: null,
    discord_id: null,
    permissions: [],
};

export const MOCK_TOKENS = {
    access_token: 'mock-access-token',
    refresh_token: 'mock-refresh-token',
    token_type: 'bearer',
};

export async function mockAuthenticatedUser(page: Page) {
    await page.route('**/auth/me', async (route) => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ is_success: true, status_code: 200, message: 'OK', data: MOCK_USER }),
        });
    });
}

export async function mockUnauthenticated(page: Page) {
    await page.route('**/auth/me', async (route) => {
        await route.fulfill({
            status: 401,
            contentType: 'application/json',
            body: JSON.stringify({ is_success: false, status_code: 401, message: 'Not authenticated', data: null }),
        });
    });
}

export async function mockLoginSuccess(page: Page) {
    await page.route('**/auth/login', async (route) => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ is_success: true, status_code: 200, message: 'Login successful', data: MOCK_TOKENS }),
        });
    });
}

export async function mockEmptyList(page: Page, pattern: string) {
    await page.route(pattern, async (route) => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ is_success: true, status_code: 200, message: 'OK', data: [] }),
        });
    });
}

export async function mockAllApiCallsEmpty(page: Page) {
    await page.route('http://localhost:8001/**', async (route) => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ is_success: true, status_code: 200, message: 'OK', data: [] }),
        });
    });
}
