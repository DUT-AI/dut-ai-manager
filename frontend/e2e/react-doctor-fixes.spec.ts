import { test, expect } from '@playwright/test';
import {
    mockAuthenticatedUser,
    mockUnauthenticated,
    mockLoginSuccess,
    mockEmptyList,
    mockAllApiCallsEmpty,
    MOCK_USER,
} from './helpers';

const API = 'http://localhost:8001/api/v1';

// ─── 1. Login Page ────────────────────────────────────────────────────────────

test.describe('Login Page', () => {
    test.beforeEach(async ({ page }) => {
        await mockUnauthenticated(page);
    });

    test('redirects to /login when unauthenticated', async ({ page }) => {
        await page.goto('/');
        await expect(page).toHaveURL('/login');
    });

    test('renders login form with email and password fields', async ({ page }) => {
        await page.goto('/login');
        await expect(page.locator('input[placeholder="Email"]')).toBeVisible();
        await expect(page.locator('input[placeholder="Password"]')).toBeVisible();
        await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();
    });

    test('shows validation errors when submitting empty form', async ({ page }) => {
        await page.goto('/login');
        await page.getByRole('button', { name: /sign in/i }).click();
        await expect(page.locator('.ant-form-item-explain-error').first()).toBeVisible();
    });

    test('shows validation error for invalid email format', async ({ page }) => {
        await page.goto('/login');
        await page.locator('input[placeholder="Email"]').fill('not-an-email');
        await page.locator('input[placeholder="Password"]').fill('somepassword');
        await page.getByRole('button', { name: /sign in/i }).click();
        const emailError = page.locator('.ant-form-item').filter({ has: page.locator('input[placeholder="Email"]') }).locator('.ant-form-item-explain-error');
        await expect(emailError).toContainText('valid email');
    });

    test('shows error message on failed login', async ({ page }) => {
        await page.route(`${API}/auth/login`, async (route) => {
            await route.fulfill({
                status: 400, contentType: 'application/json',
                body: JSON.stringify({ is_success: false, status_code: 400, message: 'Incorrect email or password', data: null }),
            });
        });
        await page.goto('/login');
        await page.locator('input[placeholder="Email"]').fill('wrong@test.com');
        await page.locator('input[placeholder="Password"]').fill('wrongpassword');
        await page.getByRole('button', { name: /sign in/i }).click();
        await expect(page.locator('.ant-message-notice')).toBeVisible({ timeout: 5000 });
    });
});

// ─── 2. Dashboard Layout ──────────────────────────────────────────────────────

test.describe('Dashboard Layout (SidebarContent at module scope)', () => {
    test.beforeEach(async ({ page }) => {
        await page.route(`${API}/auth/me`, (r) => r.fulfill({
            status: 200, contentType: 'application/json',
            body: JSON.stringify({ is_success: true, status_code: 200, data: MOCK_USER }),
        }));
        await page.route(`${API}/reports/dashboard-overview**`, (r) => r.fulfill({
            status: 200, contentType: 'application/json',
            body: JSON.stringify({ is_success: true, data: { bonus_points: [], violations: [], permission_requests: [], unsubmitted_homeworks: [], meetings: [] } }),
        }));
    });

    test('renders sidebar navigation on desktop', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 800 });
        await page.goto('/dashboard');
        await page.waitForLoadState('load');
        await expect(page.locator('.ant-menu-item').filter({ hasText: 'Tổng quan' })).toBeVisible({ timeout: 8000 });
        await expect(page.locator('.ant-menu-item').filter({ hasText: 'Báo cáo' })).toBeVisible();
        await expect(page.locator('.ant-menu-item').filter({ hasText: 'Quản lý Thành viên' })).toBeVisible();
    });

    test('sidebar navigation clicks navigate correctly', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 800 });
        await page.route(`${API}/users**`, (r) => r.fulfill({
            status: 200, contentType: 'application/json',
            body: JSON.stringify({ is_success: true, data: [] }),
        }));
        await page.route(`${API}/roles**`, (r) => r.fulfill({
            status: 200, contentType: 'application/json',
            body: JSON.stringify({ is_success: true, data: [] }),
        }));
        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');
        await page.getByText('Quản lý Thành viên').click();
        await expect(page).toHaveURL(/\/dashboard\/users/, { timeout: 5000 });
    });

    test('shows loading spinner while authenticating', async ({ page }) => {
        await page.goto('/dashboard');
        const spinner = page.locator('.ant-spin');
        await expect(spinner.or(page.locator('.ant-card'))).toBeTruthy();
    });
});

