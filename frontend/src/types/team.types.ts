export interface TeamMemberResponse {
    user_id: number;
    user_name: string;
    email: string;
}

export interface TeamResponse {
    id: number;
    team_name: string;
    created_at: string;
    updated_at: string;
    member_count: number;
    members: TeamMemberResponse[];
}

export interface TeamCreate {
    team_name: string;
    member_ids?: number[];
}

export interface TeamUpdate extends Partial<TeamCreate> {}
