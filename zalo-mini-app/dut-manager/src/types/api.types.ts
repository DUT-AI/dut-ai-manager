export interface PaginationMeta {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  has_next: boolean;
}

export interface ApiResponse<T> {
  is_success: boolean;
  status_code: number;
  data: T | null;
  message: string;
  pagination?: PaginationMeta | null;
}
