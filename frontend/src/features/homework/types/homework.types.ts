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
  description: z.string(),
  deadline: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
  created_by: z.number().optional(),
  submission_count: z.number().optional(),
  file_url: z.string().optional(),
  submissions: z.array(homeworkSubmissionSchema).optional(),
});
export type Homework = z.infer<typeof homeworkSchema>;

export const homeworkCreateSchema = z.object({
  title: z.string().min(1, 'Vui lòng nhập tiêu đề bài tập'),
  description: z.string().min(1, 'Vui lòng nhập mô tả'),
  deadline: z.string().min(1, 'Vui lòng chọn hạn nộp'),
  assignee_ids: z.array(z.number()).optional(),
  team_ids: z.array(z.number()).optional(),
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
