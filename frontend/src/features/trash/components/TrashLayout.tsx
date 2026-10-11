import React from 'react';
import { Typography, Card, Tabs, Space, Grid } from 'antd';
import type { TabsProps } from 'antd';
import { DeleteOutlined, TrophyOutlined, WarningOutlined, FileTextOutlined } from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, type Variants } from 'motion/react';

const { Title, Text } = Typography;

const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.05
        }
    }
};

const itemVariants: Variants = {
    hidden: { opacity: 0, y: 10 },
    visible: {
        opacity: 1,
        y: 0,
        transition: { duration: 0.25, ease: "easeOut" }
    }
};

interface TrashLayoutProps {
    children: React.ReactNode;
}

export const TrashLayout: React.FC<TrashLayoutProps> = ({ children }) => {
    const navigate = useNavigate();
    const location = useLocation();
    const screens = Grid.useBreakpoint();

    const getActiveTabKey = () => {
        const path = location.pathname;
        if (path.includes('/trash/permission')) return 'permission-request';
        if (path.includes('/trash/violation')) return 'violation';
        return 'bonus-point';
    };

    const tabItems: TabsProps['items'] = [
        {
            key: 'bonus-point',
            label: (
                <span className="flex items-center gap-2">
                    <TrophyOutlined />
                    <span>Điểm cộng</span>
                </span>
            ),
        },
        {
            key: 'violation',
            label: (
                <span className="flex items-center gap-2">
                    <WarningOutlined />
                    <span>Vi phạm</span>
                </span>
            ),
        },
        {
            key: 'permission-request',
            label: (
                <span className="flex items-center gap-2">
                    <FileTextOutlined />
                    <span>Đơn phép</span>
                </span>
            ),
        },
    ];

    const handleTabChange = (key: string) => {
        navigate(`/dashboard/trash/${key}`);
    };

    return (
        <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="p-4 md:p-6 bg-[#f8fafc] min-h-full"
        >
            <motion.div variants={itemVariants} className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4 px-3 md:px-0">
                <Space size="middle">
                    <div className="hidden md:flex w-12 h-12 rounded-xl bg-gray-100 items-center justify-center text-gray-500 shadow-sm">
                        <DeleteOutlined className="text-2xl" />
                    </div>
                    <div>
                        <Title level={3} className="!m-0 text-xl md:text-2xl text-gray-800 mt-4 leading-relaxed">Thùng rác</Title>
                        <Text type="secondary" className="text-xs md:text-sm">Quản lý và khôi phục các dữ liệu đã xóa</Text>
                    </div>
                </Space>
            </motion.div>

            <motion.div variants={itemVariants}>
                <Card
                    className={!screens.md ? "bg-transparent shadow-none border-none p-0" : "shadow-sm border-gray-100 rounded-xl overflow-hidden"}
                    styles={{ body: { padding: !screens.md ? 0 : undefined } }}
                >
                    <div className="overflow-x-auto no-scrollbar">
                        <Tabs
                            activeKey={getActiveTabKey()}
                            items={tabItems}
                            onChange={handleTabChange}
                            className="trash-tabs"
                            tabBarStyle={{
                                paddingLeft: !screens.md ? '16px' : '24px',
                                paddingRight: !screens.md ? '16px' : '24px',
                                margin: 0,
                                minWidth: !screens.md ? 'max-content' : '100%',
                                borderBottom: '1px solid #f0f0f0'
                            }}
                        />
                    </div>
                    <div className="p-0 md:p-4">
                        {children}
                    </div>
                </Card>
            </motion.div>
        </motion.div>
    );
};

export default TrashLayout;
