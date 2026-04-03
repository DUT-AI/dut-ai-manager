import axiosInstance from '../axiosInstance';
import type { ApiResponse } from '@/types/api.types';
import { HomeworkStatus } from '@/types/homework.types';
import type { 
    Homework, 
    HomeworkCreate, 
    HomeworkSubmission, 
    HomeworkUpdate 
} from '@/types/homework.types';

export const homeworkService = {
    baseUrl: 'homeworks',
    submissionUrl: 'homework-submission',

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

    async create(data: HomeworkCreate & { file?: File }) {
        const formData = new FormData();
        formData.append('title', data.title);
        formData.append('description', data.description);
        formData.append('deadline', data.deadline);
        
        if (data.assignee_ids) {
            data.assignee_ids.forEach(id => formData.append('assignee_ids', id.toString()));
        }
        if (data.team_ids) {
            data.team_ids.forEach(id => formData.append('team_ids', id.toString()));
        }
        if (data.file) {
            formData.append('file', data.file);
        }

        const response = await axiosInstance.post<ApiResponse<Homework>>(`/${this.baseUrl}`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data.data;
    },
    
    async update(id: number, data: HomeworkUpdate & { file?: File }) {
        const formData = new FormData();
        // Title is mandatory now
        if (data.title) formData.append('title', data.title);
        if (data.description) formData.append('description', data.description);
        if (data.deadline) formData.append('deadline', typeof data.deadline === 'string' ? data.deadline : (data.deadline as any).toISOString());
        
        if (data.assignee_ids) {
            data.assignee_ids.forEach(id => formData.append('assignee_ids', id.toString()));
        }
        if (data.team_ids) {
            data.team_ids.forEach(id => formData.append('team_ids', id.toString()));
        }
        if (data.file) {
            formData.append('file', data.file);
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

    // Submissions
    async submit(homeworkId: number, file: File) {
        const formData = new FormData();
        formData.append('homework_id', homeworkId.toString());
        formData.append('file', file);
        const response = await axiosInstance.post<ApiResponse<HomeworkSubmission>>(
            `/${this.submissionUrl}`,
            formData,
            {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            }
        );
        return response.data.data;
    },

    async getSubmissions(homeworkId: number) {
        const response = await axiosInstance.get<ApiResponse<HomeworkSubmission[]>>(`/${this.submissionUrl}`, {
            params: { homework_id: homeworkId }
        });
        return response.data.data;
    },

    async getMySubmission(homeworkId: number) {
        // Return null data if 404 handled gracefully or rely on try-catch in component
        const response = await axiosInstance.get<ApiResponse<HomeworkSubmission>>(`/${this.submissionUrl}/me`, {
            params: { homework_id: homeworkId }
        });
        return response.data.data;
    },

    async updateStatus(submissionId: number, status: HomeworkStatus) {
        const response = await axiosInstance.put<ApiResponse<HomeworkSubmission>>(`/${this.submissionUrl}/${submissionId}/status`, null, { 
            params: { status } 
        });
        return response.data.data;
    }
};
