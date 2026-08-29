frontend/src/
├── assets/                 # Ảnh, fonts, tài nguyên tĩnh dùng chung toàn dự án
├── components/             # Global Components (Chỉ chứa UI components thực sự dùng chung)
│   ├── ui/                 # Các component cơ bản (Button, Modal, Input wrapper...)
│   ├── feedback/           # CapacityWarning, Toast, Loading skeleton...
│   ├── layout/             # MainLayout, Header, Sidebar (Tách biệt khỏi logic route)
│   └── PageWrapper.tsx
├── context/                # Global Contexts (AuthContext, ThemeContext...)
├── routes/                 # Quản lý cấu hình Router tập trung
│   ├── AppRoutes.tsx       # Định nghĩa các Route chính của ứng dụng
│   └── routeConfig.tsx     # Cấu hình danh sách route kèm permission
├── config/                 # Cấu hình hệ thống, menu items
├── lib/                    # Cấu hình các thư viện bên thứ 3 (queryClient, axiosInstance)
├── hooks/                  # Global Hooks (useDebounce, useToggle, useAuth...)
├── services/               # Global Services (gọi API chung, upload file...)
├── types/                  # Global Types (Common API responses, User base types...)
│
├── features/               # NƠI CHỨA CÁC MODULE TÍNH NĂNG CHÍNH
│   ├── billing/            # Module Billing
│   │   ├── components/     # Components đặc thù của Billing (BillingTable, InvoiceModal...)
│   │   ├── hooks/          # Hooks xử lý logic Billing (useBilling, useInvoices...)
│   │   ├── services/       # billing.service.ts (API calls riêng cho Billing)
│   │   ├── types/          # billing.types.ts
│   │   ├── pages/          # Các trang thuộc Billing (AdminBillingPage, InvoicesPage)
│   │   └── index.ts        # Public API: Export các components/pages ra ngoài
│   │
│   ├── homework/           # Module Homework
│   │   ├── components/     # HomeworkMobileList, DeadlineText...
│   │   ├── hooks/          # useHomeworks, useHomeworkActions
│   │   ├── services/       # homework.service.ts
│   │   ├── types/          # homework.types.ts
│   │   ├── pages/          # HomeworkPage.tsx
│   │   └── index.ts
│   │
│   ├── robot/              # Module Robot
│   │   ├── components/
│   │   ├── pages/          # RobotActivityPage, RobotCheckinPage...
│   │   ├── services/       # robot.service.ts (tách từ zalo hoặc api-key nếu cần)
│   │   └── index.ts
│   │
│   └── rbac/               # Module Quản lý quyền (Role/Permission)
│       ├── components/
│       ├── hooks/          # useRbac, usePermissionRequests
│       ├── services/       # rbac.service.ts, permission.service.ts
│       ├── pages/          # RoleManagementPage, PermissionManagementPage
│       └── index.ts
