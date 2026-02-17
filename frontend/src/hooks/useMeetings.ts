import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { meetingService } from '@/services/api/meeting.service';
import type { MeetingCreate, MeetingUpdate } from '@/types/meeting.types';

// Query Keys
export const meetingKeys = {
  all: ['meetings'] as const,
  list: (filters: Record<string, unknown>) =>
    ['meetings', filters] as const,
  byWeek: (startDate: string, endDate: string) =>
    ['meetings', 'week', startDate, endDate] as const,
  detail: (id: number) => ['meetings', id] as const,
};

// Queries
export const useMeetings = (filters: {
  skip?: number;
  limit?: number;
  enabled?: boolean;
} = {}) => {
  const { enabled = true, skip = 0, limit = 100 } = filters;
  return useQuery({
    queryKey: meetingKeys.list({ skip, limit }),
    queryFn: async () => {
      const response = await meetingService.getMeetings(skip, limit);
      return response.data ?? [];
    },
    staleTime: 60 * 1000,
    enabled,
  });
};

export const useMeetingsByWeek = (startDate: string, endDate: string) => {
  return useQuery({
    queryKey: meetingKeys.byWeek(startDate, endDate),
    queryFn: async () => {
      const response = await meetingService.getMeetingsByDateRange(startDate, endDate);
      return response.data ?? [];
    },
    staleTime: 60 * 1000,
    enabled: !!startDate && !!endDate,
  });
};

export const useMeetingDetail = (id: number) => {
  return useQuery({
    queryKey: meetingKeys.detail(id),
    queryFn: async () => {
      const response = await meetingService.getMeetingById(id);
      return response.data;
    },
    staleTime: 60 * 1000,
    enabled: id > 0,
  });
};

// Mutations
export const useCreateMeeting = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: MeetingCreate) => meetingService.createMeeting(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: meetingKeys.all });
    },
  });
};

export const useUpdateMeeting = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: MeetingUpdate }) =>
      meetingService.updateMeeting(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: meetingKeys.all });
    },
  });
};

export const useDeleteMeeting = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => meetingService.deleteMeeting(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: meetingKeys.all });
    },
  });
};
