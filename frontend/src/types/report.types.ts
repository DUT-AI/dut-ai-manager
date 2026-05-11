import type { BonusPointResponse, PermissionRequestResponse, ViolationResponse } from "./activity.types";
import type { Homework } from "./homework.types";
import type { MeetingResponse } from "./meeting.types";

export interface DashboardOverviewResponse {
    permission_requests: PermissionRequestResponse[];
    bonus_points: BonusPointResponse[];
    violations: ViolationResponse[];
    unsubmitted_homeworks: Homework[];
    meetings: MeetingResponse[];
}

export interface ReportItem {
    rank: number;
    user: any; // Using any for now or UserResponse if imported, usually simplified object
    total_points: number;
    total_violations: number;
    details_count: number;
}

export interface ReportResponse {
    items: ReportItem[];
    month: number | null;
    year: number | null;
}

export interface TitleReportItem {
    user: {
        id: number;
        name: string;
        email: string;
        avatar_url?: string;
    };
    title: string | null;
    total_points: number;
    violation_count: number;
    hours: number;
}
