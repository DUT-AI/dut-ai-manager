import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { permissionService } from '@/services/api/permission.service';
import type { PermissionCreate, PermissionUpdate } from '@/types/activity.types';

// Query Keys
const permissionRequestKeys = {
  all: ['permissionRequests'] as const,
  list: (filters: { userId?: number; month?: number; year?: number; category?: string }) => 
    ['permissionRequests', filters] as const,
};

// Queries
export const usePermissionRequests = (filters: { 
  userId?: number; 
  month?: number; 
  year?: number;
  category?: string;
  enabled?: boolean;
} = {}) => {
  const { enabled = true, ...rest } = filters;
  return useQuery({
    queryKey: permissionRequestKeys.list(rest),
    queryFn: async () => {
      const response = await permissionService.getPermissions(
        rest.userId, 
        rest.month, 
        rest.year,
        rest.category
      );
      return response ?? [];
    },
    staleTime: 60 * 1000, // 1 minute
    enabled,
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
