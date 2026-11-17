import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Empty, Pagination, Space, Spin, Tooltip, Typography, message } from 'antd';
import { BookOutlined, ReloadOutlined, SyncOutlined } from '@ant-design/icons';
import { motion, type Variants } from 'motion/react';

import { useMyHomeworks, useSyncMyUnsubmitted } from '../hooks/useHomeworks';
import {
    HomeworkCard,
    MyHomeworkFilterBar,
    MyHomeworkStatsCards,
} from '../components';
import type { HomeworkFilterStatus } from '../types/homework.types';

const { Title, Text } = Typography;

const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.08 } },
};

const itemVariants: Variants = {
    hidden: { opacity: 0, y: 16 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.35, ease: 'easeOut' } },
};

export const MyHomeworkPage: React.FC = () => {
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState<HomeworkFilterStatus>('all');
    const [searchInput, setSearchInput] = useState<string>('');
    const [debouncedSearch, setDebouncedSearch] = useState<string>('');
    const [page, setPage] = useState<number>(1);
    const [pageSize, setPageSize] = useState<number>(20);

    // Debounce search & reset page to 1 (Constitution Principle XII)
    useEffect(() => {
        const timer = window.setTimeout(() => {
            setDebouncedSearch(searchInput.trim());
            setPage(1);
        }, 300);
        return () => window.clearTimeout(timer);
    }, [searchInput]);

    const { data, isLoading, isFetching, refetch } = useMyHomeworks({
        page,
        pageSize,
        status: activeTab,
        search: debouncedSearch,
    });

    const { mutate: syncMyUnsubmitted, isPending: isSyncingAll } = useSyncMyUnsubmitted();

    const items = data?.items ?? [];
    const stats = data?.stats ?? {
        total: 0,
        completed: 0,
        completed_on_time: 0,
        completed_late: 0,
        uncompleted: 0,
        overdue: 0,
    };
    const totalFiltered = data?.pagination?.total ?? items.length;

    const handleTabChange = (nextStatus: HomeworkFilterStatus) => {
        setActiveTab(nextStatus);
        setPage(1);
    };

    const handleSyncAllUnsubmitted = () => {
        syncMyUnsubmitted(undefined, {
            onSuccess: (res) => {
                message.success(res?.message || 'Đã đồng bộ kết quả mới nhất từ Quiz.');
            },
            onError: () => {
                message.error('Không thể đồng bộ từ Quiz. Vui lòng thử lại sau.');
            },
        });
    };

    return (
        <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="p-4 md:p-6 bg-white md:rounded-xl shadow-xs min-h-full"
        >
            {/* Page Header */}
            <motion.div
                variants={itemVariants}
                className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4"
            >
                <Space size="middle">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-50 to-indigo-100/60 flex items-center justify-center text-indigo-600 shadow-xs border border-indigo-100">
                        <BookOutlined className="text-2xl" />
                    </div>
                    <div>
                        <Title level={3} className="!mb-0 text-xl md:text-2xl text-indigo-600 font-bold">
                            Bài tập của tôi
                        </Title>
                        <Text type="secondary" className="text-xs md:text-sm">
                            Theo dõi bài tập được giao, hạn nộp cá nhân và tiến độ hoàn thành trên hệ thống Quiz
                        </Text>
                    </div>
                </Space>

                <Space wrap>
                    {(stats.uncompleted ?? 0) > 0 && (
                        <Tooltip title="Kéo kết quả mới nhất từ hệ thống Quiz cho các bài tập chưa hoàn thành">
                            <Button
                                type="primary"
                                icon={<SyncOutlined spin={isSyncingAll} />}
                                loading={isSyncingAll}
                                onClick={handleSyncAllUnsubmitted}
                                className="h-10 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-medium"
                            >
                                Đồng bộ từ Quiz
                            </Button>
                        </Tooltip>
                    )}
                    <Button
                        icon={<ReloadOutlined />}
                        onClick={() => refetch()}
                        loading={isFetching}
                        className="h-10 px-4 rounded-xl border-gray-200 hover:border-indigo-500 font-medium"
                    >
                        Làm mới
                    </Button>
                </Space>
            </motion.div>

            {/* Stat Cards (100% server-computed across all assigned homeworks) */}
            <motion.div variants={itemVariants} className="mb-6">
                <MyHomeworkStatsCards stats={stats} />
            </motion.div>

            {/* Server-driven Filter Tabs & Search */}
            <motion.div variants={itemVariants} className="mb-5">
                <MyHomeworkFilterBar
                    activeTab={activeTab}
                    onTabChange={handleTabChange}
                    searchInput={searchInput}
                    onSearchChange={setSearchInput}
                    stats={stats}
                />
            </motion.div>

            {/* Homework List & Server Pagination */}
            <motion.div variants={itemVariants}>
                {isLoading ? (
                    <div className="py-16 flex justify-center items-center">
                        <Spin size="large" tip="Đang tải danh sách bài tập..." />
                    </div>
                ) : items.length === 0 ? (
                    <Empty
                        description={
                            debouncedSearch
                                ? 'Không tìm thấy bài tập nào phù hợp'
                                : activeTab === 'uncompleted'
                                    ? 'Tuyệt vời! Bạn đã hoàn thành toàn bộ bài tập được giao'
                                    : activeTab === 'overdue'
                                        ? 'Bạn không có bài tập nào quá hạn chưa hoàn thành'
                                        : 'Chưa có bài tập nào'
                        }
                        className="py-12"
                    />
                ) : (
                    <>
                        <div className="space-y-4">
                            {items.map((hw) => (
                                <HomeworkCard
                                    key={hw.id}
                                    homework={hw}
                                    onViewDetail={(item) => navigate(`/dashboard/my-homeworks/${item.id}`)}
                                />
                            ))}
                        </div>

                        {totalFiltered > 0 && (
                            <div className="mt-6 flex justify-end">
                                <Pagination
                                    current={page}
                                    pageSize={pageSize}
                                    total={totalFiltered}
                                    pageSizeOptions={['10', '20', '50', '100']}
                                    showSizeChanger
                                    showTotal={(total, range) =>
                                        `Hiển thị ${range[0]}-${range[1]} / ${total} bài tập`
                                    }
                                    onChange={(nextPage, nextSize) => {
                                        if (nextSize !== pageSize) {
                                            setPageSize(nextSize);
                                            setPage(1);
                                        } else {
                                            setPage(nextPage);
                                        }
                                    }}
                                />
                            </div>
                        )}
                    </>
                )}
            </motion.div>
        </motion.div>
    );
};

export default MyHomeworkPage;
