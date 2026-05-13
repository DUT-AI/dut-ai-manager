export const ParticipantStatus = {
    NOT_JOINED: "chưa tham gia",
    JOINED: "đã checkin"
} as const;
export type ParticipantStatus = typeof ParticipantStatus[keyof typeof ParticipantStatus];

export interface MeetingCreate {
    title: string;
    content?: string;
    start_time: string; // ISO string
    end_time: string;   // ISO string
    require_check_in?: boolean;
    team_ids?: number[];
    user_ids?: number[];
}

export interface MeetingUpdate extends Partial<MeetingCreate> {}

export interface ParticipantResponse {
    id: number;
    meeting_id: number;
    user_id: number;
    user_name?: string;
    user_avatar_url?: string;
    check_in_at?: string;
    check_out_at?: string;
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
    require_check_in: boolean;
    participants: ParticipantResponse[];
    created_at: string;
    updated_at: string;
}
