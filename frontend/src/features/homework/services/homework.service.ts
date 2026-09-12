import axiosInstance from '@/services/axiosInstance';
import type { ApiResponse } from '@/types/api.types';
import { HomeworkStatus } from '@/features/homework/types/homework.types';
import type {
    Homework,
    HomeworkCreate,
    HomeworkSubmission,
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

    async getById(id: number) {
        const response = await axiosInstance.get<ApiResponse<Homework>>(`/${this.baseUrl}/${id}`);
        return response.data.data;
    },

    async create(data: HomeworkCreate) {
        const formData = new FormData();
        formData.append('title', data.title);
        formData.append('deadline', data.deadline);
        if (data.link) formData.append('link', data.link);
        if (data.slug) formData.append('slug', data.slug);
        if (data.assignee_ids && data.assignee_ids.length > 0) {
            data.assignee_ids.forEach(id => formData.append('assignee_ids', String(id)));
        }
        if (data.team_ids && data.team_ids.length > 0) {
            data.team_ids.forEach(id => formData.append('team_ids', String(id)));
        }

        const response = await axiosInstance.post<ApiResponse<Homework>>(`/${this.baseUrl}`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data.data;
    },

    async update(id: number, data: HomeworkUpdate) {
        const formData = new FormData();
        if (data.title) formData.append('title', data.title);
        if (data.deadline) formData.append('deadline', typeof data.deadline === 'string' ? data.deadline : (data.deadline as { toISOString: () => string }).toISOString());
        if (data.link !== undefined) formData.append('link', data.link || '');
        if (data.slug !== undefined) formData.append('slug', data.slug || '');
        if (data.assignee_ids !== undefined) {
            if (data.assignee_ids.length === 0) {
                formData.append('assignee_ids', '[]');
            } else {
                data.assignee_ids.forEach(id => formData.append('assignee_ids', String(id)));
            }
        }
        if (data.team_ids !== undefined) {
            if (data.team_ids.length === 0) {
                formData.append('team_ids', '[]');
            } else {
                data.team_ids.forEach(id => formData.append('team_ids', String(id)));
            }
        }

        const response = await axiosInstance.put<ApiResponse<Homework>>(`/${this.baseUrl}/${id}`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
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

