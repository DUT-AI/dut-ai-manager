import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { permissionService } from '@/features/rbac/services/permission.service';
import type { PermissionCreate, PermissionUpdate } from '@/features/activity/types/activity.types';

// Query Keys
const permissionRequestKeys = {
  all: ['permissionRequests'] as const,
  list: (filters: { userId?: number; month?: number; year?: number; category?: string; page?: number; pageSize?: number }) =>
    ['permissionRequests', filters] as const,
  detail: (id: number) => ['permissionRequests', 'detail', id] as const,
};

// Queries
export const usePermissionRequests = (filters: {
  userId?: number;
  month?: number;
  year?: number;
  category?: string;
  page?: number;
  pageSize?: number;
  enabled?: boolean;
} = {}) => {
  const { enabled = true, ...rest } = filters;
  return useQuery({
    queryKey: permissionRequestKeys.list(rest),
    queryFn: async () => {
      const response = await permissionService.getPermissions(rest);
      return response ?? [];
    },
    staleTime: 60 * 1000, // 1 minute
    enabled,
  });
};

export const usePermissionRequestDetail = (id: number | null | undefined, enabled = true) => {
  return useQuery({
    queryKey: id ? permissionRequestKeys.detail(id) : ['permissionRequests', 'detail', 'null'],
    queryFn: async () => {
      if (!id) return null;
      return await permissionService.getPermissionById(id);
    },
    staleTime: 60 * 1000,
    enabled: enabled && !!id,
  });
};

// Mutations
export const useCreatePermissionRequest = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: PermissionCreate) => permissionService.createPermission(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: permissionRequestKeys.all });
    },
  });
};

export const useUpdatePermissionRequest = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: PermissionUpdate }) =>
      permissionService.updatePermission(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: permissionRequestKeys.all });
    },
  });
};

export const useDeletePermissionRequest = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => permissionService.deletePermission(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: permissionRequestKeys.all });
    },
  });
};
