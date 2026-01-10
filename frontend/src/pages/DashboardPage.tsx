import HeaderLayout from '@/components/MainLayout/Header';
import {
    CalendarOutlined,
    DashboardOutlined,
    SafetyCertificateOutlined,
    SettingOutlined,
    TeamOutlined
} from '@ant-design/icons';
import type { MenuProps } from 'antd';
import { Layout, Menu, Spin, Tag, Typography } from 'antd';
import { Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import ActivityCalendarPage from './ActivityCalendarPage';
import HomePage from './HomePage';
import ProfilePage from './ProfilePage';
import RoleManagementPage from './RoleManagementPage';
import UserManagementPage from './UserManagementPage';
import ViolationManagementPage from './ViolationManagementPage';
import PermissionManagementPage from './PermissionManagementPage';
import TeamManagementPage from './TeamManagementPage';
import { HomeworkPage } from './HomeworkPage';
import { SettingsPage } from './SettingsPage';
import { WarningOutlined, FileTextOutlined, ApartmentOutlined, UserOutlined } from '@ant-design/icons';
const { Content, Sider } = Layout;
const { Text } = Typography;



const DashboardPage = () => {
    const { loading, hasPermission } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    // Determine active key from path
    const getActiveKey = () => {
        const path = location.pathname;
        if (path.includes('/rbac')) return 'rbac';
        if (path.includes('/users')) return 'users';
        if (path.includes('/activities')) return 'activities';
        if (path.includes('/permissions')) return 'permissions';
        if (path.includes('/violations')) return 'violations';
        if (path.includes('/teams')) return 'teams';
        if (path.includes('/profile')) return 'profile_detail';
        if (path.includes('/settings')) return 'settings';
        return 'profile';
    };

    const activeKey = getActiveKey();

    const sideMenuItems: MenuProps['items'] = [
        {
            key: 'profile',
            icon: <DashboardOutlined />,
            label: 'Tổng quan',
            onClick: () => navigate('/dashboard'),
        },
        {
            key: 'rbac',
            icon: <SafetyCertificateOutlined />,
            label: 'Quản lý Quyền',
            onClick: () => navigate('/dashboard/rbac'),
        },
        {
            key: 'users',
            icon: <UserOutlined />,
            label: 'Quản lý Thành viên',
            onClick: () => navigate('/dashboard/users'),
        },
        {
            key: 'teams',
            icon: <TeamOutlined />,
            label: 'Quản lý Nhóm (Teams)',
            onClick: () => navigate('/dashboard/teams'),
        },
        {
            key: 'activities',
            icon: <CalendarOutlined />,
            label: 'Lịch Hoạt động',
            onClick: () => navigate('/dashboard/activities'),
        },
        {
            key: 'permissions',
            icon: <FileTextOutlined />,
            label: 'Quản lý Đơn phép',
            onClick: () => navigate('/dashboard/permissions'),
        },
        {
            key: 'violations',
            icon: <WarningOutlined />,
            label: 'Quản lý Vi phạm',
            onClick: () => navigate('/dashboard/violations'),
        },
        {
            key: 'homework',
            icon: <WarningOutlined />,
            label: 'Bài tập về nhà',
            onClick: () => navigate('/dashboard/homeworks'),
        },
        {
            key: 'settings',
            icon: <SettingOutlined />,
            label: 'Cài đặt',
            onClick: () => navigate('/dashboard/settings'),
        },
    ];

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <Spin size="large" />
            </div>
        );
    }

    return (
        <Layout style={{ height: '100vh', overflow: 'hidden' }}>
            <HeaderLayout />

            <Layout style={{ overflow: 'hidden' }}>
                <Sider
                    width={260}
                    className="bg-white border-r border-gray-100 z-10"
                    theme="light"
                >
                    <div className="flex flex-col h-full">
                        <Menu
                            mode="inline"
                            selectedKeys={[activeKey]}
                            items={sideMenuItems}
                            className="border-none flex-grow mt-4 custom-sidebar-menu"
                        />
                        <div className="p-4 border-t border-gray-50">
                            <div className="bg-gray-50 p-3 rounded-xl border border-gray-100">
                                <Text className="text-[10px] text-gray-400 font-bold uppercase block mb-2 px-1">Trạng thái</Text>
                                <div className="flex items-center justify-between px-1">
                                    <Tag color="success" className="m-0 rounded-full px-3 text-[10px] font-bold">ONLINE</Tag>
                                    <span className="flex h-2 w-2 relative">
                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                        <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </Sider>
                <Content className="p-0 bg-[#f8fafc] overflow-y-auto custom-scrollbar">
                    <div className="min-h-full relative">
                        <Routes>
                            <Route index element={<HomePage />} />
                            <Route path="rbac" element={<RoleManagementPage />} />
                            <Route path="users" element={<UserManagementPage />} />
                            <Route path="activities" element={<ActivityCalendarPage />} />
                            <Route path="permissions" element={<PermissionManagementPage />} />
                            <Route path="violations" element={<ViolationManagementPage />} />
                            <Route path="teams" element={<TeamManagementPage />} />
                            <Route path="homeworks" element={<HomeworkPage />} />
                            <Route path="settings" element={<SettingsPage />} />
                            <Route path="profile/:userId" element={<ProfilePage />} />
                            <Route path="*" element={<Navigate to="/dashboard" replace />} />
                        </Routes>
                    </div>
                </Content>
            </Layout>
            <style>{`
                .custom-sidebar-menu .ant-menu-item {
                    height: 50px !important;
                    margin: 4px 12px !important;
                    width: calc(100% - 24px) !important;
                    border-radius: 12px !important;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
                }
                .custom-sidebar-menu .ant-menu-item-selected {
                    background: rgba(99, 102, 241, 0.08) !important;
                    color: #4f46e5 !important;
                    font-weight: 600 !important;
                }
                .custom-sidebar-menu .ant-menu-item-selected .ant-menu-item-icon {
                    color: #4f46e5 !important;
                }
                .custom-scrollbar::-webkit-scrollbar {
                    width: 6px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: transparent;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: #e2e8f0;
                    border-radius: 10px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: #cbd5e1;
                }
            `}</style>
        </Layout>
    );
};

export default DashboardPage;