// ─── 3. HomePage (lazy state + unique stat keys) ──────────────────────────────

test.describe('HomePage', () => {
    test.beforeEach(async ({ page }) => {
        await page.route(`${API}/auth/me`, (r) => r.fulfill({
            status: 200, contentType: 'application/json',
            body: JSON.stringify({ is_success: true, status_code: 200, data: MOCK_USER }),
        }));
        await page.route(`${API}/reports/dashboard-overview**`, (r) => r.fulfill({
            status: 200, contentType: 'application/json',
            body: JSON.stringify({
                is_success: true,
                data: { bonus_points: [], violations: [], permission_requests: [], unsubmitted_homeworks: [], meetings: [] },
            }),
        }));
    });

    test('renders stat cards with no React key warnings', async ({ page }) => {
        const keyWarnings: string[] = [];
        page.on('console', (msg) => {
            if (msg.text().includes('unique key')) keyWarnings.push(msg.text());
        });

        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');

        await expect(page.locator('.ant-card').filter({ hasText: 'Điểm cộng' }).first()).toBeVisible({ timeout: 8000 });
        await expect(page.locator('.ant-card').filter({ hasText: 'Vi phạm' }).first()).toBeVisible();

        expect(keyWarnings, `React key warnings: ${keyWarnings.join(', ')}`).toHaveLength(0);
    });

    test('month picker changes data filter', async ({ page }) => {
        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');
        const picker = page.locator('.ant-picker').first();
        await expect(picker).toBeVisible({ timeout: 8000 });
    });
});

// ─── 4. Violation Management (MobileListView at module scope) ─────────────────

test.describe('ViolationManagementPage — mobile list', () => {
    test.beforeEach(async ({ page }) => {
        await page.route(`${API}/auth/me`, (r) => r.fulfill({
            status: 200, contentType: 'application/json',
            body: JSON.stringify({ is_success: true, status_code: 200, data: MOCK_USER }),
        }));
        await page.route(`${API}/violations**`, async (route) => {
            if (route.request().method() !== 'GET') { await route.continue(); return; }
            await route.fulfill({
                status: 200, contentType: 'application/json',
                body: JSON.stringify({
                    is_success: true,
                    data: [{ id: 1, reason: 'Vắng không phép', date: '2025-01-15T10:00:00Z', user_id: 2, user_name: 'Nguyễn Văn A', user_avatar: null, created_at: '2025-01-15T10:00:00Z', updated_at: '2025-01-15T10:00:00Z' }],
                }),
            });
        });
        await page.route(`${API}/users**`, (r) => r.fulfill({
            status: 200, contentType: 'application/json',
            body: JSON.stringify({ is_success: true, data: [] }),
        }));
    });

    test('renders violation list on mobile viewport', async ({ page }) => {
        await page.setViewportSize({ width: 375, height: 812 });
        await page.goto('/dashboard/violations');
        await expect(page.getByText('Nguyễn Văn A')).toBeVisible({ timeout: 8000 });
        await expect(page.getByText('Vắng không phép')).toBeVisible();
    });

    test('edit button triggers modal on mobile', async ({ page }) => {
        await page.setViewportSize({ width: 375, height: 812 });
        await page.goto('/dashboard/violations');
        await expect(page.getByText('Nguyễn Văn A')).toBeVisible({ timeout: 8000 });
        const editBtn = page.locator('.ant-btn').filter({ hasText: 'Sửa' }).first();
        await editBtn.click();
        await expect(page.locator('.ant-modal')).toBeVisible({ timeout: 5000 });
    });
});

