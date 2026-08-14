import axiosInstance from '@/services/axiosInstance';
import type { ApiResponse } from '@/types/api.types';
import type {
  PermissionRequestCreate,
  PermissionRequestUpdate,
  PermissionRequestResponse,
} from '@/types/permission.types';

export const permissionService = {
  subPath: 'permissions',

  async getPermissions(params?: {
    userId?: number;
    month?: number;
    year?: number;
    category?: string;
    deleted?: boolean;
    skip?: number;
    limit?: number;
  }): Promise<PermissionRequestResponse[]> {
    const response = await axiosInstance.get<ApiResponse<PermissionRequestResponse[]>>(
      `/${this.subPath}`,
      {
        params: {
          user_id: params?.userId,
          month: params?.month,
          year: params?.year,
          category: params?.category,
          deleted: params?.deleted,
          skip: params?.skip ?? 0,
          limit: params?.limit ?? 100,
        },
      }
    );
    return response.data.data || [];
  },

  async createPermission(data: PermissionRequestCreate): Promise<ApiResponse<PermissionRequestResponse>> {
    const response = await axiosInstance.post<ApiResponse<PermissionRequestResponse>>(
      `/${this.subPath}`,
      data
    );
    return response.data;
  },

  async updatePermission(
    id: number,
    data: PermissionRequestUpdate
  ): Promise<ApiResponse<PermissionRequestResponse>> {
    const response = await axiosInstance.put<ApiResponse<PermissionRequestResponse>>(
      `/${this.subPath}/${id}`,
      data
    );
    return response.data;
  },

  async deletePermission(id: number): Promise<ApiResponse<boolean>> {
    const response = await axiosInstance.delete<ApiResponse<boolean>>(`/${this.subPath}/${id}`);
    return response.data;
  },

  async restorePermission(id: number): Promise<ApiResponse<PermissionRequestResponse>> {
    const response = await axiosInstance.put<ApiResponse<PermissionRequestResponse>>(
      `/${this.subPath}/${id}/restore`
    );
    return response.data;
  },
};
