import axiosInstance from '../axiosInstance';
import type { ApiResponse } from '@/types/api.types';
import type { 
  RoleResponse, 
  RoleCreate, 
  RoleUpdate, 
  PermissionResponse, 
  PermissionCreate, 
  PermissionUpdate 
} from '@/types/rbac.types';

export const rbacService = {
  // Roles
  getRoles: async (): Promise<ApiResponse<RoleResponse[]>> => {
    const response = await axiosInstance.get<ApiResponse<RoleResponse[]>>('/rbac/roles');
    return response.data;
  },

  createRole: async (data: RoleCreate): Promise<ApiResponse<RoleResponse>> => {
    const response = await axiosInstance.post<ApiResponse<RoleResponse>>('/rbac/roles', data);
    return response.data;
  },

  updateRole: async (id: number, data: RoleUpdate): Promise<ApiResponse<RoleResponse>> => {
    const response = await axiosInstance.put<ApiResponse<RoleResponse>>(`/rbac/roles/${id}`, data);
    return response.data;
  },

  deleteRole: async (id: number): Promise<ApiResponse<null>> => {
    const response = await axiosInstance.delete<ApiResponse<null>>(`/rbac/roles/${id}`);
    return response.data;
  },

  // Permissions
  getPermissions: async (): Promise<ApiResponse<PermissionResponse[]>> => {
    const response = await axiosInstance.get<ApiResponse<PermissionResponse[]>>('/rbac/permissions');
    return response.data;
  },

  createPermission: async (data: PermissionCreate): Promise<ApiResponse<PermissionResponse>> => {
    const response = await axiosInstance.post<ApiResponse<PermissionResponse>>('/rbac/permissions', data);
    return response.data;
  },

  updatePermission: async (id: number, data: PermissionUpdate): Promise<ApiResponse<PermissionResponse>> => {
    const response = await axiosInstance.put<ApiResponse<PermissionResponse>>(`/rbac/permissions/${id}`, data);
    return response.data;
  },

  deletePermission: async (id: number): Promise<ApiResponse<null>> => {
    const response = await axiosInstance.delete<ApiResponse<null>>(`/rbac/permissions/${id}`);
    return response.data;
  },

  // Linking
  addPermissionToRole: async (roleId: number, permId: number): Promise<ApiResponse<null>> => {
    const response = await axiosInstance.post<ApiResponse<null>>(`/rbac/roles/${roleId}/permissions/${permId}`);
    return response.data;
  },

  removePermissionFromRole: async (roleId: number, permId: number): Promise<ApiResponse<null>> => {
    const response = await axiosInstance.delete<ApiResponse<null>>(`/rbac/roles/${roleId}/permissions/${permId}`);
    return response.data;
  },
};