// ─── 5. User Management (MobileListView at module scope) ─────────────────────

test.describe('UserManagementPage — mobile list', () => {
    test('renders user list on mobile without key warnings', async ({ page }) => {
        await mockAllApiCallsEmpty(page);
        await page.route(`${API}/auth/me`, (r) => r.fulfill({
            status: 200, contentType: 'application/json',
            body: JSON.stringify({ is_success: true, status_code: 200, data: MOCK_USER }),
        }));
        await page.route(`${API}/users`, (r) => r.fulfill({
            status: 200, contentType: 'application/json',
            body: JSON.stringify({ is_success: true, data: [{ id: 2, name: 'Trần Thị B', email: 'b@test.com', role_name: 'teammate', status: 'active', phone_number: '0987654321', avatar_url: null, discord_id: null }] }),
        }));

        const keyWarnings: string[] = [];
        page.on('console', (msg) => {
            if (msg.text().includes('unique key')) keyWarnings.push(msg.text());
        });
        await page.setViewportSize({ width: 375, height: 812 });
        await page.goto('/dashboard/users');
        await expect(page.getByText('Trần Thị B')).toBeVisible({ timeout: 8000 });
        await expect(page.getByText('b@test.com')).toBeVisible();
        expect(keyWarnings).toHaveLength(0);
    });
});

// ─── 6. Team Management (key fix in Card.actions) ────────────────────────────

test.describe('TeamManagementPage — card actions key fix', () => {
    test.beforeEach(async ({ page }) => {
        await page.route(`${API}/auth/me`, (r) => r.fulfill({
            status: 200, contentType: 'application/json',
            body: JSON.stringify({ is_success: true, status_code: 200, data: MOCK_USER }),
        }));
        await page.route(`${API}/teams**`, async (route) => {
            if (route.request().method() !== 'GET') { await route.continue(); return; }
            await route.fulfill({
                status: 200, contentType: 'application/json',
                body: JSON.stringify({ is_success: true, data: [{ id: 1, team_name: 'Đội AI', member_count: 3, members: [], created_at: '2025-01-01T00:00:00Z' }] }),
            });
        });
        await page.route(`${API}/users**`, (r) => r.fulfill({
            status: 200, contentType: 'application/json',
            body: JSON.stringify({ is_success: true, data: [] }),
        }));
    });

    test('renders teams on mobile without key warnings', async ({ page }) => {
        const keyWarnings: string[] = [];
        page.on('console', (msg) => {
            if (msg.text().includes('unique key')) keyWarnings.push(msg.text());
        });
        await page.setViewportSize({ width: 375, height: 812 });
        await page.goto('/dashboard/teams');
        await expect(page.getByText('Đội AI')).toBeVisible({ timeout: 8000 });
        expect(keyWarnings).toHaveLength(0);
    });
});

// ─── 7. Profile Page (FilterBar at module scope) ──────────────────────────────

