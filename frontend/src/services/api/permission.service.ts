import axiosInstance from '../axiosInstance';
import type { ApiResponse } from '@/types/api.types';
import type { 
  PermissionCreate,
  PermissionUpdate,
  PermissionRequestResponse,
} from '@/types/activity.types';

export const permissionService = {
  subPath: 'permissions',

  async getPermissions(userId?: number, month?: number, year?: number) {
    const response = await axiosInstance.get<ApiResponse<PermissionRequestResponse[]>>(`/${this.subPath}`, {
        params: { user_id: userId, month, year }
    });
    return response.data;
  },

  async createPermission(data: PermissionCreate) {
    const response = await axiosInstance.post<ApiResponse<PermissionRequestResponse>>(`/${this.subPath}`, data);
    return response.data;
  },
  
  async updatePermission(id: number, data: PermissionUpdate) {
    const response = await axiosInstance.put<ApiResponse<PermissionRequestResponse>>(`/${this.subPath}/${id}`, data);
    return response.data;
  },

  async deletePermission(id: number) {
    const response = await axiosInstance.delete<ApiResponse<boolean>>(`/${this.subPath}/${id}`);
    return response.data;
  },
};
