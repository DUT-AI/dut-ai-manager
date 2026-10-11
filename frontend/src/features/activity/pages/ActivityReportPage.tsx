import { useState } from 'react';
import {
    Tabs,
    Typography,
    Space,
    Grid,
} from 'antd';
import {
    BarChartOutlined,
    CalendarOutlined,
    CrownOutlined,
    LineChartOutlined,
} from '@ant-design/icons';
import { motion, type Variants } from 'motion/react';
import { Agentation } from 'agentation';

import ActivityParticipationPage from './ActivityParticipationPage';
import ActivityTitlesPage from './ActivityTitlesPage';
import ActivityTrendPage from './ActivityTrendPage';

const { Title, Text } = Typography;
const { useBreakpoint } = Grid;

const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.1,
        },
    },
};

const itemVariants: Variants = {
    hidden: { opacity: 0, y: 15 },
    visible: {
        opacity: 1,
        y: 0,
        transition: { duration: 0.35, ease: 'easeOut' },
    },
};

const ActivityReportPage = () => {
    const screens = useBreakpoint();
    const [activeTab, setActiveTab] = useState<'participation' | 'title' | 'trend'>('participation');

    return (
        <>
            <motion.div
                variants={containerVariants}
                initial="hidden"
                animate="visible"
                className="w-full p-4 md:p-6"
            >
                {/* Header Page */}
                <motion.div
                    variants={itemVariants}
                    className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-4"
                >
                    <Space size="middle">
                        <div className="hidden md:flex w-12 h-12 rounded-xl bg-orange-50 items-center justify-center text-orange-600 shadow-sm">
                            <BarChartOutlined className="text-2xl" />
                        </div>
                        <div>
                            <Title level={3} className="text-xl md:text-2xl m-0 text-orange-600">
                                Báo cáo Hoạt động
                            </Title>
                            <Text type="secondary" className="text-xs md:text-sm">
                                Xem thống kê tham gia sinh hoạt, bảng xếp hạng danh hiệu và xu hướng hoạt động
                            </Text>
                        </div>
                    </Space>
                </motion.div>

                {/* Tabs full-width with destroyInactiveTabPane */}
                <motion.div variants={itemVariants} className="w-full">
                    <Tabs
                        activeKey={activeTab}
                        onChange={(key) => setActiveTab(key as any)}
                        destroyInactiveTabPane={true}
                        size="large"
                        className="custom-report-tabs w-full"
                        tabBarStyle={{
                            padding: !screens.md ? '0 8px' : '0 16px',
                            margin: '0 0 16px 0',
                            borderBottom: '1px solid #f1f5f9',
                        }}
                        items={[
                            {
                                key: 'participation',
                                label: (
                                    <Space>
                                        <CalendarOutlined />
                                        <span>Chi tiết</span>
                                    </Space>
                                ),
                                children: <ActivityParticipationPage />,
                            },
                            {
                                key: 'title',
                                label: (
                                    <Space>
                                        <CrownOutlined />
                                        <span>Danh hiệu</span>
                                    </Space>
                                ),
                                children: <ActivityTitlesPage />,
                            },
                            {
                                key: 'trend',
                                label: (
                                    <Space>
                                        <LineChartOutlined />
                                        <span>Xu hướng hoạt động</span>
                                    </Space>
                                ),
                                children: <ActivityTrendPage />,
                            },
                        ]}
                    />
                </motion.div>
            </motion.div>

            <style>{`
                .custom-report-tabs .ant-tabs-nav::before {
                    display: none;
                }
                .custom-report-tabs .ant-tabs-tab {
                    padding: 14px 0 !important;
                    margin-right: 32px !important;
                    transition: all 0.3s ease;
                }
                .custom-report-tabs .ant-tabs-tab-active .ant-tabs-tab-btn {
                    color: #f97316 !important;
                    font-weight: 600;
                }
                .custom-report-tabs .ant-tabs-ink-bar {
                    background: #f97316 !important;
                    height: 3px !important;
                    border-radius: 3px 3px 0 0;
                }
                .ant-table-thead > tr > th {
                    background: #fcfcfd !important;
                    color: #64748b !important;
                    font-size: 12px !important;
                    text-transform: uppercase !important;
                    letter-spacing: 0.025em !important;
                    font-weight: 700 !important;
                    border-bottom: 1px solid #f1f5f9 !important;
                }
                .ant-table-tbody > tr > td {
                    border-bottom: 1px solid #f8fafc !important;
                    padding: 16px !important;
                }
                .ant-table-tbody > tr:hover > td {
                    background: #fffaf5 !important;
                }
            `}</style>
            <Agentation />
        </>
    );
};

export default ActivityReportPage;
