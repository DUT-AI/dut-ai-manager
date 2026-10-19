import axiosInstance from "../../../services/axiosInstance";
import type {
  BillingSummary,
  Invoice,
  InvoiceCreate,
  MonthlyInvoiceCreate,
  MonthlyInvoicePreviewResponse
} from "../types/billing.types";
import type { ApiResponse } from "../../../types/api.types";

const billingService = {
  getMyInvoices: async () => {
    const response = await axiosInstance.get<ApiResponse<Invoice[]>>("/billing/me");
    return response.data;
  },

  getAllInvoices: async (
    filters?: { user_id?: number; team_id?: number; status?: string; billing_period?: string },
    page: number = 1,
    pageSize: number = 20
  ) => {
    const apiParams: Record<string, unknown> = {
      page,
      page_size: pageSize,
    };

    if (filters) {
      if (filters.user_id !== undefined) apiParams.user_id = filters.user_id;
      if (filters.team_id !== undefined) apiParams.team_id = filters.team_id;
      if (filters.status !== undefined) apiParams.bill_status = filters.status;
      if (filters.billing_period !== undefined) apiParams.billing_period = filters.billing_period;
    }

    const response = await axiosInstance.get<ApiResponse<Invoice[]>>("/billing/", {
      params: apiParams
    });
    return response.data;
  },

  getMatrixReport: async (params: { start_month: number, start_year: number, end_month: number, end_year: number, user_ids?: number[] }) => {
    const response = await axiosInstance.get<ApiResponse<Invoice[]>>("/billing/report/matrix", {
      params
    });
    return response.data;
  },

  getBillingSummary: async (filters?: { user_id?: number; team_id?: number; billing_period?: string }) => {
    const response = await axiosInstance.get<ApiResponse<BillingSummary>>("/billing/summary", {
      params: filters
    });
    return response.data;
  },

  getInvoiceDetails: async (id: number) => {
    const response = await axiosInstance.get<ApiResponse<Invoice>>(`/billing/${id}`);
    return response.data;
  },

  createInvoice: async (data: InvoiceCreate) => {
    const response = await axiosInstance.post<ApiResponse<Invoice[]>>("/billing/", data);
    return response.data;
  },

  updateInvoice: async (invoiceId: number, data: Omit<InvoiceCreate, 'user_ids' | 'user_id'>) => {
    const response = await axiosInstance.put<ApiResponse<Invoice>>(`/billing/${invoiceId}`, data);
    return response.data;
  },

  createMonthlyInvoices: async (data: MonthlyInvoiceCreate) => {
    const response = await axiosInstance.post<ApiResponse<MonthlyInvoicePreviewResponse | Invoice[]>>("/billing/monthly", data);
    return response.data;
  },

  deleteInvoice: async (id: number) => {
    const response = await axiosInstance.delete<ApiResponse<boolean>>(`/billing/${id}`);
    return response.data;
  }
};

export default billingService;
