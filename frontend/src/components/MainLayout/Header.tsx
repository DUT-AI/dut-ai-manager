import Logo from '@/assets/logo.jpg';
import { useAuth } from '@/context/AuthContext';
import {
    LogoutOutlined,
    UserOutlined
} from '@ant-design/icons';
import type { MenuProps } from 'antd';
import { Avatar, Dropdown, Layout, Space, Typography } from 'antd';
import { useNavigate } from 'react-router-dom';
const { Header } = Layout;
const { Title, Text } = Typography;

const HeaderLayout = () => {
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
                padding: '0 24px',
            }}
            className="flex items-center justify-between shadow-2xl border-b border-indigo-500/20 z-20 h-16 relative overflow-hidden"
        >
            {/* Subtle shine effect */}
            <div className="absolute top-0 left-0 w-full h-full pointer-events-none bg-[radial-gradient(circle_at_50%_0%,rgba(99,102,241,0.15),transparent_50%)]"></div>

            <div className="flex items-center gap-3 relative z-10">

                <img src={Logo} alt="Logo" className="w-auto h-10 bg-linear-to-br from-[#6366f1] via-[#818cf8] to-[#a855f7] rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/30 border border-white/20" />

                <div className="flex flex-col leading-tight">
                    <Title level={4} className="!m-0 font-bold tracking-tight drop-shadow-sm" style={{ color: '#ffffff' }}>
                        DUT AI Manager
                    </Title>
                    <Text className="text-[9px] uppercase font-bold tracking-[0.2em] opacity-90" style={{ color: '#ffffff' }}>Management System</Text>
                </div>
            </div>

            <Dropdown menu={{ items: menuItems }} placement="bottomRight" arrow>
                <Space className="cursor-pointer hover:bg-white/5 px-3 py-1.5 rounded-xl transition-all border border-transparent hover:border-white/10 group relative z-10">
                    <Avatar
                        className="bg-linear-to-br from-[#6366f1] to-[#a855f7] text-white shadow-md border-2 border-white/10 group-hover:border-white/30 transition-all"
                        size="large"
                        icon={<UserOutlined />}
                    />
                    <div className="hidden md:flex flex-col items-start leading-none ml-1">
                        <Text className="font-semibold text-sm group-hover:text-white transition-colors" style={{ color: '#ffffff' }}>{user?.name}</Text>
                        <div className="flex items-center gap-1.5 mt-0.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]"></span>
                            <Text className="text-[10px] uppercase font-bold tracking-wider opacity-80" style={{ color: '#ffffff' }}>{user?.role_name}</Text>
                        </div>
                    </div>
                </Space>
            </Dropdown>
        </Header>)
}

export default HeaderLayout