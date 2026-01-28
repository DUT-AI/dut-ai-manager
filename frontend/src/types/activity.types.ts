import type { MeetingResponse } from './meeting.types';
import type { UserResponse } from './user.types';

export interface PermissionCreate {
    category: string;
    note: string;
    date: string;       // YYYY-MM-DD
    start_time: string; // HH:MM:SS
    end_time: string;   // HH:MM:SS
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
    note: string;  // Not "reason"
    date: string;
    start_time: string;
    end_time: string;
    created_by?: number;
    updated_by?: number;
    user_name?: string;
    user_avatar?: string;
    creator_name?: string;
    updater_name?: string;
    created_at: string;
    updated_at: string;
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

export interface ViolationResponse {
    id: number;
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

export interface DailySummaryResponse {
    date: string;
    permission_requests: PermissionRequestResponse[];
    bonus_points: BonusPointResponse[];
    violations: ViolationResponse[];
    meetings: MeetingResponse[];
}
