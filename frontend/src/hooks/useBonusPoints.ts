import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { bonusPointService } from '@/services/api/bonus-point.service';
import type { BonusPointCreate, BonusPointUpdate } from '@/types/activity.types';

// Query Keys
const bonusPointKeys = {
  all: ['bonusPoints'] as const,
  list: (filters: { userId?: number; month?: number; year?: number }) => 
    ['bonusPoints', filters] as const,
};

// Queries
export const useBonusPoints = (filters: { 
  userId?: number; 
  month?: number; 
  year?: number;
  enabled?: boolean;
} = {}) => {
  const { enabled = true, ...rest } = filters;
  return useQuery({
    queryKey: bonusPointKeys.list(rest),
    queryFn: async () => {
      const response = await bonusPointService.getBonusPoints(
        rest.userId, 
        rest.month, 
        rest.year
      );
      return response ?? [];
    },
    staleTime: 60 * 1000, // 1 minute
    enabled,
  });
};

// Mutations
export const useCreateBonusPoint = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: BonusPointCreate) => bonusPointService.createBonusPoint(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: bonusPointKeys.all });
    },
  });
};

export const useUpdateBonusPoint = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: BonusPointUpdate }) => 
      bonusPointService.updateBonusPoint(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: bonusPointKeys.all });
    },
  });
};

export const useDeleteBonusPoint = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: number) => bonusPointService.deleteBonusPoint(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: bonusPointKeys.all });
    },
  });
};
