import React, { useState, useMemo } from 'react';
import {
    Button, Tabs, Space, Typography, Tag, Card, Input, Row, Col, Empty, Spin
} from 'antd';
import {
    BookOutlined,
    CheckCircleOutlined,
    ClockCircleOutlined,
    ExclamationCircleOutlined,
    ExportOutlined,
    EyeOutlined,
    SearchOutlined,
    ReloadOutlined
} from '@ant-design/icons';
import { motion, type Variants } from 'motion/react';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/vi';

import { useAuth } from '@/features/auth';
import { useMyHomeworks, useUnsubmittedByUser } from '../hooks/useHomeworks';
import type { Homework } from '../types/homework.types';
import { HomeworkDetailDrawer } from '../components';

dayjs.extend(relativeTime);
dayjs.locale('vi');

const { Title, Text } = Typography;

const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.1 } }
};

const itemVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } }
};

export const MyHomeworkPage: React.FC = () => {
    const { user } = useAuth();
    const [activeTab, setActiveTab] = useState<string>('all');
    const [searchText, setSearchText] = useState<string>('');
    const [detailHomework, setDetailHomework] = useState<Homework | null>(null);

    const { data: myHomeworksData, isLoading: isMyLoading, refetch: refetchMy } = useMyHomeworks();
    const { data: unsubmittedHomeworksData, isLoading: isUnsubLoading, refetch: refetchUnsub } = useUnsubmittedByUser(user?.id ?? null);

    const myHomeworks = myHomeworksData || [];
    const unsubmittedHomeworks = unsubmittedHomeworksData || [];

    const isLoading = isMyLoading || isUnsubLoading;

    const unsubmittedIdsSet = useMemo(() => {
        return new Set(unsubmittedHomeworks.map(hw => hw.id));
    }, [unsubmittedHomeworks]);

    const processedHomeworks = useMemo(() => {
        const now = dayjs();
        return myHomeworks.map(hw => {
            const isUnsubmitted = unsubmittedIdsSet.has(hw.id);
            const isSubmitted = !isUnsubmitted;
            const isOverdue = isUnsubmitted && dayjs(hw.deadline).isBefore(now);

            return {
                ...hw,
                isSubmitted,
                isOverdue,
            };
        });
    }, [myHomeworks, unsubmittedIdsSet]);

    // Filtered homework list based on tab & search text
    const filteredHomeworks = useMemo(() => {
        return processedHomeworks.filter(hw => {
            const matchesSearch = hw.title.toLowerCase().includes(searchText.toLowerCase());
            if (!matchesSearch) return false;

            if (activeTab === 'unsubmitted') {
                return !hw.isSubmitted;
            }
            if (activeTab === 'submitted') {
                return hw.isSubmitted;
            }
            if (activeTab === 'overdue') {
                return hw.isOverdue;
            }
            return true;
        });
    }, [processedHomeworks, activeTab, searchText]);

    // Statistics
    const stats = useMemo(() => {
        const total = processedHomeworks.length;
        const submitted = processedHomeworks.filter(h => h.isSubmitted).length;
        const unsubmitted = processedHomeworks.filter(h => !h.isSubmitted).length;
        const overdue = processedHomeworks.filter(h => h.isOverdue).length;
        return { total, submitted, unsubmitted, overdue };
    }, [processedHomeworks]);

    const handleRefresh = () => {
        refetchMy();
        refetchUnsub();
    };

    const renderStatusBadge = (record: { isSubmitted: boolean; isOverdue: boolean; deadline: string }) => {
        if (record.isSubmitted) {
            return (
                <Tag icon={<CheckCircleOutlined />} color="success" className="px-3 py-1 text-xs font-semibold rounded-full">
                    Đã nộp bài
                </Tag>
            );
        }
        if (record.isOverdue) {
            return (
                <Tag icon={<ExclamationCircleOutlined />} color="error" className="px-3 py-1 text-xs font-semibold rounded-full">
                    Quá hạn nộp
                </Tag>
            );
        }
        return (
            <Tag icon={<ClockCircleOutlined />} color="warning" className="px-3 py-1 text-xs font-semibold rounded-full">
                Chưa nộp
            </Tag>
        );
    };

    const renderDeadlineText = (deadline: string, isOverdue: boolean) => {
        const d = dayjs(deadline);
        const formatted = d.format('DD/MM/YYYY HH:mm');
        const fromNow = d.fromNow();

        return (
            <div>
                <div className={`font-medium text-sm ${isOverdue ? 'text-red-600' : 'text-gray-800'}`}>
                    {formatted}
                </div>
                <div className={`text-xs ${isOverdue ? 'text-red-500' : 'text-gray-500'}`}>
                    {isOverdue ? `Hết hạn ${fromNow}` : `Còn ${fromNow}`}
                </div>
            </div>
        );
    };

    return (
        <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="p-4 md:p-6 bg-white md:rounded-xl shadow-xs min-h-full"
        >
            {/* Page Header */}
            <motion.div variants={itemVariants} className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
                <Space size="middle">
                    <div className="w-12 h-12 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600 shadow-sm">
                        <BookOutlined className="text-2xl" />
                    </div>
                    <div>
                        <Title level={3} className="!mb-0 text-xl md:text-2xl text-indigo-600 font-bold">
                            Bài tập của tôi
                        </Title>
                        <Text type="secondary" className="text-xs md:text-sm">
                            Xem bài tập được giao, hạn nộp và trạng thái làm bài trên hệ thống Quiz
                        </Text>
                    </div>
                </Space>
                <Button
                    icon={<ReloadOutlined />}
                    onClick={handleRefresh}
                    loading={isLoading}
                    className="h-10 px-4 rounded-lg border-gray-200 hover:border-indigo-500"
                >
                    Làm mới
                </Button>
            </motion.div>

            {/* Stat Cards */}
            <motion.div variants={itemVariants} className="mb-6">
                <Row gutter={[16, 16]}>
                    <Col xs={12} sm={6}>
                        <Card bordered={false} className="bg-indigo-50/60 rounded-xl shadow-2xs">
                            <Text type="secondary" className="text-xs uppercase font-semibold">Tất cả bài tập</Text>
                            <Title level={3} className="!mt-1 !mb-0 text-indigo-700">{stats.total}</Title>
                        </Card>
                    </Col>
                    <Col xs={12} sm={6}>
                        <Card bordered={false} className="bg-emerald-50/60 rounded-xl shadow-2xs">
                            <Text type="secondary" className="text-xs uppercase font-semibold">Đã hoàn thành</Text>
                            <Title level={3} className="!mt-1 !mb-0 text-emerald-600">{stats.submitted}</Title>
                        </Card>
                    </Col>
                    <Col xs={12} sm={6}>
                        <Card bordered={false} className="bg-amber-50/60 rounded-xl shadow-2xs">
                            <Text type="secondary" className="text-xs uppercase font-semibold">Chưa nộp</Text>
                            <Title level={3} className="!mt-1 !mb-0 text-amber-600">{stats.unsubmitted}</Title>
                        </Card>
                    </Col>
                    <Col xs={12} sm={6}>
                        <Card bordered={false} className="bg-rose-50/60 rounded-xl shadow-2xs">
                            <Text type="secondary" className="text-xs uppercase font-semibold">Quá hạn</Text>
                            <Title level={3} className="!mt-1 !mb-0 text-rose-600">{stats.overdue}</Title>
                        </Card>
                    </Col>
                </Row>
            </motion.div>

            {/* Filter Tabs & Search */}
            <motion.div variants={itemVariants} className="mb-4 flex flex-col md:flex-row justify-between items-stretch md:items-center gap-4">
                <Tabs
                    activeKey={activeTab}
                    onChange={setActiveTab}
                    className="flex-1 border-b-0"
                    items={[
                        { key: 'all', label: `Tất cả (${stats.total})` },
                        { key: 'unsubmitted', label: `Chưa nộp (${stats.unsubmitted})` },
                        { key: 'submitted', label: `Đã nộp (${stats.submitted})` },
                        { key: 'overdue', label: `Quá hạn (${stats.overdue})` },
                    ]}
                />
                <Input
                    prefix={<SearchOutlined className="text-gray-400" />}
                    placeholder="Tìm theo tên bài tập..."
                    value={searchText}
                    onChange={e => setSearchText(e.target.value)}
                    allowClear
                    className="w-full md:w-64 h-10 rounded-lg shadow-2xs"
                />
            </motion.div>

            {/* Homework List */}
            <motion.div variants={itemVariants}>
                {isLoading ? (
                    <div className="py-16 flex justify-center items-center">
                        <Spin size="large" tip="Đang tải danh sách bài tập..." />
                    </div>
                ) : filteredHomeworks.length === 0 ? (
                    <Empty
                        description={
                            searchText
                                ? "Không tìm thấy bài tập nào phù hợp"
                                : activeTab === 'unsubmitted'
                                    ? "Tuyệt vời! Bạn không có bài tập nào chưa nộp"
                                    : "Chưa có bài tập nào"
                        }
                        className="py-12"
                    />
                ) : (
                    <div className="space-y-4">
                        {filteredHomeworks.map((hw) => (
                            <Card
                                key={hw.id}
                                hoverable
                                className={`rounded-xl border transition-all shadow-2xs hover:shadow-xs ${hw.isOverdue
                                    ? 'border-red-200 bg-red-50/20'
                                    : hw.isSubmitted
                                        ? 'border-emerald-200 bg-emerald-50/10'
                                        : 'border-gray-200 bg-white'
                                    }`}
                            >
                                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-2 flex-wrap">
                                            {renderStatusBadge(hw)}
                                        </div>
                                        <Title level={5} className="!mb-1 text-gray-800 font-semibold truncate text-base">
                                            {hw.title}
                                        </Title>
                                        <div className="mt-2 text-xs text-gray-500">
                                            Hạn nộp: {renderDeadlineText(hw.deadline, hw.isOverdue)}
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-2 w-full md:w-auto justify-end pt-2 md:pt-0 border-t md:border-t-0 border-gray-100">
                                        {hw.link && (
                                            <Button
                                                type="primary"
                                                icon={<ExportOutlined />}
                                                href={hw.link}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className={`${hw.isSubmitted
                                                    ? 'bg-emerald-600 hover:bg-emerald-700'
                                                    : 'bg-indigo-600 hover:bg-indigo-700'
                                                    } font-medium h-9 rounded-lg`}
                                            >
                                                {hw.isSubmitted ? 'Xem bài nộp trên Quiz ↗' : 'Làm bài ngay ↗'}
                                            </Button>
                                        )}
                                    </div>
                                </div>
                            </Card>
                        ))}
                    </div>
                )}
            </motion.div>

            {/* Detail Drawer */}
            <HomeworkDetailDrawer
                homework={detailHomework}
                onClose={() => setDetailHomework(null)}
            />
        </motion.div>
    );
};

export default MyHomeworkPage;
