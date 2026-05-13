import type { UserRef } from './activity.types';

export const HomeworkStatus = {
    NOT_SUBMITTED: "chưa nộp",
    SUBMITTED: "đã nộp",
    LeaderChecked: "leader đã check",
    FINISHED: "finish"
} as const;

export type HomeworkStatus = typeof HomeworkStatus[keyof typeof HomeworkStatus];

export interface Homework {
    id: number;
    title: string;
    description: string;
    deadline: string;
    created_at: string;
    updated_at: string;
    created_by?: number;
    submission_count?: number;
    file_url?: string;
    submissions?: HomeworkSubmission[];
}

export interface HomeworkCreate {
    title: string;
    description: string;
    deadline: string; // ISO string
    assignee_ids?: number[];
    team_ids?: number[];
}

export interface HomeworkUpdate {
    title?: string;
    description?: string;
    deadline?: string;
    assignee_ids?: number[];
    team_ids?: number[];
}

export interface ScoreDetail {
    id: number;
    criterion: string;
    status: boolean;
    description: string;
    weight: number;
}

export interface HomeworkSubmission {
    id: number;
    homework_id: number;
    owner_id: number;
    owner?: UserRef;
    created_by?: number;
    link: string;
    status: HomeworkStatus;
    is_late: boolean;
    is_pass?: boolean | null;
    score?: number | null;
    feedback?: string | null;
    score_details?: ScoreDetail[] | null;
    plagiarism_info?: any[] | null;
    is_plagiarized: boolean;
    plagiarized_from_user_id?: number | null;
    created_at: string;
    updated_at: string;
}

export interface HomeworkSubmissionCreate {
    link: string;
}

export interface HomeworkReportResponse {
    user_id: number;
    owner?: UserRef;
    unsubmitted_count: number;
}
