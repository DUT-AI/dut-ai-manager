import axiosInstance from '@/services/axiosInstance';
import type { ApiResponse } from '@/types/api.types';
import type {
    Homework,
    HomeworkCreate,
    HomeworkUpdate,
    HomeworkReportResponse,
    HomeworkSubmissionStatus,
} from '@/features/homework/types/homework.types';

export const homeworkService = {
    baseUrl: 'homeworks',

    // Homeworks
    async getAll(skip = 0, limit = 100, deleted = false) {
        const response = await axiosInstance.get<ApiResponse<Homework[]>>(`/${this.baseUrl}`, {
            params: { skip, limit, deleted }
        });
        return response.data.data;
    },

    async getMyHomeworks(skip = 0, limit = 100) {
        const response = await axiosInstance.get<ApiResponse<Homework[]>>(`/${this.baseUrl}/me`, {
            params: { skip, limit }
        });
        return response.data.data;
    },

    async getById(id: number) {
        const response = await axiosInstance.get<ApiResponse<Homework>>(`/${this.baseUrl}/${id}`);
        return response.data.data;
    },

    async create(data: HomeworkCreate) {
        const response = await axiosInstance.post<ApiResponse<Homework>>(`/${this.baseUrl}`, data);
        return response.data.data;
    },

    async update(id: number, data: HomeworkUpdate) {
        const response = await axiosInstance.put<ApiResponse<Homework>>(`/${this.baseUrl}/${id}`, data);
        return response.data.data;
    },


    async delete(id: number) {
        const response = await axiosInstance.delete<ApiResponse<boolean>>(`/${this.baseUrl}/${id}`);
        return response.data.data;
    },

    async restore(id: number) {
        const response = await axiosInstance.put<ApiResponse<Homework>>(`/${this.baseUrl}/${id}/restore`);
        return response.data.data;
    },

    // Reports
    async getUnsubmittedReport() {
        const response = await axiosInstance.get<ApiResponse<HomeworkReportResponse[]>>(`/${this.baseUrl}/report/unsubmitted`);
        return response.data.data;
    },

    async getUnsubmittedByUser(userId: number) {
        const response = await axiosInstance.get<ApiResponse<Homework[]>>(`/${this.baseUrl}/report/unsubmitted/${userId}`);
        return response.data.data;
    },

    async getSubmissionStatus(homeworkId: number) {
        const response = await axiosInstance.get<ApiResponse<HomeworkSubmissionStatus>>(`/${this.baseUrl}/${homeworkId}/submission-status`);
        return response.data.data;
    },

};

