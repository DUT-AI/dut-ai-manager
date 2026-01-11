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

export interface HomeworkSubmission {
    id: number;
    homework_id: number;
    owner_id: number;
    user_name?: string;
    created_by?: number;
    link: string;
    status: HomeworkStatus;
    is_late: boolean;
    created_at: string;
    updated_at: string;
}

export interface HomeworkSubmissionCreate {
    link: string;
}
