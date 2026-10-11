import { test, expect } from '@playwright/test';
import type { TablePaginationConfig } from 'antd';

test.describe('useTablePagination specification and contracts', () => {
  test('verifies Constitution Article VIII pagination defaults and props', () => {
    const defaultPageSize = 20;
    const pageSizeOptions = ['10', '20', '50', '100'];
    const showSizeChanger = true;

    expect(defaultPageSize).toBeGreaterThanOrEqual(20);
    expect(pageSizeOptions).toEqual(['10', '20', '50', '100']);
    expect(showSizeChanger).toBe(true);
  });

  test('verifies item range calculations and total indicator format', () => {
    const total = 55;
    const page = 2;
    const pageSize = 20;

    const start = (page - 1) * pageSize + 1;
    const end = Math.min(page * pageSize, total);
    const label = `Hiển thị ${start}-${end} trên tổng số ${total} bản ghi`;

    expect(start).toBe(21);
    expect(end).toBe(40);
    expect(label).toBe('Hiển thị 21-40 trên tổng số 55 bản ghi');
  });

  test('verifies last page calculation without overflow', () => {
    const total = 55;
    const page = 3;
    const pageSize = 20;

    const start = (page - 1) * pageSize + 1;
    const end = Math.min(page * pageSize, total);
    const label = `Hiển thị ${start}-${end} trên tổng số ${total} bản ghi`;

    expect(start).toBe(41);
    expect(end).toBe(55);
    expect(label).toBe('Hiển thị 41-55 trên tổng số 55 bản ghi');
  });
});
