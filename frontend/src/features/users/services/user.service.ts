import axiosInstance from '../../../services/axiosInstance';
import type { ApiResponse } from '@/types/api.types';
import type { UserResponse, UserCreate, UserUpdate, UserSettingsUpdate, UserImportResult } from '@/features/users/types/user.types';

export const userService = {
  getUsers: async () => {
    const response = await axiosInstance.get<ApiResponse<UserResponse[]>>('/users');
    return response.data;
  },

  getUser: async (id: number) => {
    const response = await axiosInstance.get<ApiResponse<UserResponse>>(`/users/${id}`);
    return response.data;
  },

  createUser: async (data: UserCreate) => {
    const response = await axiosInstance.post<ApiResponse<UserResponse>>('/users', data);
    return response.data;
  },

  updateUser: async (id: number, data: UserUpdate) => {
    const response = await axiosInstance.put<ApiResponse<UserResponse>>(`/users/${id}`, data);
    return response.data;
  },

  updateSettings: async (data: UserSettingsUpdate) => {
    const response = await axiosInstance.put<ApiResponse<UserResponse>>('/users/me/settings', data);
    return response.data;
  },

  updateAvatar: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await axiosInstance.post<ApiResponse<UserResponse>>('/users/me/avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  importUsers: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await axiosInstance.post<ApiResponse<UserImportResult>>('/users/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  downloadTemplate: async () => {
    const response = await axiosInstance.get('/users/template', {
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'user_import_template.xlsx');
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  deleteUser: async (id: number) => {
    const response = await axiosInstance.delete<ApiResponse<null>>(`/users/${id}`);
    return response.data;
  },
};
