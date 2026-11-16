export type DutyStatus = 'PENDING' | 'AWAITING_APPROVAL' | 'COMPLETED' | 'REJECTED' | 'VIOLATED' | 'CANCELLED';

export interface DutyChecklistItem {
  id: string;
  title: string;
  checked: boolean;
  assignee_id?: number | null;
  assignee_name?: string | null;
  status?: 'PENDING' | 'APPROVED' | 'REJECTED';
  rejection_reason?: string | null;
}

export interface TeamCandidateMember {
  id: number;
  name: string;
  email?: string | null;
  avatar_url?: string | null;
  served?: boolean;
}

export interface DutyCandidatesResponse {
  team_id: number;
  team_name: string;
  current_round: number;
  total_members: number;
  all_members: TeamCandidateMember[];
  available_members: TeamCandidateMember[];
}

export interface DutyResponse {
  id: number;
  duty_date: string;
  start_time?: string | null;
  end_time?: string | null;
  team_id: number | number[];
  team_name: string | null;
  team_names?: string[];
  meeting_id: number | null;
  meeting_title: string | null;
  status: DutyStatus;
  checklist: DutyChecklistItem[];
  note: string | null;
  evidence_image_urls: string[];
  submitted_by: number | null;
  submitted_by_name: string | null;
  submitted_at: string | null;
  rejection_reason?: string | null;
  approved_by?: number | null;
  approved_at?: string | null;
  rejected_by?: number | null;
  rejected_at?: string | null;
}

export interface WeeklyDutyClassDto {
  team_id: number | number[];
  team_name: string;
  team_names?: string[];
  day_of_week: number;
  day_name: string;
  duty_date: string;
  start_time?: string | null;
  end_time?: string | null;
  is_time_conflict?: boolean;
  conflict_message?: string | null;
  has_meeting?: boolean;
  meeting_id: number | null;
  meeting_title: string | null;
  meeting_time?: string | null;
  is_scheduled: boolean;
  duty_id: number | null;
  status: DutyStatus | 'NO_MEETING' | 'NOT_SCHEDULED' | null;
  evidence_image_urls: string[];
  note: string | null;
  checklist: DutyChecklistItem[];
  submitted_by_name: string | null;
  rejection_reason?: string | null;
}

export interface ToggleDutyScheduleRequest {
  duty_date: string;
  team_id: number | number[];
  enabled: boolean;
  start_time?: string | null;
  end_time?: string | null;
  meeting_id?: number | null;
  checklist?: DutyChecklistItem[];
  note?: string | null;
  responsible_ids?: number[];
  random_round?: number;
}

export interface BatchCreateDutyRequest {
  team_ids: number[];
  duty_date: string;
  start_time?: string | null;
  end_time?: string | null;
  checklist?: DutyChecklistItem[];
  note?: string | null;
}

export interface UpdateDutyRequest {
  checklist?: DutyChecklistItem[];
  note?: string | null;
  duty_date?: string;
  start_time?: string | null;
  end_time?: string | null;
  team_id?: number;
}
