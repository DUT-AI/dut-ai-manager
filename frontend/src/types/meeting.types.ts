export enum ParticipantStatus {
    NOT_JOINED = "chưa tham gia",
    JOINED = "đã checkin"
}

export interface MeetingCreate {
    title: string;
    content?: string;
    start_time: string; // ISO string
    end_time: string;   // ISO string
    team_ids?: number[];
    user_ids?: number[];
}

export interface MeetingUpdate extends Partial<MeetingCreate> {}

export interface ParticipantResponse {
    id: number;
    meeting_id: number;
    user_id: number;
    user_name?: string;
    user_avatar?: string;
    check_in_at?: string;
    status: ParticipantStatus;
    link_image?: string;
    created_at: string;
    updated_at: string;
}

export interface MeetingResponse {
    id: number;
    title: string;
    content?: string;
    start_time: string;
    end_time: string;
    participants: ParticipantResponse[];
    created_at: string;
    updated_at: string;
}
