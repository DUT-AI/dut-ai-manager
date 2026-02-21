import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { rbacService } from '@/services/api/rbac.service';
import type { RoleCreate, RoleUpdate, PermissionCreate, PermissionUpdate } from '@/types/rbac.types';

// Query Keys
const rbacKeys = {
  roles: ['roles'] as const,
  permissions: ['permissions'] as const,
};

// Queries
export const useRoles = () => {
  return useQuery({
    queryKey: rbacKeys.roles,
    queryFn: async () => {
      const response = await rbacService.getRoles();
      return response.data ?? [];
    },
    staleTime: 10 * 60 * 1000, // 10 minutes - rarely changes
  });
};

export const usePermissions = () => {
  return useQuery({
    queryKey: rbacKeys.permissions,
    queryFn: async () => {
      const response = await rbacService.getPermissions();
      return response.data ?? [];
    },
    staleTime: 10 * 60 * 1000, // 10 minutes - rarely changes
  });
};

// Role Mutations
export const useCreateRole = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: RoleCreate) => rbacService.createRole(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: rbacKeys.roles });
    },
  });
};

export const useUpdateRole = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: RoleUpdate }) => 
      rbacService.updateRole(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: rbacKeys.roles });
    },
  });
};

export const useDeleteRole = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: number) => rbacService.deleteRole(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: rbacKeys.roles });
    },
  });
};

// Permission Mutations
export const useCreatePermission = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: PermissionCreate) => rbacService.createPermission(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: rbacKeys.permissions });
    },
  });
};

export const useUpdatePermission = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: PermissionUpdate }) => 
      rbacService.updatePermission(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: rbacKeys.permissions });
    },
  });
};

export const useDeletePermission = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: number) => rbacService.deletePermission(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: rbacKeys.permissions });
    },
  });
};

// Role-Permission Linking
export const useAddPermissionToRole = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ roleId, permId }: { roleId: number; permId: number }) => 
      rbacService.addPermissionToRole(roleId, permId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: rbacKeys.roles });
    },
  });
};

export const useRemovePermissionFromRole = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ roleId, permId }: { roleId: number; permId: number }) => 
      rbacService.removePermissionFromRole(roleId, permId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: rbacKeys.roles });
    },
  });
};
