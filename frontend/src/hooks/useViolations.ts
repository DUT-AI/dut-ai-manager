import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { violationService } from '@/services/api/violation.service';

// Query Keys
export const violationKeys = {
  all: ['violations'] as const,
  list: (filters: { userId?: number; month?: number; year?: number }) => 
    ['violations', filters] as const,
};

// Queries
export const useViolations = (filters: { 
  userId?: number; 
  month?: number; 
  year?: number;
  enabled?: boolean;
} = {}) => {
  const { enabled = true, ...rest } = filters;
  return useQuery({
    queryKey: violationKeys.list(rest),
    queryFn: async () => {
      const response = await violationService.getViolations(
        0, 100, 
        rest.userId, 
        rest.month, 
        rest.year
      );
      return response.data ?? [];
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
