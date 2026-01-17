import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { homeworkService } from '@/services/api/homework.service';
import type { HomeworkCreate, HomeworkUpdate, HomeworkStatus } from '@/types/homework.types';

// Query Keys
export const homeworkKeys = {
  all: ['homeworks'] as const,
  my: ['homeworks', 'me'] as const,
  detail: (id: number) => ['homeworks', id] as const,
  submissions: (homeworkId: number) => ['submissions', homeworkId] as const,
  mySubmission: (homeworkId: number) => ['submissions', 'me', homeworkId] as const,
};

// Queries
export const useHomeworks = () => {
  return useQuery({
    queryKey: homeworkKeys.all,
    queryFn: () => homeworkService.getAll(),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

export const useMyHomeworks = () => {
  return useQuery({
    queryKey: homeworkKeys.my,
    queryFn: () => homeworkService.getMyHomeworks(),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

export const useHomework = (id: number) => {
  return useQuery({
    queryKey: homeworkKeys.detail(id),
    queryFn: () => homeworkService.getById(id),
    enabled: !!id,
  });
};

export const useSubmissions = (homeworkId: number) => {
  return useQuery({
    queryKey: homeworkKeys.submissions(homeworkId),
    queryFn: () => homeworkService.getSubmissions(homeworkId),
    enabled: !!homeworkId,
    staleTime: 60 * 1000, // 1 minute
  });
};

export const useMySubmission = (homeworkId: number) => {
  return useQuery({
    queryKey: homeworkKeys.mySubmission(homeworkId),
    queryFn: () => homeworkService.getMySubmission(homeworkId),
    enabled: !!homeworkId,
    staleTime: 30 * 1000, // 30 seconds
    retry: false, // Don't retry on 404
  });
};

// Mutations
export const useCreateHomework = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: HomeworkCreate) => homeworkService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: homeworkKeys.all });
      queryClient.invalidateQueries({ queryKey: homeworkKeys.my });
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
      queryClient.invalidateQueries({ queryKey: homeworkKeys.my });
    },
  });
};

export const useDeleteHomework = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: number) => homeworkService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: homeworkKeys.all });
      queryClient.invalidateQueries({ queryKey: homeworkKeys.my });
    },
  });
};

export const useSubmitHomework = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ homeworkId, file }: { homeworkId: number; file: File }) => 
      homeworkService.submit(homeworkId, file),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ 
        queryKey: homeworkKeys.submissions(variables.homeworkId) 
      });
      queryClient.invalidateQueries({ 
        queryKey: homeworkKeys.mySubmission(variables.homeworkId) 
      });
    },
  });
};

export const useUpdateSubmissionStatus = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ submissionId, status }: { 
      submissionId: number; 
      status: HomeworkStatus;
      homeworkId: number;
    }) => homeworkService.updateStatus(submissionId, status),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ 
        queryKey: homeworkKeys.submissions(variables.homeworkId) 
      });
    },
  });
};
