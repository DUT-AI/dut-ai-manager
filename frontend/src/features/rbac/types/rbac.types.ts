import { z } from 'zod';

export const RolePermission = {
  CREATE: 'role:create',
  READ: 'role:read',
  UPDATE: 'role:update',
  DELETE: 'role:delete',
} as const;

export const UserPermission = {
  CREATE: 'user:create',
  READ: 'user:read',
  UPDATE: 'user:update',
  DELETE: 'user:delete',
} as const;

export const BonusPointPermission = {
  CREATE: 'bonus_point:create',
  READ: 'bonus_point:read',
  UPDATE: 'bonus_point:update',
  DELETE: 'bonus_point:delete',
} as const;

export const ViolationPermission = {
  CREATE: 'violation:create',
  READ: 'violation:read',
  UPDATE: 'violation:update',
  DELETE: 'violation:delete',
} as const;

export const PermissionRequestPermission = {
  CREATE: 'permission_request:create',
  READ: 'permission_request:read',
  UPDATE: 'permission_request:update',
  DELETE: 'permission_request:delete',
} as const;

export const PermissionPermission = {
  CREATE: 'permission:create',
  READ: 'permission:read',
  UPDATE: 'permission:update',
  DELETE: 'permission:delete',
} as const;

export const TeamPermission = {
  CREATE: 'team:create',
  READ: 'team:read',
  UPDATE: 'team:update',
  DELETE: 'team:delete',
} as const;

export const TeamMemberPermission = {
  CREATE: 'team_member:create',
  READ: 'team_member:read',
  UPDATE: 'team_member:update',
  DELETE: 'team_member:delete',
} as const;

export const HomeworkPermission = {
  CREATE: 'homework:create',
  READ: 'homework:read',
  UPDATE: 'homework:update',
  DELETE: 'homework:delete',
} as const;

export const HomeworkSubmissionPermission = {
  CREATE: 'homework_submission:create',
  READ: 'homework_submission:read',
  UPDATE: 'homework_submission:update',
  DELETE: 'homework_submission:delete',
} as const;

export const BillingPermission = {
  CREATE: 'billing:create',
  READ: 'billing:read',
  MY_INVOICES: 'billing:my_invoices',
  DELETE: 'billing:delete',
} as const;

export const permissionResponseSchema = z.object({
  id: z.number(),
  name: z.string(),
  description: z.string().nullable().optional(),
  resource: z.string(),
  action: z.string(),
});
export type PermissionResponse = z.infer<typeof permissionResponseSchema>;

export const roleResponseSchema = z.object({
  id: z.number(),
  name: z.enum(['admin', 'leader', 'teammate']).or(z.string()),
  description: z.string().nullable().optional(),
  permissions: z.array(permissionResponseSchema).default([]),
});
export type RoleResponse = z.infer<typeof roleResponseSchema>;

export const roleCreateSchema = z.object({
  name: z.string().min(1, 'Vui lòng nhập tên vai trò'),
  description: z.string().optional(),
});
export type RoleCreate = z.infer<typeof roleCreateSchema>;

export const roleUpdateSchema = roleCreateSchema.partial();
export type RoleUpdate = z.infer<typeof roleUpdateSchema>;

export const permissionCreateSchema = z.object({
  name: z.string().min(1, 'Vui lòng nhập tên quyền'),
  description: z.string().optional(),
  resource: z.string().min(1, 'Vui lòng nhập resource'),
  action: z.string().min(1, 'Vui lòng nhập action'),
});
export type PermissionCreate = z.infer<typeof permissionCreateSchema>;

export const permissionUpdateSchema = permissionCreateSchema.partial();
export type PermissionUpdate = z.infer<typeof permissionUpdateSchema>;
