import { z } from 'zod';
import { userRefSchema } from '../../activity/types/activity.types';

export const HomeworkStatus = {
  NOT_SUBMITTED: 'NOT_SUBMITTED',
  SUBMITTED: 'SUBMITTED',
  LeaderChecked: 'LEADER_CHECKED',
  FINISHED: 'FINISHED',
} as const;

export type HomeworkStatus = typeof HomeworkStatus[keyof typeof HomeworkStatus];
export const homeworkStatusSchema = z.enum([
  'NOT_SUBMITTED',
  'SUBMITTED',
  'LEADER_CHECKED',
  'FINISHED',
]);

export const scoreDetailSchema = z.object({
  id: z.number(),
  criterion: z.string(),
  status: z.boolean(),
  description: z.string(),
  weight: z.number(),
});
export type ScoreDetail = z.infer<typeof scoreDetailSchema>;

export const homeworkSubmissionSchema = z.object({
  id: z.number(),
  homework_id: z.number(),
  owner_id: z.number(),
  owner: userRefSchema.nullable().optional(),
  created_by: z.number().nullable().optional(),
  link: z.string(),
  status: homeworkStatusSchema,
  is_late: z.boolean(),
  is_pass: z.boolean().nullable().optional(),
  score: z.number().nullable().optional(),
  feedback: z.string().nullable().optional(),
  is_plagiarized: z.boolean().optional(),
  plagiarized_from_user_id: z.number().nullable().optional(),
  scores: z.array(scoreDetailSchema).optional(),
  submitted_at: z.string().optional(),
});
export type HomeworkSubmission = z.infer<typeof homeworkSubmissionSchema>;

export const homeworkSchema = z.object({
  id: z.number(),
  title: z.string(),
  deadline: z.string(),
  link: z.string().nullable().optional(),
  slug: z.string().nullable().optional(),
  requires_coding: z.boolean().optional(),
  requires_game: z.boolean().optional(),
  assignee_ids: z.array(z.number()).optional(),
  created_at: z.string(),
  updated_at: z.string(),
  created_by: z.number().optional(),
  submission_count: z.number().optional(),
  is_submitted: z.boolean().nullable().optional(),
  is_overdue: z.boolean().nullable().optional(),
  has_coding: z.boolean().optional(),
  coding_submitted: z.boolean().optional(),
  has_game: z.boolean().optional(),
  game_submitted: z.boolean().optional(),
  uncompleted_items: z.array(z.string()).optional(),
  submissions: z.array(homeworkSubmissionSchema).optional(),
});
export type Homework = z.infer<typeof homeworkSchema>;

export const homeworkCreateSchema = z.object({
  title: z.string().min(1, 'Vui lòng nhập tiêu đề bài tập'),
  deadline: z.string().min(1, 'Vui lòng chọn hạn nộp'),
  link: z.string().optional(),
  slug: z.string().optional(),
  requires_coding: z.boolean().optional(),
  requires_game: z.boolean().optional(),
  assignee_ids: z.array(z.number()).optional(),
});
export type HomeworkCreate = z.infer<typeof homeworkCreateSchema>;

export type CreateHomeworkFormValues = HomeworkCreate;

export const homeworkUpdateSchema = homeworkCreateSchema.partial();
export type HomeworkUpdate = z.infer<typeof homeworkUpdateSchema>;
export type UpdateHomeworkFormValues = HomeworkUpdate;


export const homeworkSubmitSchema = z.object({
  link: z.string().url('Vui lòng nhập đường dẫn URL hợp lệ'),
});
export type HomeworkSubmit = z.infer<typeof homeworkSubmitSchema>;

export const scoreItemSchema = z.object({
  criterion: z.string(),
  status: z.boolean(),
  description: z.string(),
  weight: z.number(),
});
export type ScoreItem = z.infer<typeof scoreItemSchema>;

export const homeworkCheckSchema = z.object({
  is_pass: z.boolean(),
  feedback: z.string().optional(),
  scores: z.array(scoreItemSchema).optional(),
});
export type HomeworkCheck = z.infer<typeof homeworkCheckSchema>;

export const homeworkReportResponseSchema = z.object({
  user_id: z.number(),
  owner: userRefSchema.nullable().optional(),
  unsubmitted_count: z.number(),
});
export type HomeworkReportResponse = z.infer<typeof homeworkReportResponseSchema>;

export const exerciseSummarySchema = z.object({
  id: z.string(),
  title: z.string(),
  order_index: z.number().optional(),
});
export type ExerciseSummary = z.infer<typeof exerciseSummarySchema>;

export const studentExerciseStatusSchema = z.object({
  exercise_id: z.string(),
  exercise_title: z.string().nullable().optional(),
  is_submitted: z.boolean().default(false),
  submitted_at: z.string().nullable().optional(),
  is_late: z.boolean().default(false),
  score: z.number().nullable().optional(),
  attempt_number: z.number().default(1),
});
export type StudentExerciseStatus = z.infer<typeof studentExerciseStatusSchema>;

export const userSubmissionInfoSchema = z.object({
  user_id: z.number(),
  name: z.string().nullable().optional(),
  avatar_url: z.string().nullable().optional(),
  is_late: z.boolean().optional(),
  submitted_at: z.string().nullable().optional(),
  total_coding_required: z.number().optional(),
  total_coding_completed: z.number().optional(),
  coding_status: z.string().optional(),
  coding_exercises: z.array(studentExerciseStatusSchema).optional(),
});
export type UserSubmissionInfo = z.infer<typeof userSubmissionInfoSchema>;

export const categorySubmissionStatusSchema = z.object({
  submitted: z.array(userSubmissionInfoSchema),
  not_submitted: z.array(userSubmissionInfoSchema),
});
export type CategorySubmissionStatus = z.infer<typeof categorySubmissionStatusSchema>;

export const studentHomeworkDetailSchema = z.object({
  user_id: z.number(),
  name: z.string().nullable().optional(),
  avatar_url: z.string().nullable().optional(),
  total_coding_required: z.number().default(0),
  total_coding_completed: z.number().default(0),
  coding_status: z.string().default('NOT_SUBMITTED'),
  coding_is_late: z.boolean().default(false),
  coding_exercises: z.array(studentExerciseStatusSchema).default([]),
  game_is_submitted: z.boolean().default(false),
  game_is_late: z.boolean().default(false),
  game_submitted_at: z.string().nullable().optional(),
  game_score: z.number().nullable().optional(),
});
export type StudentHomeworkDetail = z.infer<typeof studentHomeworkDetailSchema>;

export const homeworkSubmissionStatusSchema = z.object({
  coding: categorySubmissionStatusSchema.optional(),
  game: categorySubmissionStatusSchema.optional(),
  coding_exercises: z.array(exerciseSummarySchema).optional(),
  students: z.array(studentHomeworkDetailSchema).optional(),
  submitted: z.array(userSubmissionInfoSchema).optional(),
  not_submitted: z.array(userSubmissionInfoSchema).optional(),
});
export type HomeworkSubmissionStatus = z.infer<typeof homeworkSubmissionStatusSchema>;

export interface SubmissionHistoryItem {
  id: number;
  homework_id: number;
  user_id: number;
  submission_type: 'CODING' | 'GAME';
  exercise_id?: string | null;
  exercise_title?: string | null;
  score?: number | null;
  attempt_number?: number;
  submitted_at: string;
  source?: string;
  details?: Record<string, any> | null;
  metadata?: Record<string, any> | null;
  is_passed?: boolean;
  created_at?: string;
}


