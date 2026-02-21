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


export interface PermissionResponse {
  id: number;
  name: string;
  description: string | null;
  resource: string;
  action: string;
}

export interface RoleResponse {
  id: number;
  name: 'admin' | 'leader' | 'teammate';
  description: string | null;
  permissions: PermissionResponse[];
}

export interface RoleCreate {
  name: string;
  description?: string;
}

export interface RoleUpdate {
  name?: string;
  description?: string;
}

export interface PermissionCreate {
  name: string;
  description?: string;
  resource: string;
  action: string;
}

export interface PermissionUpdate {
  name?: string;
  description?: string;
  resource?: string;
  action?: string;
}