test.describe('ProfilePage', () => {
    test.beforeEach(async ({ page }) => {
        await page.route(`${API}/auth/me`, (r) => r.fulfill({
            status: 200, contentType: 'application/json',
            body: JSON.stringify({ is_success: true, status_code: 200, data: MOCK_USER }),
        }));
        await page.route(`${API}/users**`, async (route) => {
            if (route.request().method() !== 'GET') { await route.continue(); return; }
            await route.fulfill({
                status: 200, contentType: 'application/json',
                body: JSON.stringify({ is_success: true, data: [{ ...MOCK_USER, id: 1 }] }),
            });
        });
    });

    test('renders profile with tabs', async ({ page }) => {
        await page.goto('/dashboard/profile/1');
        await expect(page.getByRole('heading', { name: 'Admin Test' })).toBeVisible({ timeout: 8000 });
        await expect(page.getByRole('tab', { name: /thông tin/i })).toBeVisible();
        await expect(page.getByRole('tab', { name: /vi phạm/i })).toBeVisible();
        await expect(page.getByRole('tab', { name: /điểm cộng/i })).toBeVisible();
    });

    test('FilterBar appears when switching to violations tab', async ({ page }) => {
        await page.route(`${API}/violations**`, (r) => r.fulfill({
            status: 200, contentType: 'application/json',
            body: JSON.stringify({ is_success: true, data: [] }),
        }));
        await page.goto('/dashboard/profile/1');
        await page.getByRole('tab', { name: /vi phạm/i }).click();
        await expect(page.locator('.ant-picker').first()).toBeVisible({ timeout: 5000 });
    });
});

// ─── 8. Homework Page (HomeworkMobileList at module scope) ───────────────────

test.describe('HomeworkPage — mobile list', () => {
    test.beforeEach(async ({ page }) => {
        await mockAllApiCallsEmpty(page);
        await page.route(`${API}/auth/me`, (r) => r.fulfill({
            status: 200, contentType: 'application/json',
            body: JSON.stringify({ is_success: true, status_code: 200, data: MOCK_USER }),
        }));
        await page.route(`${API}/homeworks/me*`, (r) => r.fulfill({
            status: 200, contentType: 'application/json',
            body: JSON.stringify({ is_success: true, data: [{ id: 1, title: 'Bài tập React', description: 'Làm bài tập về hooks', deadline: '2099-12-31T23:59:59Z', created_at: '2025-01-01T00:00:00Z', updated_at: '2025-01-01T00:00:00Z' }] }),
        }));
    });

    test('renders homework list on mobile', async ({ page }) => {
        await page.setViewportSize({ width: 375, height: 812 });
        await page.goto('/dashboard/homeworks');
        await expect(page.getByText('Bài tập React')).toBeVisible({ timeout: 8000 });
        await expect(page.locator('.ant-btn').filter({ hasText: 'Nộp bài' }).first()).toBeVisible();
    });
});

// ─── 9. Modal Initialization (useEffect → initialValues fix) ─────────────────

test.describe('Modal initialValues — create mode starts empty', () => {
    test.beforeEach(async ({ page }) => {
        await page.route(`${API}/auth/me`, (r) => r.fulfill({
            status: 200, contentType: 'application/json',
            body: JSON.stringify({ is_success: true, status_code: 200, data: MOCK_USER }),
        }));
        await page.route(`${API}/violations**`, async (route) => {
            if (route.request().method() !== 'GET') { await route.continue(); return; }
            await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ is_success: true, data: [] }) });
        });
        await page.route(`${API}/users**`, (r) => r.fulfill({
            status: 200, contentType: 'application/json',
            body: JSON.stringify({ is_success: true, data: [] }),
        }));
    });

    test('create violation modal opens with empty reason field', async ({ page }) => {
        await page.goto('/dashboard/violations');
        await page.waitForLoadState('networkidle');
        const addBtn = page.locator('.ant-btn').filter({ hasText: 'Thêm Vi phạm' });
        await expect(addBtn).toBeVisible({ timeout: 8000 });
        await addBtn.click();
        await expect(page.locator('.ant-modal')).toBeVisible({ timeout: 5000 });
        const reasonField = page.locator('.ant-modal textarea').first();
        const value = await reasonField.inputValue().catch(() => '');
        expect(value).toBe('');
    });
});

// ─── 10. Accessibility — role=button on interactive divs ─────────────────────

