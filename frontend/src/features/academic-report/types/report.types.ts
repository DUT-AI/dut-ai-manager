import { z } from 'zod';
import { bonusPointResponseSchema, permissionRequestResponseSchema, userRefSchema } from '../../activity/types/activity.types';
import { violationResponseSchema } from '../../violations/types/violation.types';
import { homeworkSchema } from '../../homework/types/homework.types';
import { meetingResponseSchema } from '../../meeting/types/meeting.types';
import { userResponseSchema } from '../../users/types/user.types';

export const dashboardOverviewResponseSchema = z.object({
  permission_requests: z.array(permissionRequestResponseSchema).default([]),
  bonus_points: z.array(bonusPointResponseSchema).default([]),
  violations: z.array(violationResponseSchema).default([]),
  unsubmitted_homeworks: z.array(homeworkSchema).default([]),
  meetings: z.array(meetingResponseSchema).default([]),
});
export type DashboardOverviewResponse = z.infer<typeof dashboardOverviewResponseSchema>;

export const reportItemSchema = z.object({
  rank: z.number(),
  user: userResponseSchema,
  total_points: z.number(),
  total_violations: z.number(),
  details_count: z.number(),
});
export type ReportItem = z.infer<typeof reportItemSchema>;

export const reportResponseSchema = z.object({
  items: z.array(reportItemSchema).default([]),
  month: z.number().nullable().optional(),
  year: z.number().nullable().optional(),
});
export type ReportResponse = z.infer<typeof reportResponseSchema>;

export const titleReportItemSchema = z.object({
  user: userRefSchema,
  title: z.string().nullable().optional(),
  total_points: z.number(),
  violation_count: z.number(),
  hours: z.number(),
});
export type TitleReportItem = z.infer<typeof titleReportItemSchema>;

export const participationStatsSchema = z.object({
  user_id: z.number(),
  user: userRefSchema.nullable().optional(),
  total_points: z.number(),
  total_bonus_points: z.number(),
  violation_count: z.number(),
  month: z.number(),
  year: z.number(),
  total_sessions: z.number(),
  total_hours: z.number(),
  weekly_frequency: z.number(),
  current_streak: z.number(),
  longest_streak: z.number(),
  on_time_rate: z.number(),
  late_count: z.number(),
  absent_count: z.number(),
});
export type ParticipationStats = z.infer<typeof participationStatsSchema>;

export const activityTrendItemSchema = z.object({
  label: z.string(),
  total_bonus_points: z.number(),
  violation_count: z.number(),
});
export type ActivityTrendItem = z.infer<typeof activityTrendItemSchema>;
