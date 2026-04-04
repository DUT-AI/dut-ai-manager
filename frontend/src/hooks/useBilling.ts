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

export const useAllInvoices = (skip = 0, limit = 100) => {
  return useQuery({
    queryKey: billingKeys.list(skip, limit),
    queryFn: async () => {
      const response = await billingService.getAllInvoices(skip, limit);
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

export const useCreateMonthlyInvoices = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: MonthlyInvoiceCreate) => billingService.createMonthlyInvoices(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: billingKeys.all });
    },
  });
};
