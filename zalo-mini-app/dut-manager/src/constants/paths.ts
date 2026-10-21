export const PATHS = {
  // Main Tabs
  HOME: '/',
  CALENDAR: '/calendar',
  NOTIFICATIONS: '/notifications',
  PROFILE: '/profile',

  // Auth
  LOGIN: '/login',

  // Features / Sub-routes
  SHORTCUTS: '/shortcuts',
  ACADEMIC_REPORTS: '/academic-reports',
  ACTIVITY_REPORTS: '/activity-reports',
  ACTIVITIES: '/activities',
  MEETINGS: '/meetings',
  MEETING_DETAIL: '/meetings/:id',
  PERMISSIONS: '/permissions',
  VIOLATIONS: '/violations',
  HOMEWORKS: '/homeworks',
  INVOICES: '/invoices',
  SETTINGS: '/settings',

  // Admin / Leader features
  USERS: '/users',
  TEAMS: '/teams',
  RBAC: '/rbac',
  ADMIN_BILLING: '/admin-billing',
} as const;

export const TAB_PATHS: Record<string, string> = {
  home: PATHS.HOME,
  calendar: PATHS.CALENDAR,
  notifications: PATHS.NOTIFICATIONS,
  profile: PATHS.PROFILE,
};

export const PATH_TO_TAB: Record<string, string> = {
  [PATHS.HOME]: 'home',
  [PATHS.CALENDAR]: 'calendar',
  [PATHS.NOTIFICATIONS]: 'notifications',
  [PATHS.PROFILE]: 'profile',
};
