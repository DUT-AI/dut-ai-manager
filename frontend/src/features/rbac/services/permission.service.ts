import axiosInstance from '../../../services/axiosInstance';
import type { ApiResponse } from '@/types/api.types';
import type {
  PermissionCreate,
  PermissionUpdate,
  PermissionRequestResponse,
} from '@/features/activity/types/activity.types';

export const permissionService = {
  subPath: 'permissions',

  async getPermissions(
    paramsOrUserId?:
      | {
          userId?: number;
          month?: number;
          year?: number;
          category?: string;
          deleted?: boolean;
          page?: number;
          pageSize?: number;
        }
      | number,
    month?: number,
    year?: number,
    category?: string,
    deleted?: boolean,
    page?: number,
    pageSize?: number
  ) {
    let params: Record<string, any> = {};
    if (typeof paramsOrUserId === 'object' && paramsOrUserId !== null) {
      params = {
        user_id: paramsOrUserId.userId,
        month: paramsOrUserId.month,
        year: paramsOrUserId.year,
        category: paramsOrUserId.category,
        deleted: paramsOrUserId.deleted,
        page: paramsOrUserId.page,
        page_size: paramsOrUserId.pageSize,
      };
    } else {
      params = {
        user_id: paramsOrUserId,
        month,
        year,
        category,
        deleted,
        page,
        page_size: pageSize,
      };
    }

    const response = await axiosInstance.get<ApiResponse<PermissionRequestResponse[]>>(`/${this.subPath}`, {
      params,
    });
    const items = response.data.data ?? [];
    if (response.data.pagination) {
      (items as any).pagination = response.data.pagination;
    }
    return items;
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

  async restorePermission(id: number) {
    const response = await axiosInstance.put<ApiResponse<PermissionRequestResponse>>(`/${this.subPath}/${id}/restore`);
    return response.data;
  },
};
