/* File này sẽ import tất cả các trang con và định nghĩa
mảng cấu hình route (kèm thông tin path, component tương ứng 
và phân quyền).*/

import React from 'react';
import HomePage from '@/pages/HomePage';
import { SettingsPage } from '@/features/settings';
import { TrashPage } from '@/features/trash';

import { AcademicReportPage } from '@/features/academic-report';
import { ActivityCalendarPage, ActivityReportPage } from '@/features/activity';
import { AdminBillingPage, InvoicesPage } from '@/features/billing';
import { HomeworkPage } from '@/features/homework';
import { MeetingCalendarPage } from '@/features/meeting';
import { PermissionManagementPage, RoleManagementPage } from '@/features/rbac';
import { RobotInterfacePage } from '@/features/robot';
import { TeamManagementPage } from '@/features/teams';
import { ProfilePage, UserManagementPage } from '@/features/users';
import { ViolationManagementPage } from '@/features/violations';

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