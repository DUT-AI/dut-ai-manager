# Data Model: Đồng Bộ Lịch Meeting & Quản Lý Đơn Phép Trên Zalo Mini App

**Feature**: `020-zalo-mini-app-meeting-and-permissions`  
**Date**: 2026-10-21  

---

## 1. Entities & Types (Frontend Zalo Mini App)

### 1.1 Meeting Detail & Participant Types

```typescript
// zmp-app/src/types/meeting.types.ts

export const ParticipantStatus = {
  REGISTERED: 'REGISTERED',
  JOINED: 'JOINED',
  ABSENT: 'ABSENT',
  LATE: 'LATE',
  CANCELLED: 'CANCELLED',
  COMPLETED: 'COMPLETED',
} as const;

export type ParticipantStatus = (typeof ParticipantStatus)[keyof typeof ParticipantStatus];

export interface ParticipantResponse {
  id: number;
  meeting_id: number;
  user_id: number;
  role: 'host' | 'trainer' | 'trainee' | 'member';
  status: ParticipantStatus;
  check_in_time?: string | null;
  check_in_image_url?: string | null;
  note?: string | null;
  user?: {
    id: number;
    name: string;
    email: string;
    avatar_url?: string | null;
  };
}

export interface MeetingResponse {
  id: number;
  title: string;
  description?: string | null;
  start_time: string;
  end_time: string;
  location?: string | null;
  meeting_url?: string | null;
  max_participants?: number | null;
  require_check_in: boolean;
  enable_evaluation: boolean;
  created_by?: number | null;
  participants: ParticipantResponse[];
}

export interface UpdateParticipantStatusPayload {
  status: ParticipantStatus;
  note?: string;
}
```

### 1.2 Evaluation Types

```typescript
export interface TraineeSubmitEvaluationPayload {
  trainee_id: number;
  criteria: Array<{
    criteria_id?: number;
    criteria_name: string;
    score: number;
    max_score?: number;
    comment?: string;
  }>;
  general_comment?: string;
}

export interface MeetingOverallEvaluationPayload {
  summary: string;
  achievements?: string;
  issues?: string;
  next_steps?: string;
}
```

### 1.3 Permission Request Types

```typescript
// zmp-app/src/types/permission.types.ts

export const RequestCategory = {
  ABSENCE: 'ABSENCE',
  POSTPONE: 'POSTPONE',
  LATE: 'LATE',
  OTHER: 'OTHER',
  CHANGE_MEETING: 'CHANGE_MEETING',
} as const;

export type RequestCategory = (typeof RequestCategory)[keyof typeof RequestCategory];

export interface PermissionRequestResponse {
  id: number;
  category: RequestCategory;
  note: string;
  start_time?: string | null;
  homework_id?: number | null;
  meeting_id?: number | null;
  old_meeting_id?: number | null;
  created_by?: number | null;
  created_at: string;
  updated_at: string;
  owner?: {
    id: number;
    name: string;
    avatar_url?: string | null;
  };
  meeting?: {
    id: number;
    title: string;
    start_time: string;
  } | null;
  old_meeting?: {
    id: number;
    title: string;
    start_time: string;
  } | null;
}
```

---

## 2. State & Component Mapping

| Entity | UI Component (ZaUI) | Trạng thái State / Cache Key |
| :--- | :--- | :--- |
| **Meeting Detail** | `MeetingDetailPage.tsx` | React Query: `['meeting', id]` |
| **Meeting Hero** | `MeetingHeroCard.tsx` | Dữ liệu `meeting` |
| **Meeting Stats** | `MeetingStatsCard.tsx` | Tính toán từ `meeting.participants` |
| **Participants List** | `MeetingParticipantsList.tsx` | Filter theo trạng thái (`ALL`, `JOINED`, `ABSENT`, `LATE`) |
| **Evaluation Tab** | `MeetingEvaluationTab.tsx` | React Query: `['meeting-evaluations', id]` |
| **Permission List** | `PermissionList.tsx` | React Query: `['permissions', { filter, category }]` |
| **Permission Filter** | `PermissionFilterBar.tsx` | Local State: `category`, `onlyMine` |
