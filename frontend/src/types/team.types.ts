import { z } from 'zod';

export const teamMemberSchema = z.object({
  user_id: z.number(),
  user_name: z.string(),
  user_email: z.string().email(),
  user_avatar_url: z.string().nullable().optional(),
  joined_at: z.string().optional(),
});
export type TeamMember = z.infer<typeof teamMemberSchema>;

export const teamResponseSchema = z.object({
  id: z.number(),
  team_name: z.string(),
  created_at: z.string(),
  member_count: z.number().default(0),
  members: z.array(teamMemberSchema).default([]),
});
export type TeamResponse = z.infer<typeof teamResponseSchema>;

export const teamCreateSchema = z.object({
  team_name: z.string().min(1, 'Vui lòng nhập tên nhóm'),
  member_ids: z.array(z.number()).optional(),
});
export type TeamCreate = z.infer<typeof teamCreateSchema>;
export type CreateTeamFormValues = TeamCreate;

export const teamUpdateSchema = teamCreateSchema.partial();
export type TeamUpdate = z.infer<typeof teamUpdateSchema>;
export type UpdateTeamFormValues = TeamUpdate;
