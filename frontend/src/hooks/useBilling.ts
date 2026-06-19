import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import billingService from '@/services/api/billing.service';
import type { InvoiceCreate, MonthlyInvoiceCreate } from '@/types/billing.types';

// Query Keys
export const billingKeys = {
  all: ['billing'] as const,
  my: () => ['billing', 'me'] as const,
  list: (skip?: number, limit?: number) => ['billing', { skip, limit }] as const,
  detail: (id: number) => ['billing', 'detail', id] as const,
};

// Queries
export const useMyInvoices = () => {
  return useQuery({
    queryKey: billingKeys.my(),
    queryFn: async () => {
      const response = await billingService.getMyInvoices();
      return response.data ?? [];
    },
    staleTime: 30 * 1000, // 30 seconds
  });
};

export const useAllInvoices = (
  filters?: { user_id?: number; status?: string; billing_period?: string },
  skip = 0,
  limit = 100
) => {
  return useQuery({
    queryKey: ['billing', 'list', { filters, skip, limit }],
    queryFn: async () => {
      const response = await billingService.getAllInvoices(filters, skip, limit);
      return response.data ?? [];
    },
    staleTime: 30 * 1000,
  });
};

export const useInvoiceDetail = (id: number, enabled = true, refetchInterval?: number) => {
  return useQuery({
    queryKey: billingKeys.detail(id),
    queryFn: async () => {
      const response = await billingService.getInvoiceDetails(id);
      return response.data;
    },
    enabled: !!id && enabled,
    refetchInterval, // Used for polling payment status
  });
};

export const useMatrixReport = (
  params: { start_month: number; start_year: number; end_month: number; end_year: number; user_ids?: number[] },
  enabled = false
) => {
  return useQuery({
    queryKey: ['billing', 'matrix', params],
    queryFn: async () => {
      const response = await billingService.getMatrixReport(params);
      return response.data ?? [];
    },
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Mutations
export const useCreateInvoice = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: InvoiceCreate) => billingService.createInvoice(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: billingKeys.all });
    },
  });
};

export const useUpdateInvoice = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Omit<InvoiceCreate, 'user_id'> }) => 
      billingService.updateInvoice(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: billingKeys.all });
      queryClient.invalidateQueries({ queryKey: billingKeys.detail(id) });
    },
  });
};

export const useCreateMonthlyInvoices = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: MonthlyInvoiceCreate) => billingService.createMonthlyInvoices(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: billingKeys.all });
    },
  });
};

export const useDeleteInvoice = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: number) => billingService.deleteInvoice(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: billingKeys.all });
    },
  });
};
