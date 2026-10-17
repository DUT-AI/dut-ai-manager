import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { homeworkService } from '@/features/homework/services/homework.service';
import type { HomeworkCreate, HomeworkUpdate, HomeworkStatus, Homework } from '@/features/homework/types/homework.types';
import type { PaginationMeta } from '@/types/api.types';

// Query Keys
const homeworkKeys = {
  all: ['homeworks'] as const,
  detail: (id: number) => ['homeworks', id] as const,
};

// Queries
export const useHomeworks = (options?: {
  page?: number;
  pageSize?: number;
  deleted?: boolean;
  enabled?: boolean;
}) => {
  const page = options?.page ?? 1;
  const pageSize = options?.pageSize ?? 20;
  const deleted = options?.deleted ?? false;
  return useQuery({
    queryKey: ['homeworks', { page, pageSize, deleted }],
    queryFn: async () => {
      const res = await homeworkService.getAll(page, pageSize, deleted);
      const items = res.data ?? [];
      const result = items as Array<Homework> & {
        data: Homework[];
        pagination: PaginationMeta | null;
      };
      result.data = items;
      result.pagination = res.pagination ?? null;
      return result;
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
    enabled: options?.enabled,
  });
};

export const useMyHomeworks = (options?: { page?: number; pageSize?: number }) => {
  const page = options?.page ?? 1;
  const pageSize = options?.pageSize ?? 20;
  return useQuery({
    queryKey: ['homeworks', 'me', { page, pageSize }],
    queryFn: async () => {
      const res = await homeworkService.getMyHomeworks(page, pageSize);
      const items = res.data ?? [];
      const result = items as Array<Homework> & {
        data: Homework[];
        pagination: PaginationMeta | null;
      };
      result.data = items;
      result.pagination = res.pagination ?? null;
      return result;
    },
    staleTime: 0,
    refetchOnMount: 'always',
  });
};

export const useHomework = (id: number | null) => {
  return useQuery({
    queryKey: homeworkKeys.detail(id!),
    queryFn: () => homeworkService.getById(id!),
    enabled: !!id,
  });
};

export const useUnsubmittedReport = () => {
  return useQuery({
    queryKey: ['homeworks', 'report', 'unsubmitted'],
    queryFn: () => homeworkService.getUnsubmittedReport(),
    staleTime: 0,
    refetchOnMount: 'always',
  });
};

export const useUnsubmittedByUser = (userId: number | null) => {
  return useQuery({
    queryKey: ['homeworks', 'report', 'unsubmitted', userId],
    queryFn: () => homeworkService.getUnsubmittedByUser(userId!),
    enabled: !!userId,
    staleTime: 0,
    refetchOnMount: 'always',
  });
};

export const useHomeworkSubmissionStatus = (homeworkId: number | null) => {
  return useQuery({
    queryKey: ['homeworks', 'submission-status', homeworkId],
    queryFn: () => homeworkService.getSubmissionStatus(homeworkId!),
    enabled: !!homeworkId,
    staleTime: 60 * 1000, // 1 minute
  });
};

// Mutations
export const useCreateHomework = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: HomeworkCreate) => homeworkService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: homeworkKeys.all });
    },
  });
};

export const useUpdateHomework = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: HomeworkUpdate }) =>
      homeworkService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: homeworkKeys.all });
    },
  });
};

export const useDeleteHomework = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => homeworkService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: homeworkKeys.all });
    },
  });
};

export const useSyncHomeworkFromQuiz = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (homeworkId: number) => homeworkService.syncFromQuiz(homeworkId),
    onSuccess: (_, homeworkId) => {
      queryClient.invalidateQueries({ queryKey: ['homeworks', 'submission-status', homeworkId] });
      queryClient.invalidateQueries({ queryKey: ['homeworks', 'submissions', homeworkId] });
      queryClient.invalidateQueries({ queryKey: ['homeworks', 'my-submissions', homeworkId] });
      queryClient.invalidateQueries({ queryKey: ['homeworks', 'me'] });
      queryClient.invalidateQueries({ queryKey: homeworkKeys.all });
    },
  });
};

export const useHomeworkSubmissions = (homeworkId: number | null, userId: number | null) => {
  return useQuery({
    queryKey: ['homeworks', 'submissions', homeworkId, userId],
    queryFn: () => homeworkService.getUserSubmissions(homeworkId!, userId!),
    enabled: !!homeworkId && !!userId,
  });
};

export const useMyHomeworkSubmissions = (homeworkId: number | null) => {
  return useQuery({
    queryKey: ['homeworks', 'my-submissions', homeworkId],
    queryFn: () => homeworkService.getMySubmissions(homeworkId!),
    enabled: !!homeworkId,
  });
};

