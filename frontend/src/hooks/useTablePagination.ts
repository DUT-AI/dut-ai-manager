import { useSearchParams } from 'react-router-dom';
import { useMemo, useCallback, useEffect } from 'react';
import type { TablePaginationConfig } from 'antd';

export interface UseTablePaginationOptions {
  defaultPage?: number;
  defaultPageSize?: number;
  syncUrl?: boolean;
  pageParamName?: string;
  pageSizeParamName?: string;
}

export interface UseTablePaginationReturn {
  page: number;
  pageSize: number;
  setPage: (newPage: number) => void;
  setPageSize: (newPageSize: number) => void;
  resetPage: () => void;
  getPaginationProps: (totalOrMeta?: number | { total: number } | null) => TablePaginationConfig;
  paginationProps: TablePaginationConfig;
}

/**
 * Custom hook to handle table pagination state synchronized with URL search params.
 * Enforces Constitution Principle VIII:
 * - defaultPageSize >= 20
 * - pageSizeOptions: ['10', '20', '50', '100']
 * - showSizeChanger: true
 * - showTotal indicators
 */
export const useTablePagination = (
  options: UseTablePaginationOptions = {}
): UseTablePaginationReturn => {
  const {
    defaultPage = 1,
    defaultPageSize = 20,
    syncUrl = true,
    pageParamName = 'page',
    pageSizeParamName = 'pageSize',
  } = options;

  const [searchParams, setSearchParams] = useSearchParams();

  // Tự động đồng bộ page & pageSize lên URL nếu URL chưa có
  useEffect(() => {
    if (!syncUrl) return;
    const hasPage = searchParams.has(pageParamName);
    const hasPageSize = searchParams.has(pageSizeParamName);
    if (!hasPage || !hasPageSize) {
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          if (!hasPage) next.set(pageParamName, String(defaultPage));
          if (!hasPageSize) next.set(pageSizeParamName, String(defaultPageSize));
          return next;
        },
        { replace: true }
      );
    }
  }, [syncUrl, pageParamName, pageSizeParamName, defaultPage, defaultPageSize, searchParams, setSearchParams]);

  const page = useMemo(() => {
    if (!syncUrl) return defaultPage;
    const raw = searchParams.get(pageParamName);
    const parsed = raw ? parseInt(raw, 10) : defaultPage;
    return isNaN(parsed) || parsed < 1 ? defaultPage : parsed;
  }, [searchParams, pageParamName, defaultPage, syncUrl]);

  const pageSize = useMemo(() => {
    if (!syncUrl) return defaultPageSize;
    const raw = searchParams.get(pageSizeParamName);
    const parsed = raw ? parseInt(raw, 10) : defaultPageSize;
    return isNaN(parsed) || parsed < 1 ? defaultPageSize : parsed;
  }, [searchParams, pageSizeParamName, defaultPageSize, syncUrl]);

  const setPage = useCallback(
    (newPage: number) => {
      if (!syncUrl) return;
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          next.set(pageParamName, String(newPage));
          return next;
        },
        { replace: true }
      );
    },
    [setSearchParams, pageParamName, syncUrl]
  );

  const setPageSize = useCallback(
    (newPageSize: number) => {
      if (!syncUrl) return;
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          next.set(pageSizeParamName, String(newPageSize));
          next.set(pageParamName, '1'); // Reset to page 1 on pageSize change
          return next;
        },
        { replace: true }
      );
    },
    [setSearchParams, pageSizeParamName, pageParamName, syncUrl]
  );

  const resetPage = useCallback(() => {
    setPage(1);
  }, [setPage]);

  const getPaginationProps = useCallback(
    (totalOrMeta?: number | { total: number } | null): TablePaginationConfig => {
      const total =
        typeof totalOrMeta === 'object' && totalOrMeta !== null
          ? totalOrMeta.total
          : typeof totalOrMeta === 'number'
            ? totalOrMeta
            : 0;

      return {
        current: page,
        pageSize: pageSize,
        total: total,
        defaultPageSize: defaultPageSize,
        pageSizeOptions: ['10', '20', '50', '100'],
        showSizeChanger: true,
        showTotal: (t, range) => `${range[0]}-${range[1]} / ${t} bản ghi`,
        onChange: (newPage, newPageSize) => {
          if (newPageSize !== pageSize) {
            setPageSize(newPageSize);
          } else {
            setPage(newPage);
          }
        },
      };
    },
    [page, pageSize, defaultPageSize, setPage, setPageSize]
  );

  const paginationProps = useMemo(() => getPaginationProps(0), [getPaginationProps]);

  return {
    page,
    pageSize,
    setPage,
    setPageSize,
    resetPage,
    getPaginationProps,
    paginationProps,
  };
};
