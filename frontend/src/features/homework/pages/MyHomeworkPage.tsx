import React, { useState, useMemo } from 'react';
import {
    Button, Tabs, Space, Typography, Input, Row, Col, Empty, Spin
} from 'antd';
import {
    BookOutlined,
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
import { HomeworkDetailDrawer, HomeworkCard } from '../components';

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
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-50 to-indigo-100/60 flex items-center justify-center text-indigo-600 shadow-xs border border-indigo-100">
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
                    className="h-10 px-4 rounded-xl border-gray-200 hover:border-indigo-500 font-medium"
                >
                    Làm mới
                </Button>
            </motion.div>

            {/* Stat Cards */}
            <motion.div variants={itemVariants} className="mb-6">
                <Row gutter={[16, 16]}>
                    <Col xs={12} sm={6}>
                        <div className="p-4 rounded-2xl bg-gradient-to-br from-indigo-50/70 via-indigo-50/30 to-slate-50 border border-indigo-100/70 shadow-2xs hover:shadow-xs transition-all">
                            <Text type="secondary" className="text-xs uppercase font-bold tracking-wider text-indigo-600/80">Tất cả bài tập</Text>
                            <div className="text-2xl sm:text-3xl font-extrabold text-indigo-700 mt-1">{stats.total}</div>
                        </div>
                    </Col>
                    <Col xs={12} sm={6}>
                        <div className="p-4 rounded-2xl bg-gradient-to-br from-emerald-50/70 via-emerald-50/30 to-teal-50/30 border border-emerald-100/70 shadow-2xs hover:shadow-xs transition-all">
                            <Text type="secondary" className="text-xs uppercase font-bold tracking-wider text-emerald-600/80">Đã hoàn thành</Text>
                            <div className="text-2xl sm:text-3xl font-extrabold text-emerald-600 mt-1">{stats.submitted}</div>
                        </div>
                    </Col>
                    <Col xs={12} sm={6}>
                        <div className="p-4 rounded-2xl bg-gradient-to-br from-amber-50/70 via-amber-50/30 to-yellow-50/30 border border-amber-100/70 shadow-2xs hover:shadow-xs transition-all">
                            <Text type="secondary" className="text-xs uppercase font-bold tracking-wider text-amber-600/80">Chưa nộp</Text>
                            <div className="text-2xl sm:text-3xl font-extrabold text-amber-600 mt-1">{stats.unsubmitted}</div>
                        </div>
                    </Col>
                    <Col xs={12} sm={6}>
                        <div className="p-4 rounded-2xl bg-gradient-to-br from-rose-50/70 via-rose-50/30 to-pink-50/30 border border-rose-100/70 shadow-2xs hover:shadow-xs transition-all">
                            <Text type="secondary" className="text-xs uppercase font-bold tracking-wider text-rose-600/80">Quá hạn</Text>
                            <div className="text-2xl sm:text-3xl font-extrabold text-rose-600 mt-1">{stats.overdue}</div>
                        </div>
                    </Col>
                </Row>
            </motion.div>

            {/* Filter Tabs & Search */}
            <motion.div variants={itemVariants} className="mb-5 flex flex-col md:flex-row justify-between items-stretch md:items-center gap-4">
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
                    className="w-full md:w-64 h-10 rounded-xl shadow-2xs"
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
                            <HomeworkCard
                                key={hw.id}
                                homework={hw}
                                onViewDetail={(item) => setDetailHomework(item)}
                            />
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

