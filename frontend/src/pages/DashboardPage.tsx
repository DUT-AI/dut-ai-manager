import { useState } from 'react';
import { Layout, Menu, Spin, Tag, Typography, Drawer, Grid } from 'antd';
import type { MenuProps } from 'antd';
import { Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/features/auth/context/AuthContext';
import HeaderLayout from '@/components/MainLayout/Header';

// Import cấu hình mới tạo
import { sidebarMenuConfig } from '@/config/menu';
import { dashboardRoutesConfig } from '@/routes/dashboardRoutes';

const { Content, Sider } = Layout;
const { Text } = Typography;
const { useBreakpoint } = Grid;



interface SidebarContentProps {
    activeKey: string;
    sideMenuItems: MenuProps['items'];
}

const SidebarContent = ({ activeKey, sideMenuItems }: SidebarContentProps) => (
    <div className="flex flex-col h-full overflow-hidden">
        <div className="flex items-center justify-center py-4 shrink-0">
            {/* Logo area if needed */}
        </div>
        <div className="flex-1 overflow-y-auto custom-scrollbar">
            <Menu
                mode="inline"
                selectedKeys={[activeKey]}
                items={sideMenuItems}
                className="border-none mt-4 custom-sidebar-menu"
            />
        </div>
        <div className="p-4 border-t border-gray-50 shrink-0">
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
);

const DashboardPage = () => {
    const { loading, hasPermission } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const screens = useBreakpoint();
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    // Determines if we are on a mobile screen
    const isMobile = !screens.md;

    // Determine active key from path
    const getActiveKey = () => {
        const path = location.pathname;
        if (path.includes('/meetings')) return 'meetings';
        if (path.includes('/rbac')) return 'rbac';
        if (path.includes('/users')) return 'users';
        if (path.includes('/activities')) return 'activities';
        if (path.includes('/permissions')) return 'permissions';
        if (path.includes('/violations')) return 'violations';
        if (path.includes('/teams')) return 'teams';
        if (path.includes('/profile')) return 'profile_detail';
        if (path.includes('/settings')) return 'settings';
        if (path.includes('/trash')) return 'trash';
        if (path.includes('/academic-reports')) return 'academic_reports';
        if (path.includes('/activity-reports')) return 'activity_reports';
        if (path.includes('/admin-billing')) return 'admin_billing';
        if (path.includes('/invoices')) return 'invoices';
        if (path.includes('/expenses')) return 'expenses';
        return 'profile';
    };

    const activeKey = getActiveKey();

    const handleMenuClick = (path: string) => {
        navigate(path);
        if (isMobile) {
            setMobileMenuOpen(false);
        }
    };

    // Map cấu hình tĩnh thành định dạng menu của Antd dựa trên quyền hạn (hasPermission)
    const sideMenuItems: MenuProps['items'] = sidebarMenuConfig
        .filter(item => !item.permission || hasPermission(item.permission))
        .map(item => ({
            key: item.key,
            icon: item.icon,
            label: item.label,
            onClick: () => handleMenuClick(item.path),
        }));

    const isRobotPage = location.pathname.startsWith('/dashboard/robot');

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <Spin size="large" />
            </div>
        );
    }

    if (isRobotPage) {
        const robotRoute = dashboardRoutesConfig.find(r => r.path === 'robot/*');
        return (
            <div className="h-screen w-screen overflow-hidden">
                <Routes>
                    <Route path="robot/*" element={robotRoute?.element ?? null} />
                </Routes>
            </div>
        );
    }

    return (
        <Layout style={{ height: '100vh', overflow: 'hidden' }}>
            <HeaderLayout
                showMenuButton={isMobile}
                onMenuClick={() => setMobileMenuOpen(true)}
            />

            <Layout style={{ overflow: 'hidden' }}>
                {!isMobile && (
                    <Sider
                        width={260}
                        className="bg-white border-r border-gray-100 z-10"
                        theme="light"
                    >
                        <SidebarContent activeKey={activeKey} sideMenuItems={sideMenuItems} />
                    </Sider>
                )}

                <Drawer
                    placement="left"
                    onClose={() => setMobileMenuOpen(false)}
                    open={mobileMenuOpen}
                    width={280}
                    styles={{ body: { padding: 0 } }}
                    closable={false}
                >
                    <SidebarContent activeKey={activeKey} sideMenuItems={sideMenuItems} />
                </Drawer>

                <Content className="p-0 bg-[#f8fafc] overflow-auto custom-scrollbar">
                    <div className="min-h-full relative">
                        <Routes>
                            {dashboardRoutesConfig.map((route, idx) => {
                                // Kiểm tra quyền truy cập route
                                if (route.permission && !hasPermission(route.permission)) {
                                    return <Route key={idx} path={route.path} element={<Navigate to="/dashboard" replace />} />;
                                }

                                return (
                                    <Route
                                        key={idx}
                                        index={route.index}
                                        path={route.index ? undefined : route.path}
                                        element={route.element}
                                    />
                                );
                            })}
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
