import React, { useState } from 'react';
import { Typography, Badge, Card, Grid, Button, message } from 'antd';
import { BellOutlined, ExperimentOutlined } from '@ant-design/icons';
import { motion, type Variants } from 'motion/react';
import { pushService } from '@/features/pwa/services/pushService';
import { useInAppNotifications } from '../hooks/useInAppNotifications';
import {
    NotificationFilter,
    NotificationTable,
    NotificationDetailModal,
} from '../components';
import type { Notification } from '../types/notification.types';

const { Title, Text } = Typography;

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
    hidden: { opacity: 0, y: 20 },
    visible: {
        opacity: 1,
        y: 0,
        transition: { duration: 0.4, ease: 'easeOut' },
    },
};

const NotificationManagementPage: React.FC = () => {
    const screens = Grid.useBreakpoint();
    const {
        notifications,
        unreadCount,
        loading,
        total,
        page,
        setPage,
        pageSize,
        setPageSize,
        category,
        setCategory,
        isRead,
        setIsRead,
        refresh,
        markAsRead,
        markAllAsRead,
    } = useInAppNotifications();

    const [selectedNotification, setSelectedNotification] =
        useState<Notification | null>(null);
    const [detailModalOpen, setDetailModalOpen] = useState<boolean>(false);
    const [testPushLoading, setTestPushLoading] = useState<boolean>(false);

    const handleTestPush = async () => {
        setTestPushLoading(true);
        try {
            const res = await pushService.testPush();
            if (res.is_success && res.data && res.data.sent_count > 0) {
                message.success(`Đã gửi thông báo đẩy tới ${res.data.sent_count} thiết bị! Hãy kiểm tra màn hình khóa.`);
            } else {
                message.info('Chưa có thiết bị nào kích hoạt Web Push. Hãy bấm "Bật thông báo" trên thanh gợi ý trước.');
            }
        } catch (err) {
            console.error('Lỗi khi gửi test push:', err);
            message.error('Không thể gửi thông báo thử nghiệm. Vui lòng thử lại sau.');
        } finally {
            setTestPushLoading(false);
        }
    };

    const handleViewDetail = (item: Notification) => {
        setSelectedNotification(item);
        setDetailModalOpen(true);
    };

    const handlePageChange = (newPage: number, newPageSize: number) => {
        setPage(newPage);
        setPageSize(newPageSize);
    };

    return (
        <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="p-4 md:p-6"
        >
            <Card
                className={
                    !screens.md
                        ? 'bg-transparent shadow-none border-none'
                        : 'shadow-sm border-gray-100 rounded-xl overflow-hidden'
                }
                styles={{ body: { padding: !screens.md ? 0 : undefined } }}
            >
                {/* Header section */}
                <motion.div
                    variants={itemVariants}
                    className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6 px-3 md:px-0"
                >
                    <div className="flex items-center gap-3">
                        <div className="hidden md:flex w-12 h-12 rounded-xl bg-indigo-50 items-center justify-center text-indigo-600 text-2xl font-bold">
                            <BellOutlined />
                        </div>
                        <div>
                            <div className="flex items-center gap-2">
                                <Title
                                    level={3}
                                    className="!m-0 text-xl md:text-2xl text-[#4f46e5] font-bold"
                                >
                                    Thông báo của tôi
                                </Title>
                                {unreadCount > 0 && (
                                    <Badge
                                        count={unreadCount}
                                        overflowCount={99}
                                        className="site-badge-count-4"
                                    />
                                )}
                            </div>
                            <Text type="secondary" className="text-xs md:text-sm">
                                Theo dõi các nhắc nhở bài tập, ca trực nhật vệ sinh và thông báo quan trọng từ hệ thống
                            </Text>
                        </div>
                    </div>
                    <div className="flex items-center gap-2 w-full md:w-auto justify-end">
                        <Button
                            icon={<ExperimentOutlined />}
                            onClick={handleTestPush}
                            loading={testPushLoading}
                            className="rounded-lg text-xs"
                        >
                            Thử thông báo đẩy
                        </Button>
                    </div>
                </motion.div>

                {/* Filter Section */}
                <motion.div variants={itemVariants}>
                    <NotificationFilter
                        category={category}
                        onCategoryChange={setCategory}
                        isRead={isRead}
                        onIsReadChange={setIsRead}
                        onRefresh={refresh}
                        onMarkAllAsRead={markAllAsRead}
                        hasUnread={unreadCount > 0}
                    />
                </motion.div>

                {/* Data Table Section */}
                <motion.div variants={itemVariants}>
                    <NotificationTable
                        notifications={notifications}
                        loading={loading}
                        total={total}
                        page={page}
                        pageSize={pageSize}
                        onPageChange={handlePageChange}
                        onMarkAsRead={markAsRead}
                        onViewDetail={handleViewDetail}
                    />
                </motion.div>
            </Card>

            {/* Modal Detail */}
            <NotificationDetailModal
                notification={selectedNotification}
                open={detailModalOpen}
                onClose={() => setDetailModalOpen(false)}
                onMarkAsRead={markAsRead}
            />
        </motion.div>
    );
};

export default NotificationManagementPage;
