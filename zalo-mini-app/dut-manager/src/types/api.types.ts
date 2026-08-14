export interface ApiResponse<T> {
  is_success: boolean;
  status_code: number;
  data: T | null;
  message: string;
}
