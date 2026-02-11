import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiKeyService, type CreateApiKeyDto } from '../services/api/api-key.service';
import { message } from 'antd';

export const useRoleApiKeys = (roleId: number | null) => {
    return useQuery({
        queryKey: ['roleApiKeys', roleId],
        queryFn: () => apiKeyService.getByRole(roleId!),
        enabled: !!roleId,
        select: (data) => data.data // Extract data from ApiResponse
    });
};

export const useCreateApiKey = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (data: CreateApiKeyDto) => apiKeyService.create(data),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['roleApiKeys', variables.role_id] });
            message.success('API Key created successfully');
        },
        onError: (error: any) => {
            message.error(error?.response?.data?.message || 'Failed to create API Key');
        }
    });
};

export const useRevokeApiKey = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (keyId: number) => apiKeyService.revoke(keyId),
        onSuccess: (_, keyId) => {
             // We need to invalidate, but we don't know roleId here easily unless passed.
             // Invalidating all 'roleApiKeys' is safe enough or we can refetch active query.
             queryClient.invalidateQueries({ queryKey: ['roleApiKeys'] });
             message.success('API Key revoked successfully');
        },
        onError: (error: any) => {
            message.error(error?.response?.data?.message || 'Failed to revoke API Key');
        }
    });
};