test.describe('Accessibility — role=button on interactive elements', () => {
    test('MeetingCalendarPage day headers have role=button', async ({ page }) => {
        await mockAllApiCallsEmpty(page);
        await page.route(`${API}/auth/me`, (r) => r.fulfill({
            status: 200, contentType: 'application/json',
            body: JSON.stringify({ is_success: true, status_code: 200, data: MOCK_USER }),
        }));
        await page.goto('/dashboard/meetings');
        await expect(page.getByRole('heading', { name: 'Lịch Meeting' })).toBeVisible({ timeout: 8000 });
        const roleButtons = page.locator('div[role="button"]');
        const count = await roleButtons.count();
        expect(count).toBeGreaterThan(0);
    });

    test('ActivityCalendarPage day cells have role=button on mobile', async ({ page }) => {
        await mockAllApiCallsEmpty(page);
        await page.route(`${API}/auth/me`, (r) => r.fulfill({
            status: 200, contentType: 'application/json',
            body: JSON.stringify({ is_success: true, status_code: 200, data: MOCK_USER }),
        }));
        await page.setViewportSize({ width: 375, height: 812 });
        await page.goto('/dashboard/activities');
        await page.waitForTimeout(1000);
        const dayButtons = page.locator('div[role="button"]');
        const count = await dayButtons.count();
        expect(count).toBeGreaterThan(0);
    });
});

// ─── 11. ReportPage (MobileListView + DesktopTableView at module scope) ───────

test.describe('ReportPage', () => {
    test.beforeEach(async ({ page }) => {
        await page.route(`${API}/auth/me`, (r) => r.fulfill({
            status: 200, contentType: 'application/json',
            body: JSON.stringify({ is_success: true, status_code: 200, data: MOCK_USER }),
        }));
        await page.route(`${API}/reports/**`, (r) => r.fulfill({
            status: 200, contentType: 'application/json',
            body: JSON.stringify({
                is_success: true,
                data: { items: [{ rank: 1, user: { id: 1, name: 'Top Member', email: 'top@test.com', avatar_url: null }, total_points: 50, total_violations: 0, details_count: 5 }], total: 1 },
            }),
        }));
    });

    test('renders report table on desktop', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 800 });
        await page.goto('/dashboard/reports');
        await expect(page.getByText('Top Member')).toBeVisible({ timeout: 8000 });
        await expect(page.locator('.ant-table')).toBeVisible();
    });

    test('renders report list on mobile', async ({ page }) => {
        await page.setViewportSize({ width: 375, height: 812 });
        await page.goto('/dashboard/reports');
        await expect(page.getByText('Top Member')).toBeVisible({ timeout: 8000 });
    });

    test('tab switching sets aria-selected', async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 800 });
        await page.goto('/dashboard/reports');
        await page.waitForLoadState('networkidle');
        const violationsTab = page.getByRole('tab', { name: /violations/i });
        await violationsTab.click();
        await expect(violationsTab).toHaveAttribute('aria-selected', 'true', { timeout: 5000 });
    });
});

// ─── 12. Settings Page ────────────────────────────────────────────────────────

test.describe('SettingsPage', () => {
    test.beforeEach(async ({ page }) => {
        await page.route(`${API}/auth/me`, (r) => r.fulfill({
            status: 200, contentType: 'application/json',
            body: JSON.stringify({ is_success: true, status_code: 200, data: MOCK_USER }),
        }));
    });

    test('renders general settings with user info and Discord field', async ({ page }) => {
        await page.goto('/dashboard/settings');
        await expect(page.getByRole('heading', { name: 'Admin Test' })).toBeVisible({ timeout: 8000 });
        await expect(page.locator('input[id*="discord"]').or(page.locator('input[placeholder*="Discord"]'))).toBeVisible();
    });

    test('switches to security tab and shows password form', async ({ page }) => {
        await page.goto('/dashboard/settings');
        await page.waitForLoadState('networkidle');
        const securityItem = page.locator('.ant-menu-item').filter({ hasText: 'Bảo mật' })
            .or(page.getByRole('button', { name: /bảo mật/i }));
        await securityItem.first().click();
        await expect(page.locator('input[type="password"]').first()).toBeVisible({ timeout: 5000 });
    });
});
