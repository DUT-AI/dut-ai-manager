import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userService } from '@/features/users/services/user.service';
import type { UserCreate, UserUpdate, UserOptionDto, UserResponse } from '@/features/users/types/user.types';
import type { PaginationMeta } from '@/types/api.types';

// Query Keys
const userKeys = {
  all: ['users'] as const,
  list: (filters: { page?: number; pageSize?: number; keyword?: string }) =>
    ['users', filters] as const,
  options: ['users', 'options'] as const,
  detail: (id: number) => ['users', id] as const,
};

// Queries
export const useUsers = (filters?: {
  page?: number;
  pageSize?: number;
  keyword?: string;
  enabled?: boolean;
}) => {
  const page = filters?.page;
  const pageSize = filters?.pageSize;
  const keyword = filters?.keyword;
  const enabled = filters?.enabled ?? true;

  return useQuery({
    queryKey: userKeys.list({ page, pageSize, keyword }),
    queryFn: async () => {
      const response = await userService.getUsers(page ?? 1, pageSize ?? 20, keyword);
      const items = response.data ?? [];
      const result = items as Array<UserResponse> & {
        data: UserResponse[];
        pagination: PaginationMeta | null;
      };
      result.data = items;
      result.pagination = response.pagination ?? null;
      return result;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled,
  });
};

export const useUserOptions = () => {
  return useQuery({
    queryKey: userKeys.options,
    queryFn: async () => {
      const response = await userService.getUserOptions();
      return response.data ?? [];
    },
    staleTime: 5 * 60 * 1000,
  });
};

export const useUser = (id: number) => {
  return useQuery({
    queryKey: userKeys.detail(id),
    queryFn: async () => {
      const response = await userService.getUser(id);
      return response.data;
    },
    enabled: !!id,
  });
};

// Mutations
export const useCreateUser = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: UserCreate) => userService.createUser(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.all });
    },
  });
};

export const useUpdateUser = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UserUpdate }) =>
      userService.updateUser(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.all });
    },
  });
};

export const useDeleteUser = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => userService.deleteUser(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.all });
    },
  });
};

export const useImportUsers = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => userService.importUsers(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.all });
    },
  });
};
