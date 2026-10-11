import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { violationService } from '@/features/violations/services/violation.service';

// Query Keys
const violationKeys = {
  all: ['violations'] as const,
  list: (filters: { page?: number; pageSize?: number; userId?: number; month?: number; year?: number; startDate?: string; endDate?: string }) =>
    ['violations', filters] as const,
};

// Queries
export const useViolations = (filters: {
  page?: number;
  pageSize?: number;
  userId?: number;
  month?: number;
  year?: number;
  startDate?: string;
  endDate?: string;
  enabled?: boolean;
} = {}) => {
  const { enabled = true, page = 1, pageSize = 20, ...rest } = filters;
  return useQuery({
    queryKey: violationKeys.list({ page, pageSize, ...rest }),
    queryFn: async () => {
      const response = await violationService.getViolations(
        page,
        pageSize,
        rest.userId,
        rest.month,
        rest.year,
        undefined,
        rest.startDate,
        rest.endDate
      );
      return {
        data: response.data ?? [],
        pagination: response.pagination ?? null,
      };
    },
    staleTime: 60 * 1000, // 1 minute
    enabled,
  });
};

// Mutations
export const useCreateViolation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: any) => violationService.createViolation(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: violationKeys.all });
    },
  });
};

export const useUpdateViolation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      violationService.updateViolation(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: violationKeys.all });
    },
  });
};

export const useDeleteViolation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => violationService.deleteViolation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: violationKeys.all });
    },
  });
};

export const useBulkDeleteViolations = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (ids: number[]) => violationService.bulkDeleteViolations(ids),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: violationKeys.all });
    },
  });
};

