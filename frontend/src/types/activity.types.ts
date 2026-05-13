import type { MeetingResponse } from './meeting.types';
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
    owner?: UserRef;
    created_at: string;
    updated_at: string;

    creator?: UserRef;
    updater?: UserRef;
    
    // Nested related entities
    homework?: Homework;
    meeting?: MeetingResponse;
}

export interface UserRef {
    id: number;
    name: string;
    avatar_url: string | null;
}

export interface BonusPointResponse {
    id: number;
    points: number;
    reason: string;
    date: string;
    user_id: number;
    owner?: UserRef;
    created_by?: number;
    updated_by?: number;
    created_at: string;
    updated_at: string;

    creator?: UserRef;
    updater?: UserRef;
}


export interface ViolationResponse {
    id: number;
    reason: string;
    date: string;
    user_id: number;
    owner?: UserRef;
    creator?: UserRef;
    updater?: UserRef;
    created_by?: number;
    updated_by?: number;
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
