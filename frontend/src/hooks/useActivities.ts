import { useQuery } from '@tanstack/react-query';
import { activityService } from '@/services/api/activity.service';

export const activityKeys = {
  all: ['activities'] as const,
  monthly: (month: number, year: number) => ['activities', 'monthly', month, year] as const,
  daily: (date: string) => ['activities', 'daily', date] as const,
};

export const useMonthlyActivities = (month: number, year: number) => {
  return useQuery({
    queryKey: activityKeys.monthly(month, year),
    queryFn: async () => {
      const response = await activityService.getMonthlyStats(month, year);
      return response.data || [];
    },
  });
};

export const useDailyActivitySummary = (date: string) => {
  return useQuery({
    queryKey: activityKeys.daily(date),
    queryFn: async () => {
      const response = await activityService.getDailySummary(date);
      return response.data || null;
    },
    enabled: !!date,
  });
};
