import type { Schema } from '@/types/api';

export type UserRef = Schema<'UserRef'>;

export type PermissionRequestCreate = Schema<'PermissionRequestCreate'>;
export type PermissionRequestUpdate = Partial<PermissionRequestCreate>;

// Aliases for legacy code
export type PermissionCreate = PermissionRequestCreate;
export type PermissionUpdate = PermissionRequestUpdate;

export const BonusPointType = {
  CLUB_ACTIVITY: 'CLUB_ACTIVITY', // Điểm cộng hoạt động CLB / Lab
  OTHER: 'OTHER',                 // Điểm cộng khác (sinh hoạt, khen thưởng,...)
} as const;
export type BonusPointType = Schema<'BonusPointType'>;

export const BONUS_POINT_TYPE_LABELS: Record<string, { label: string; color: string }> = {
  CLUB_ACTIVITY: {
    label: 'Hoạt động CLB',
    color: 'blue',
  },
  OTHER: {
    label: 'Điểm cộng khác',
    color: 'purple',
  },
};

export type BonusPointCreate = Schema<'BonusPointCreate'>;
export type BonusPointUpdate = Partial<BonusPointCreate>;

export type ViolationCreate = Schema<'ViolationCreate'>;
export type ViolationUpdate = Partial<ViolationCreate>;

export type BonusPointResponse = Schema<'app__bonus_point__application__dtos__BonusPointResponse'>;
export type PermissionRequestResponse = Schema<'PermissionRequestResponse'>;
export type PermissionRequestDetailResponse = Schema<'PermissionRequestDetailResponse'>;

export type DailySummaryResponse = Schema<'DailySummaryResponse'>;
