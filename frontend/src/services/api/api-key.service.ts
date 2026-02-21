import axiosInstance from '../axiosInstance';
import type { ApiResponse } from '@/types/api.types';

interface RoleApiKey {
    id: number;
    name: string;
    prefix: string;
    is_active: boolean;
    created_at: string;
    role_id: number;
}

export interface RoleApiKeySecret extends RoleApiKey {
    secret_key: string;
}

export interface CreateApiKeyDto {
    name: string;
    role_id: number;
}

export const apiKeyService = {
    create: async (data: CreateApiKeyDto): Promise<ApiResponse<RoleApiKeySecret>> => {
        const response = await axiosInstance.post<ApiResponse<RoleApiKeySecret>>('/api-keys', data);
        return response.data;
    },

    getByRole: async (roleId: number): Promise<ApiResponse<RoleApiKey[]>> => {
        const response = await axiosInstance.get<ApiResponse<RoleApiKey[]>>(`/api-keys/role/${roleId}`);
        return response.data;
    },

    revoke: async (keyId: number): Promise<ApiResponse<null>> => {
        const response = await axiosInstance.delete<ApiResponse<null>>(`/api-keys/${keyId}`);
        return response.data;
    },
};
