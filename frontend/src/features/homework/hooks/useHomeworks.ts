import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  homeworkService,
  type MyHomeworksQueryParams,
} from '@/features/homework/services/homework.service';
import type {
  Homework,
  MyHomeworksStats,
} from '@/features/homework/types/homework.types';
import type { PaginationMeta } from '@/types/api.types';

// Query Keys
const homeworkKeys = {
  all: ['homeworks'] as const,
  detail: (id: number) => ['homeworks', id] as const,
  myDetail: (id: number) => ['homeworks', 'me-detail', id] as const,
};

const EMPTY_STATS: MyHomeworksStats = {
  total: 0,
  completed: 0,
  completed_on_time: 0,
  completed_late: 0,
  uncompleted: 0,
  overdue: 0,
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
    staleTime: 2 * 60 * 1000,
    enabled: options?.enabled,
  });
};

export const useMyHomeworks = (options?: MyHomeworksQueryParams) => {
  const page = options?.page ?? 1;
  const pageSize = options?.pageSize ?? 20;
  const status = options?.status ?? 'all';
  const search = options?.search?.trim() ?? '';

  return useQuery({
    queryKey: ['homeworks', 'me', { page, pageSize, status, search }],
    queryFn: async () => {
      const res = await homeworkService.getMyHomeworks({
        page,
        pageSize,
        status,
        search,
      });
      return {
        items: res.data?.items ?? [],
        stats: res.data?.stats ?? EMPTY_STATS,
        pagination: res.pagination ?? null,
      };
    },
    staleTime: 0,
    refetchOnMount: 'always',
  });
};

export const useMyHomeworkDetail = (homeworkId: number | null) => {
  return useQuery({
    queryKey: homeworkKeys.myDetail(homeworkId!),
    queryFn: () => homeworkService.getMyHomeworkDetail(homeworkId!),
    enabled: !!homeworkId,
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

export const useUnsubmittedReport = (options?: { enabled?: boolean }) => {
  return useQuery({
    queryKey: ['homeworks', 'report', 'unsubmitted'],
    queryFn: () => homeworkService.getUnsubmittedReport(),
    staleTime: 0,
    refetchOnMount: 'always',
    enabled: options?.enabled,
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
    staleTime: 60 * 1000,
  });
};

// Mutations
export const useDeleteHomework = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => homeworkService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: homeworkKeys.all });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
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
      queryClient.invalidateQueries({ queryKey: homeworkKeys.myDetail(homeworkId) });
      queryClient.invalidateQueries({ queryKey: ['homeworks', 'me'] });
      queryClient.invalidateQueries({ queryKey: homeworkKeys.all });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
};

export const useSyncMyUnsubmitted = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => homeworkService.syncMyUnsubmitted(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['homeworks'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
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
