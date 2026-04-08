import type { MeetingResponse } from './meeting.types';
import type { UserResponse } from './user.types';
import type { Homework } from './homework.types';

export interface PermissionCreate {
    category: string;
    note: string;
    start_time?: string; // HH:MM:SS
    homework_id?: number;
    meeting_id?: number;
}

export interface PermissionUpdate extends Partial<PermissionCreate> {}

export interface BonusPointCreate {
    user_ids: number[];
    points: number;
    reason: string;
    date: string; // ISO Datetime
}

export interface BonusPointUpdate extends Partial<BonusPointCreate> {}

export interface ViolationCreate {
    user_ids: number[];
    reason: string;
    date: string; // ISO Datetime
}

export interface ViolationUpdate extends Partial<ViolationCreate> {}

export interface PermissionRequestResponse {
    id: number;
    category: string;
    note: string;
    start_time: string;
    homework_id?: number;
    meeting_id?: number;
    created_by?: number;
    updated_by?: number;
    user_name?: string;
    user_avatar?: string;
    creator_name?: string;
    updater_name?: string;
    created_at: string;
    updated_at: string;
    
    // Nested related entities
    user?: UserResponse;
    homework?: Homework;
    meeting?: MeetingResponse;
}

export interface BonusPointResponse {
    id: number;
    points: number;
    reason: string;
    date: string;
    user_id: number;
    user_name?: string;
    user_avatar?: string;
    created_by?: number;
    updated_by?: number;
    creator_name?: string;
    updater_name?: string;
    created_at: string;
    updated_at: string;
}

export interface UserBrief {
    id: number;
    name: string;
    avatar: string;
}

export interface ViolationResponse {
    id: number;
    reason: string;
    date: string;
    user_id: number;
    user_name?: string;
    user_avatar?: string;
    owner?: UserBrief;
    creator?: UserBrief;
    updater?: UserBrief;
    created_by?: number;
    updated_by?: number;
    creator_name?: string;
    updater_name?: string;
    created_at: string;
    updated_at: string;
}

export interface DailySummaryResponse {
    date: string;
    permission_requests: PermissionRequestResponse[];
    bonus_points: BonusPointResponse[];
    violations: ViolationResponse[];
    meetings: MeetingResponse[];
}
