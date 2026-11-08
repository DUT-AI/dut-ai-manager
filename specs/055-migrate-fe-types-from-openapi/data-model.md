# Data Model & Type Mapping (Feature 055)

Tài liệu này xác định bảng ánh xạ từ Backend Pydantic Schemas sang Frontend `Schema<"T">`.

| Feature Module | Backend Pydantic Schema | Frontend Type Alias | Nguồn trích xuất |
| :--- | :--- | :--- | :--- |
| **Activity** | `BonusPointResponse` | `BonusPointResponse` | `Schema<'BonusPointResponse'>` |
| **Activity** | `PermissionRequestResponse` | `PermissionRequestResponse` | `Schema<'PermissionRequestResponse'>` |
| **Activity** | `PermissionRequestCreate` | `PermissionRequestCreate` | `Schema<'PermissionRequestCreate'>` |
| **Activity** | `BonusPointCreate` | `BonusPointCreate` | `Schema<'BonusPointCreate'>` |
| **Activity** | `ViolationCreate` | `ViolationCreate` | `Schema<'ViolationCreate'>` |
| **Report** | `DashboardOverviewResponse` | `DashboardOverviewResponse` | `Schema<'DashboardOverviewResponse'>` |
| **Report** | `ReportResponse` | `ReportResponse` | `Schema<'ReportResponse'>` |
| **Report** | `TitleReportItem` | `TitleReportItem` | `Schema<'TitleReportItem'>` |
| **Report** | `ParticipationStats` | `ParticipationStats` | `Schema<'ParticipationStats'>` |
| **Duty** | `DutyResponse` | `DutyResponse` | `Schema<'DutyResponse'>` |
| **Duty** | `WeeklyDutyClassDto` | `WeeklyDutyClassDto` | `Schema<'WeeklyDutyClassDto'>` |
| **Users** | `UserResponse` | `UserResponse` | `Schema<'UserResponse'>` |
| **Users** | `UserCreate` | `UserCreate` | `Schema<'UserCreate'>` |
| **Users** | `UserUpdate` | `UserUpdate` | `Schema<'UserUpdate'>` |
| **Meeting** | `MeetingResponse` | `MeetingResponse` | `Schema<'MeetingResponse'>` |
| **Meeting** | `ParticipantResponse` | `ParticipantResponse` | `Schema<'ParticipantResponse'>` |
| **Auth** | `TokenResponse` | `TokenResponse` | `Schema<'TokenResponse'>` |
| **Auth** | `LoginRequest` | `LoginRequest` | `Schema<'LoginRequest'>` |
