import React from 'react';
import { Table, Tag, Button, Space, Tooltip, Popconfirm } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
    EyeOutlined,
    CheckOutlined,
    DeleteOutlined,
    LinkOutlined,
    BookOutlined,
    CarryOutOutlined,
    VideoCameraOutlined,
    BellOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { useNavigate } from 'react-router-dom';
import type { Notification, NotificationCategory, NotificationLevel } from '../types/notification.types';

interface NotificationTableProps {
    notifications: Notification[];
    loading: boolean;
    total: number;
    page: number;
    pageSize: number;
    onPageChange: (page: number, pageSize: number) => void;
    onMarkAsRead: (id: number) => void;
    onViewDetail: (notification: Notification) => void;
}

const categoryConfig: Record<NotificationCategory, { label: string; color: string; icon: React.ReactNode }> = {
    HOMEWORK: { label: 'Bài tập', color: 'blue', icon: <BookOutlined /> },
    DUTY: { label: 'Trực nhật', color: 'cyan', icon: <CarryOutOutlined /> },
    MEETING: { label: 'Cuộc họp', color: 'purple', icon: <VideoCameraOutlined /> },
    SYSTEM: { label: 'Hệ thống', color: 'default', icon: <BellOutlined /> },
};

const levelConfig: Record<NotificationLevel, { label: string; color: string }> = {
    INFO: { label: 'Thông tin', color: 'blue' },
    WARNING: { label: 'Cảnh báo', color: 'orange' },
    CRITICAL: { label: 'Khẩn cấp', color: 'red' },
};

const NotificationTable: React.FC<NotificationTableProps> = ({
    notifications,
    loading,
    total,
    page,
    pageSize,
    onPageChange,
    onMarkAsRead,
    onViewDetail,
}) => {
    const navigate = useNavigate();

    const handleActionClick = (item: Notification) => {
        if (!item.is_read) {
            onMarkAsRead(item.id);
        }
        if (item.action_url) {
            if (item.action_url.startsWith('http')) {
                window.open(item.action_url, '_blank');
            } else {
                navigate(item.action_url);
            }
        } else {
            onViewDetail(item);
        }
    };

    const columns: ColumnsType<Notification> = [
        {
            title: 'Trạng thái',
            dataIndex: 'is_read',
            key: 'is_read',
            width: 100,
            render: (isRead: boolean) => (
                <Tag color={isRead ? 'default' : 'error'} className="font-semibold">
                    {isRead ? 'Đã đọc' : 'Chưa đọc'}
                </Tag>
            ),
        },
        {
            title: 'Phân loại',
            dataIndex: 'category',
            key: 'category',
            width: 130,
            render: (cat: NotificationCategory) => {
                const conf = categoryConfig[cat] || categoryConfig.SYSTEM;
                return (
                    <Tag icon={conf.icon} color={conf.color}>
                        {conf.label}
                    </Tag>
                );
            },
        },
        {
            title: 'Mức độ',
            dataIndex: 'level',
            key: 'level',
            width: 110,
            render: (lvl: NotificationLevel) => {
                const conf = levelConfig[lvl] || levelConfig.INFO;
                return <Tag color={conf.color}>{conf.label}</Tag>;
            },
        },
        {
            title: 'Tiêu đề & Nội dung',
            key: 'title_content',
            render: (_, record) => (
                <div
                    className="cursor-pointer group"
                    onClick={() => onViewDetail(record)}
                >
                    <div className="font-semibold text-slate-800 dark:text-slate-100 group-hover:text-indigo-600 transition-colors">
                        {record.title}
                    </div>
                    <div className="text-xs text-slate-500 line-clamp-1 mt-0.5">
                        {record.content}
                    </div>
                </div>
            ),
        },
        {
            title: 'Thời gian nhận',
            dataIndex: 'created_at',
            key: 'created_at',
            width: 160,
            render: (time: string) => (
                <span className="text-xs text-slate-500">
                    {dayjs(time).format('DD/MM/YYYY HH:mm')}
                </span>
            ),
        },
        {
            title: 'Thao tác',
            key: 'actions',
            width: 180,
            align: 'right',
            render: (_, record) => (
                <Space size="small">
                    {record.action_url && (
                        <Tooltip title="Mở trang nhiệm vụ">
                            <Button
                                size="small"
                                type="primary"
                                icon={<LinkOutlined />}
                                onClick={() => handleActionClick(record)}
                                className="bg-indigo-600 hover:bg-indigo-700"
                            >
                                Thực hiện
                            </Button>
                        </Tooltip>
                    )}
                    {!record.is_read && (
                        <Tooltip title="Đánh dấu đã đọc">
                            <Button
                                size="small"
                                icon={<CheckOutlined />}
                                onClick={() => onMarkAsRead(record.id)}
                            />
                        </Tooltip>
                    )}
                    <Tooltip title="Xem chi tiết">
                        <Button
                            size="small"
                            icon={<EyeOutlined />}
                            onClick={() => onViewDetail(record)}
                        />
                    </Tooltip>
                </Space>
            ),
        },
    ];

    return (
        <Table<Notification>
            rowKey="id"
            columns={columns}
            dataSource={notifications}
            loading={loading}
            className="border border-gray-100 rounded-lg custom-table"
            scroll={{ x: 800 }}
            pagination={{
                current: page,
                pageSize: pageSize,
                total: total,
                showSizeChanger: true,
                pageSizeOptions: ['10', '20', '50', '100'],
                showTotal: (totalCount, range) =>
                    `${range[0]}-${range[1]} trên tổng số ${totalCount} thông báo`,
                onChange: onPageChange,
            }}
        />
    );
};

export default NotificationTable;
