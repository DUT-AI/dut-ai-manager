import axiosInstance from "../../../services/axiosInstance";
import type {
  ExpenseInvoice,
  CreateExpenseDto,
  UpdateExpenseDto,
  ExpenseSummary,
  ExpenseStatusType,
} from "../types/expense.types";
import type { ApiResponse } from "../../../types/api.types";

const expenseService = {
  getExpenses: async (params?: {
    month?: number;
    year?: number;
    status?: ExpenseStatusType;
    spender_id?: number;
    team_id?: number;
    limit?: number;
    offset?: number;
  }) => {
    const response = await axiosInstance.get<ApiResponse<ExpenseInvoice[]>>("/expenses/", {
      params,
    });
    return response.data;
  },

  getExpenseSummary: async (params?: { month?: number; year?: number; spender_id?: number; team_id?: number }) => {
    const response = await axiosInstance.get<ApiResponse<ExpenseSummary>>("/expenses/summary", {
      params,
    });
    return response.data;
  },

  getExpenseById: async (id: string) => {
    const response = await axiosInstance.get<ApiResponse<ExpenseInvoice>>(`/expenses/${id}`);
    return response.data;
  },

  createExpense: async (data: CreateExpenseDto) => {
    const response = await axiosInstance.post<ApiResponse<ExpenseInvoice>>("/expenses/", data);
    return response.data;
  },

  updateExpense: async (id: string, data: UpdateExpenseDto) => {
    const response = await axiosInstance.put<ApiResponse<ExpenseInvoice>>(`/expenses/${id}`, data);
    return response.data;
  },

  updateExpenseStatus: async (id: string, status: ExpenseStatusType, payment_date?: string | null) => {
    const response = await axiosInstance.patch<ApiResponse<ExpenseInvoice>>(`/expenses/${id}/status`, {
      status,
      payment_date,
    });
    return response.data;
  },

  deleteExpense: async (id: string) => {
    const response = await axiosInstance.delete<ApiResponse<boolean>>(`/expenses/${id}`);
    return response.data;
  },
};

export default expenseService;
