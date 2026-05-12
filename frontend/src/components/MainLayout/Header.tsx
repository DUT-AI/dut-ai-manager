import Logo from '@/assets/logo.jpg';
import { useAuth } from '@/context/AuthContext';
import {
    LogoutOutlined,
    UserOutlined,
    MenuOutlined,
    RobotOutlined
} from '@ant-design/icons';
import type { MenuProps } from 'antd';
import { Avatar, Dropdown, Layout, Space, Typography, Button, Tooltip } from 'antd';
import { useNavigate } from 'react-router-dom';
const { Header } = Layout;
const { Title, Text } = Typography;

interface HeaderLayoutProps {
    showMenuButton?: boolean;
    onMenuClick?: () => void;
}

const HeaderLayout = ({ showMenuButton, onMenuClick }: HeaderLayoutProps) => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = async () => {
        await logout();
    };


    const menuItems: MenuProps['items'] = [
        {
            key: 'view_profile',
            label: 'Xem hồ sơ',
            icon: <UserOutlined />,
            onClick: () => navigate(`/dashboard/profile/${user?.id}`),
        },
        {
            key: 'logout',
            label: 'Đăng xuất',
            icon: <LogoutOutlined />,
            onClick: handleLogout,
        },
    ];

    return (
        <Header
            style={{
                background: 'linear-gradient(90deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%)',
            }}
            className="flex items-center justify-between shadow-2xl border-b border-indigo-500/20 z-20 h-16 relative overflow-hidden !px-4 md:!px-8"
        >
            {/* Subtle shine effect */}
            <div className="absolute top-0 left-0 w-full h-full pointer-events-none bg-[radial-gradient(circle_at_50%_0%,rgba(99,102,241,0.15),transparent_50%)]"></div>

            <div className="flex items-center gap-2 md:gap-3 relative z-10">
                {showMenuButton && (
                    <Button
                        type="text"
                        icon={<MenuOutlined style={{ color: '#fff', fontSize: '20px' }} />}
                        onClick={onMenuClick}
                        className="mr-1 !p-0 flex items-center justify-center w-8 h-8 md:w-10 md:h-10 hover:bg-white/10"
                    />
                )}
                <img src={Logo} alt="Logo" className="hidden md:block w-8 h-8 md:w-auto md:h-10 bg-linear-to-br from-[#6366f1] via-[#818cf8] to-[#a855f7] rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/30 border border-white/20" />

                <div className="flex flex-col leading-tight">
                    <Title level={4} className="!m-0 font-bold tracking-tight drop-shadow-sm text-base md:text-xl" style={{ color: '#ffffff', fontSize: 'inherit' }}>
                        DUT AI MANAGER
                    </Title>
                    <Text className="hidden md:block text-[9px] uppercase font-bold tracking-[0.2em] opacity-90" style={{ color: '#ffffff' }}>Management System</Text>
                </div>
            </div>

            <div className="flex items-center gap-4 relative z-10">
                <Tooltip title="Robot Interface">
                    <Button
                        type="text"
                        icon={<RobotOutlined style={{ color: '#4fdbc8', fontSize: '24px' }} />}
                        onClick={() => navigate('/dashboard/robot')}
                        className="hover:bg-white/10 flex items-center justify-center w-10 h-10 rounded-full border border-[#4fdbc8]/30 shadow-[0_0_10px_rgba(79,219,200,0.2)]"
                    />
                </Tooltip>

                <Dropdown menu={{ items: menuItems }} placement="bottomRight" arrow>
                <Space className="cursor-pointer hover:bg-white/5 px-2 py-1 md:px-3 md:py-1.5 rounded-xl transition-all border border-transparent hover:border-white/10 group relative z-10">
                    <Avatar
                        className="bg-linear-to-br from-[#6366f1] to-[#a855f7] text-white shadow-md border-2 border-white/10 group-hover:border-white/30 transition-all font-bold"
                        size={{ xs: 32, sm: 32, md: 40, lg: 40, xl: 40, xxl: 40 }}
                        src={user?.avatar_url}
                    >
                        {user?.name ? user.name.charAt(0).toUpperCase() : <UserOutlined />}
                    </Avatar>
                    <div className="hidden md:flex flex-col items-start leading-none ml-1">
                        <Text className="font-semibold text-sm group-hover:text-white transition-colors" style={{ color: '#ffffff' }}>{user?.name}</Text>
                        <div className="flex items-center gap-1.5 mt-0.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]"></span>
                            <Text className="text-[10px] uppercase font-bold tracking-wider opacity-80" style={{ color: '#ffffff' }}>{user?.role_name}</Text>
                        </div>
                    </div>
                </Space>
            </Dropdown>
            </div>
        </Header>)
}

export default HeaderLayout