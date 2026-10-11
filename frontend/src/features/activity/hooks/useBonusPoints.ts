import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { bonusPointService } from '@/features/activity/services/bonus-point.service';
import type { BonusPointCreate, BonusPointUpdate, BonusPointResponse } from '@/features/activity/types/activity.types';
import type { PaginationMeta } from '@/types/api.types';

// Query Keys
const bonusPointKeys = {
  all: ['bonusPoints'] as const,
  list: (filters: { userId?: number; type?: string; month?: number; year?: number; startDate?: string; endDate?: string; page?: number; pageSize?: number }) =>
    ['bonusPoints', filters] as const,
};

// Queries
export const useBonusPoints = (filters: {
  userId?: number;
  type?: string;
  month?: number;
  year?: number;
  startDate?: string;
  endDate?: string;
  page?: number;
  pageSize?: number;
  enabled?: boolean;
} = {}) => {
  const { enabled = true, page = 1, pageSize = 20, ...rest } = filters;
  return useQuery({
    queryKey: bonusPointKeys.list({ ...rest, page, pageSize }),
    queryFn: async () => {
      const response = await bonusPointService.getBonusPoints(
        rest.userId,
        rest.type,
        rest.month,
        rest.year,
        undefined,
        rest.startDate,
        rest.endDate,
        page,
        pageSize
      );
      const items = response?.data ?? [];
      const result = [...items] as BonusPointResponse[] & {
        data: BonusPointResponse[];
        pagination: PaginationMeta | null;
      };
      result.data = items;
      result.pagination = response?.pagination ?? null;
      return result;
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
