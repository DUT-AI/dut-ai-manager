import axiosInstance from "../axiosInstance";
import type { 
  Invoice, 
  InvoiceCreate, 
  MonthlyInvoiceCreate, 
  MonthlyInvoicePreviewResponse 
} from "../../types/billing.types";
import type { ApiResponse } from "../../types/api.types";

const billingService = {
  getMyInvoices: async () => {
    const response = await axiosInstance.get<ApiResponse<Invoice[]>>("/billing/me");
    return response.data;
  },

  getAllInvoices: async (
    filters?: { user_id?: number; status?: string; billing_period?: string },
    skip: number = 0,
    limit: number = 100
  ) => {
    const apiParams: {
      skip: number;
      limit: number;
      user_id?: number;
      bill_status?: string;
      billing_period?: string;
    } = { skip, limit };

    if (filters) {
      if (filters.user_id !== undefined) apiParams.user_id = filters.user_id;
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

  getInvoiceDetails: async (id: number) => {
    const response = await axiosInstance.get<ApiResponse<Invoice>>(`/billing/${id}`);
    return response.data;
  },

  createInvoice: async (data: InvoiceCreate) => {
    const response = await axiosInstance.post<ApiResponse<Invoice>>("/billing/", data);
    return response.data;
  },

  updateInvoice: async (invoiceId: number, data: Omit<InvoiceCreate, 'user_id'>) => {
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
