import axiosInstance from '@/services/axiosInstance';
import type { ApiResponse } from '@/types/api.types';

export interface PushPublicKeyResponse {
  public_key: string;
}

export interface PushSubscriptionKeys {
  p256dh: string;
  auth: string;
}

export interface RegisterPushSubscriptionRequest {
  endpoint: string;
  keys: PushSubscriptionKeys;
  user_agent?: string;
}

export interface RegisterPushSubscriptionResponse {
  subscription_id: number;
  is_active: boolean;
}

export interface TestPushResponse {
  sent_count: number;
  failed_count: number;
}

export const pushService = {
  getPushPublicKey: async (): Promise<ApiResponse<PushPublicKeyResponse>> => {
    const response = await axiosInstance.get<ApiResponse<PushPublicKeyResponse>>(
      '/notifications/push-public-key'
    );
    return response.data;
  },

  registerSubscription: async (
    data: RegisterPushSubscriptionRequest
  ): Promise<ApiResponse<RegisterPushSubscriptionResponse>> => {
    const response = await axiosInstance.post<ApiResponse<RegisterPushSubscriptionResponse>>(
      '/notifications/push-subscriptions',
      data
    );
    return response.data;
  },

  unregisterSubscription: async (endpoint: string): Promise<ApiResponse<null>> => {
    const response = await axiosInstance.delete<ApiResponse<null>>(
      '/notifications/push-subscriptions',
      { data: { endpoint } }
    );
    return response.data;
  },

  testPush: async (): Promise<ApiResponse<TestPushResponse>> => {
    const response = await axiosInstance.post<ApiResponse<TestPushResponse>>(
      '/notifications/test-push'
    );
    return response.data;
  },
};
