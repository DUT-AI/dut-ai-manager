import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import expenseService from '../services/expense.service';
import type {
  CreateExpenseDto,
  UpdateExpenseDto,
  ExpenseStatusType,
} from '../types/expense.types';
import { message } from 'antd';

export const EXPENSES_QUERY_KEY = ['expenses'];
export const EXPENSE_SUMMARY_QUERY_KEY = ['expense-summary'];

export const useExpenses = (params?: {
  month?: number;
  year?: number;
  status?: ExpenseStatusType;
  spender_id?: number;
  team_id?: number;
}) => {
  return useQuery({
    queryKey: [...EXPENSES_QUERY_KEY, params],
    queryFn: async () => {
      const res = await expenseService.getExpenses(params);
      return res.data;
    },
  });
};

export const useExpenseSummary = (params?: {
  month?: number;
  year?: number;
  spender_id?: number;
  team_id?: number;
}) => {
  return useQuery({
    queryKey: [...EXPENSE_SUMMARY_QUERY_KEY, params],
    queryFn: async () => {
      const res = await expenseService.getExpenseSummary(params);
      return res.data;
    },
  });
};

export const useCreateExpense = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateExpenseDto) => expenseService.createExpense(data),
    onSuccess: () => {
      message.success('Tạo hóa đơn xuất ra thành công!');
      queryClient.invalidateQueries({ queryKey: EXPENSES_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: EXPENSE_SUMMARY_QUERY_KEY });
    },
    onError: (err: any) => {
      message.error(err?.response?.data?.message || 'Có lỗi xảy ra khi tạo hóa đơn');
    },
  });
};

export const useUpdateExpense = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateExpenseDto }) =>
      expenseService.updateExpense(id, data),
    onSuccess: () => {
      message.success('Cập nhật hóa đơn xuất ra thành công!');
      queryClient.invalidateQueries({ queryKey: EXPENSES_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: EXPENSE_SUMMARY_QUERY_KEY });
    },
    onError: (err: any) => {
      message.error(err?.response?.data?.message || 'Có lỗi xảy ra khi cập nhật hóa đơn');
    },
  });
};

export const useUpdateExpenseStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      status,
      payment_date,
    }: {
      id: string;
      status: ExpenseStatusType;
      payment_date?: string | null;
    }) => expenseService.updateExpenseStatus(id, status, payment_date),
    onSuccess: () => {
      message.success('Cập nhật trạng thái hóa đơn thành công!');
      queryClient.invalidateQueries({ queryKey: EXPENSES_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: EXPENSE_SUMMARY_QUERY_KEY });
    },
    onError: (err: any) => {
      message.error(err?.response?.data?.message || 'Có lỗi xảy ra khi cập nhật trạng thái');
    },
  });
};

export const useDeleteExpense = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => expenseService.deleteExpense(id),
    onSuccess: () => {
      message.success('Xóa hóa đơn xuất ra thành công!');
      queryClient.invalidateQueries({ queryKey: EXPENSES_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: EXPENSE_SUMMARY_QUERY_KEY });
    },
    onError: (err: any) => {
      message.error(err?.response?.data?.message || 'Có lỗi xảy ra khi xóa hóa đơn');
    },
  });
};
