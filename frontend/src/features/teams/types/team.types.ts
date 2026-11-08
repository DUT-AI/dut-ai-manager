import type { Schema } from '@/types/api';

export type TeamMember = Schema<'TeamMemberResponse'>;
export type TeamResponse = Schema<'TeamResponse'>;

export type TeamCreate = Schema<'TeamCreate'>;
export type CreateTeamFormValues = TeamCreate;

export type TeamUpdate = Schema<'TeamUpdate'>;
export type UpdateTeamFormValues = TeamUpdate;
