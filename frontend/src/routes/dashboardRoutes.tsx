/* File này sẽ import tất cả các trang con và định nghĩa
mảng cấu hình route (kèm thông tin path, component tương ứng 
và phân quyền).*/

import React from 'react';
import HomePage from '@/pages/HomePage';
import AcademicReportPage from '@/pages/AcademicReportPage';
import ActivityReportPage from '@/pages/ActivityReportPage';
import RobotInterfacePage from '@/features/robot/pages/RobotInterfacePage';
import RoleManagementPage from '@/features/rbac/pages/RoleManagementPage';
import UserManagementPage from '@/pages/UserManagementPage';
import ActivityCalendarPage from '@/pages/ActivityCalendarPage';
import PermissionManagementPage from '@/features/rbac/pages/PermissionManagementPage';
import ViolationManagementPage from '@/features/violations/pages/ViolationManagementPage';
import TeamManagementPage from '@/pages/TeamManagementPage';
import { HomeworkPage } from '@/features/homework';
import MeetingCalendarPage from '@/pages/MeetingCalendarPage';
import InvoicesPage from '@/features/billing/pages/InvoicesPage';
import AdminBillingPage from '@/features/billing/pages/AdminBillingPage';
import { SettingsPage } from '@/pages/SettingsPage';
import { TrashPage } from '@/pages/TrashPage';
import ProfilePage from '@/pages/ProfilePage';

export interface RouteConfig {
    path: string;
    element: React.ReactNode;
    index?: boolean;       // Có phải route mặc định không
    permission?: string;   // Quyền yêu cầu để truy cập (nếu có)
}

export const dashboardRoutesConfig: RouteConfig[] = [
    {
        path: '',
        element: <HomePage />,
        index: true,
    },
    {
        path: 'academic-reports',
        element: <AcademicReportPage />,
    },
    {
        path: 'activity-reports',
        element: <ActivityReportPage />,
    },
    {
        path: 'robot/*',
        element: <RobotInterfacePage />,
    },
    {
        path: 'rbac',
        element: <RoleManagementPage />,
    },
    {
        path: 'users',
        element: <UserManagementPage />,
    },
    {
        path: 'activities',
        element: <ActivityCalendarPage />,
    },
    {
        path: 'permissions',
        element: <PermissionManagementPage />,
    },
    {
        path: 'violations',
        element: <ViolationManagementPage />,
    },
    {
        path: 'teams',
        element: <TeamManagementPage />,
    },
    {
        path: 'homeworks',
        element: <HomeworkPage />,
    },
    {
        path: 'meetings',
        element: <MeetingCalendarPage />,
    },
    {
        path: 'invoices',
        element: <InvoicesPage />,
    },
    {
        path: 'admin-billing',
        element: <AdminBillingPage />,
        permission: 'billing:read',
    },
    {
        path: 'settings',
        element: <SettingsPage />,
    },
    {
        path: 'trash',
        element: <TrashPage />,
    },
    {
        path: 'profile/:userId',
        element: <ProfilePage />,
    },
];