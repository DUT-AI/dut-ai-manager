import React from 'react';
import type { MenuProps } from 'antd';

/*
File này sẽ tập hợp tất cả các icon từ @ant-design/icons và định nghĩa 
mảng menu hiển thị.
*/

import {
    WarningOutlined,
    FileTextOutlined,
    UserOutlined,
    DeleteOutlined,
    TrophyOutlined,
    DashboardOutlined,
    SafetyCertificateOutlined,
    TeamOutlined,
    CalendarOutlined,
    BookOutlined,
    SettingOutlined,
    VideoCameraOutlined,
    CreditCardOutlined,
    AuditOutlined,
} from '@ant-design/icons';

// Định nghĩa kiểu dữ liệu cho một item trong menu để hỗ trợ phân quyền sau này
export interface MenuItemConfig {
    key: string;
    icon: React.ReactNode;
    label: string;
    path: string;
    permission?: string; // Tên quyền cần có để xem menu này (nếu có)
}

export const sidebarMenuConfig: MenuItemConfig[] = [
    {
        key: 'profile',
        icon: <DashboardOutlined />,
        label: 'Tổng quan',
        path: '/dashboard',
    },
    {
        key: 'academic_reports',
        icon: <TrophyOutlined />,
        label: 'Báo cáo Học tập',
        path: '/dashboard/academic-reports',
    },
    {
        key: 'activity_reports',
        icon: <AuditOutlined />,
        label: 'Báo cáo Hoạt động',
        path: '/dashboard/activity-reports',
    },
    {
        key: 'rbac',
        icon: <SafetyCertificateOutlined />,
        label: 'Quản lý Quyền',
        path: '/dashboard/rbac',
    },
    {
        key: 'users',
        icon: <UserOutlined />,
        label: 'Quản lý Thành viên',
        path: '/dashboard/users',
    },
    {
        key: 'teams',
        icon: <TeamOutlined />,
        label: 'Quản lý Nhóm (Teams)',
        path: '/dashboard/teams',
    },
    {
        key: 'activities',
        icon: <CalendarOutlined />,
        label: 'Lịch Hoạt động',
        path: '/dashboard/activities',
    },
    {
        key: 'meetings',
        icon: <VideoCameraOutlined />,
        label: 'Lịch Meeting',
        path: '/dashboard/meetings',
    },
    {
        key: 'permissions',
        icon: <FileTextOutlined />,
        label: 'Quản lý Đơn phép',
        path: '/dashboard/permissions',
    },
    {
        key: 'violations',
        icon: <WarningOutlined />,
        label: 'Quản lý Vi phạm',
        path: '/dashboard/violations',
    },
    {
        key: 'homework',
        icon: <BookOutlined />,
        label: 'Bài tập về nhà',
        path: '/dashboard/homeworks',
    },
    {
        key: 'invoices',
        icon: <CreditCardOutlined />,
        label: 'Hóa đơn của tôi',
        path: '/dashboard/invoices',
    },
    {
        key: 'admin_billing',
        icon: <AuditOutlined />,
        label: 'Quản lý Hóa đơn',
        path: '/dashboard/admin-billing',
        permission: 'billing:read', // Quyền cần có để xem mục này
    },
    {
        key: 'settings',
        icon: <SettingOutlined />,
        label: 'Cài đặt',
        path: '/dashboard/settings',
    },
    {
        key: 'trash',
        icon: <DeleteOutlined />,
        label: 'Thùng rác',
        path: '/dashboard/trash',
    },
];