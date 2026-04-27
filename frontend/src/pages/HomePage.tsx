import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { reportService } from "../services/api/report.service";
import { Card, Col, DatePicker, Empty, List, Row, Spin, Tag, Typography, Space } from "antd";
import dayjs from "dayjs";
import {
    ClockCircleOutlined,
    ExclamationCircleOutlined,
    StarOutlined,
    FileTextOutlined,
    TeamOutlined
} from "@ant-design/icons";
import { useQuery } from "@tanstack/react-query";
import { motion, type Variants } from "motion/react";

const { Title, Text } = Typography;

const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.1,
            delayChildren: 0.2
        }
    }
};

const itemVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
        opacity: 1,
        y: 0,
        transition: {
            duration: 0.5,
            ease: "easeOut"
        }
    }
};

const listVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.05
        }
    }
};

const listItemVariants: Variants = {
    hidden: { opacity: 0, x: -10 },
    visible: { opacity: 1, x: 0 }
};

const HomePage = () => {
    const { user } = useAuth();
    const [date, setDate] = useState(() => dayjs());

    const { data, isLoading } = useQuery({
        queryKey: ['dashboard-overview', date.month(), date.year()],
        queryFn: () => reportService.getDashboardOverview(date.month() + 1, date.year()),
    });

    const stats = [
        {
            title: "Điểm cộng",
            value: data?.bonus_points.length || 0,
            icon: <StarOutlined className="text-yellow-500 text-2xl" />,
            color: "bg-yellow-50",
        },
        {
            title: "Vi phạm",
            value: data?.violations.length || 0,
            icon: <ExclamationCircleOutlined className="text-red-500 text-2xl" />,
            color: "bg-red-50",
        },
        {
            title: "Đơn phép",
            value: data?.permission_requests.length || 0,
            icon: <FileTextOutlined className="text-blue-500 text-2xl" />,
            color: "bg-blue-50",
        },
        {
            title: "Bài tập chưa nộp",
            value: data?.unsubmitted_homeworks.length || 0,
            icon: <ClockCircleOutlined className="text-orange-500 text-2xl" />,
            color: "bg-orange-50",
        },
    ];

    return (
        <motion.div 
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="max-w-7xl mx-auto py-6 px-4 md:px-6 md:py-8"
        >
            <motion.div variants={itemVariants} className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 md:mb-8 gap-4">
                <div>
                    <Title level={3} className="!mb-1">
                        Xin chào, <span className="text-indigo-600">{user?.name}</span> 👋
                    </Title>
                    <Text type="secondary">Tổng quan hoạt động của bạn trong tháng này</Text>
                </div>
                <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                    <DatePicker 
                        picker="month" 
                        value={date} 
                        onChange={(d) => d && setDate(d)}
                        format="MM/YYYY"
                        allowClear={false}
                        className="shadow-sm border-gray-100 rounded-lg h-10 px-4"
                    />
                </motion.div>
            </motion.div>

            <Row gutter={[20, 20]} className="mb-10">
                {stats.map((stat, index) => (
                    <Col xs={24} sm={12} lg={6} key={index}>
                        <motion.div
                            variants={itemVariants}
                            whileHover={{ y: -5, transition: { duration: 0.2 } }}
                        >
                            <Card bordered={false} className={`${stat.color} shadow-xs rounded-xl overflow-hidden`}>
                                <div className="flex items-center justify-between">
                                    <div>
                                        <Text type="secondary" className="text-xs uppercase font-bold tracking-wider">{stat.title}</Text>
                                        <div className="mt-1">
                                            <Title level={2} className="!m-0 !text-gray-800">{stat.value}</Title>
                                        </div>
                                    </div>
                                    <div className="p-3 bg-white/60 rounded-xl shadow-xs">
                                        {stat.icon}
                                    </div>
                                </div>
                            </Card>
                        </motion.div>
                    </Col>
                ))}
            </Row>

            <Row gutter={[24, 24]}>
                <Col xs={24} lg={16}>
                    <motion.div variants={itemVariants}>
                        <Card 
                            title={
                                <Space>
                                    <ClockCircleOutlined className="text-indigo-500" />
                                    <span>Bài tập chưa nộp</span>
                                </Space>
                            }
                            bordered={false} 
                            className="shadow-sm border-gray-100 rounded-xl overflow-hidden h-full"
                        >
                            {isLoading ? (
                                <div className="py-12 flex justify-center"><Spin /></div>
                            ) : data?.unsubmitted_homeworks.length === 0 ? (
                                <Empty description="Chúc mừng! Bạn đã hoàn thành tất cả bài tập." className="py-10" />
                            ) : (
                                <motion.div variants={listVariants}>
                                    <List
                                        dataSource={data?.unsubmitted_homeworks}
                                        renderItem={(hw) => (
                                            <motion.div variants={listItemVariants}>
                                                <List.Item className="px-0 py-4 hover:bg-gray-50/50 transition-colors rounded-lg">
                                                    <div className="w-full flex justify-between items-center px-2">
                                                        <Space direction="vertical" size={0}>
                                                            <Text strong className="text-gray-800">{hw.title}</Text>
                                                            <Text type="secondary" className="text-xs">Hết hạn: {dayjs(hw.deadline).format('DD/MM/YYYY HH:mm')}</Text>
                                                        </Space>
                                                        <Tag color="error" className="rounded-full px-3">Chưa nộp</Tag>
                                                    </div>
                                                </List.Item>
                                            </motion.div>
                                        )}
                                    />
                                </motion.div>
                            )}
                        </Card>
                    </motion.div>
                </Col>

                <Col xs={24} lg={8}>
                    <motion.div variants={itemVariants}>
                        <Card 
                            title={
                                <Space>
                                    <TeamOutlined className="text-indigo-500" />
                                    <span>Team Members</span>
                                </Space>
                            }
                            bordered={false} 
                            className="shadow-sm border-gray-100 rounded-xl overflow-hidden h-full"
                        >
                            {isLoading ? (
                                <div className="py-12 flex justify-center"><Spin /></div>
                            ) : (
                                <motion.div variants={listVariants}>
                                    <List
                                        dataSource={data?.recent_users}
                                        renderItem={(u) => (
                                            <motion.div variants={listItemVariants}>
                                                <List.Item className="px-2 py-3">
                                                    <List.Item.Meta
                                                        avatar={<div className="w-2 h-2 rounded-full bg-green-400 mt-4" />}
                                                        title={<Text strong className="text-sm">{u.name}</Text>}
                                                        description={<Text type="secondary" className="text-[10px] uppercase font-bold">{u.role_name}</Text>}
                                                    />
                                                </List.Item>
                                            </motion.div>
                                        )}
                                    />
                                </motion.div>
                            )}
                        </Card>
                    </motion.div>
                </Col>
            </Row>
        </motion.div>
    );
};

export default HomePage;
