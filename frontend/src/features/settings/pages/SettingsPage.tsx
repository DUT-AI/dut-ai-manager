import React, { useState } from 'react';
import { Layout, Menu, Typography, Button, Grid } from 'antd';
import { LockOutlined, SettingOutlined } from '@ant-design/icons';
import { motion, type Variants } from 'motion/react';
import { PasswordContent, GeneralContent } from '../components';

const { Content, Sider } = Layout;
const { Title, Text } = Typography;

const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.1
        }
    }
};

const menuItems = [
    {
        key: 'general',
        icon: <SettingOutlined />,
        label: 'Tài khoản',
    },
    {
        key: 'password',
        icon: <LockOutlined />,
        label: 'Bảo mật',
    },
];

export const SettingsPage: React.FC = () => {
    const screens = Grid.useBreakpoint();
    const [activeKey, setActiveKey] = useState('general');

    return (
        <div className={screens.md ? 'absolute inset-0 bg-[#f8fafc]' : 'bg-[#f8fafc] min-h-screen pb-10'}>
            <Layout className="bg-transparent h-full flex flex-col md:flex-row">
                {screens.md ? (
                    <Sider
                        width={260}
                        theme="light"
                        className="bg-white border-r border-gray-200 h-full overflow-y-auto shrink-0"
                    >
                        <div className="p-6 border-b border-gray-100">
                            <Title level={4} className="mb-1!">Cài đặt</Title>
                            <Text type="secondary" className="text-xs">Quản lý tài khoản của bạn</Text>
                        </div>
                        <Menu
                            mode="inline"
                            selectedKeys={[activeKey]}
                            onClick={(e) => setActiveKey(e.key)}
                            className="border-none mt-2 px-2"
                            items={menuItems.map(item => ({
                                ...item,
                                className: 'rounded-lg mb-1'
                            }))}
                        />
                    </Sider>
                ) : (
                    <div className="bg-white border-b border-gray-200 sticky top-0 z-10 p-4">
                        <div className="mb-4">
                            <Title level={4} className="mb-0!">Cài đặt</Title>
                            <Text type="secondary" className="text-xs">Quản lý tài khoản cá nhân</Text>
                        </div>
                        <div className="flex gap-2 overflow-x-auto pb-1 no-scrollbar">
                            {menuItems.map(item => (
                                <Button
                                    key={item.key}
                                    type={activeKey === item.key ? 'primary' : 'default'}
                                    icon={item.icon}
                                    onClick={() => setActiveKey(item.key)}
                                    className={`rounded-full shadow-none ${activeKey === item.key ? 'bg-indigo-600' : ''}`}
                                >
                                    {item.label}
                                </Button>
                            ))}
                        </div>
                    </div>
                )}
                <Content className="p-4 md:p-8 overflow-y-auto bg-gray-50 flex justify-center items-start">
                    <motion.div
                        variants={containerVariants}
                        initial="hidden"
                        animate="visible"
                        key={activeKey}
                        className="w-full flex justify-center"
                    >
                        {activeKey === 'password' ? <PasswordContent /> : <GeneralContent />}
                    </motion.div>
                </Content>
            </Layout>
        </div>
    );
};

export default SettingsPage;
