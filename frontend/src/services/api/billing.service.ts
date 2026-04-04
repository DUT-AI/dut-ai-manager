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

  getAllInvoices: async (skip: number = 0, limit: number = 100) => {
    const response = await axiosInstance.get<ApiResponse<Invoice[]>>("/billing/", {
      params: { skip, limit }
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

  createMonthlyInvoices: async (data: MonthlyInvoiceCreate) => {
    const response = await axiosInstance.post<ApiResponse<MonthlyInvoicePreviewResponse | Invoice[]>>("/billing/monthly", data);
    return response.data;
  }
};

export default billingService;
