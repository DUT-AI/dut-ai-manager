import axiosInstance from '../axiosInstance';
import type { ApiResponse } from '@/types/api.types';
import type { UserResponse, UserCreate, UserUpdate } from '@/types/user.types';

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

  deleteUser: async (id: number) => {
    const response = await axiosInstance.delete<ApiResponse<null>>(`/users/${id}`);
    return response.data;
  },
};
