import React from 'react';
import { Space, Select, Button } from 'antd';
import { ReloadOutlined, CheckOutlined } from '@ant-design/icons';
import type { NotificationCategory } from '../types/notification.types';

interface NotificationFilterProps {
    category: NotificationCategory | undefined;
    onCategoryChange: (value: NotificationCategory | undefined) => void;
    isRead: boolean | undefined;
    onIsReadChange: (value: boolean | undefined) => void;
    onRefresh: () => void;
    onMarkAllAsRead: () => void;
    hasUnread: boolean;
}

const NotificationFilter: React.FC<NotificationFilterProps> = ({
    category,
    onCategoryChange,
    isRead,
    onIsReadChange,
    onRefresh,
    onMarkAllAsRead,
    hasUnread,
}) => {
    return (
        <div className="mb-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
                <Space wrap size="middle">
                    <Select
                        placeholder="Phân loại nhiệm vụ"
                        allowClear
                        value={category}
                        onChange={onCategoryChange}
                        style={{ width: 200 }}
                        options={[
                            { label: 'Tất cả phân loại', value: undefined },
                            { label: '📚 Bài tập (Homework)', value: 'HOMEWORK' },
                            { label: '🧹 Trực nhật (Duty)', value: 'DUTY' },
                            { label: '📹 Cuộc họp (Meeting)', value: 'MEETING' },
                            { label: '⚙️ Hệ thống (System)', value: 'SYSTEM' },
                        ]}
                    />

                    <Select
                        placeholder="Trạng thái đọc"
                        allowClear
                        value={isRead}
                        onChange={onIsReadChange}
                        style={{ width: 170 }}
                        options={[
                            { label: 'Tất cả trạng thái', value: undefined },
                            { label: '🔴 Chưa đọc', value: false },
                            { label: '🟢 Đã đọc', value: true },
                        ]}
                    />
                </Space>

                <Space wrap size="middle">
                    <Button
                        icon={<CheckOutlined />}
                        onClick={onMarkAllAsRead}
                        disabled={!hasUnread}
                        className="hover:border-indigo-500"
                    >
                        Đánh dấu tất cả đã đọc
                    </Button>
                    <Button
                        icon={<ReloadOutlined />}
                        onClick={onRefresh}
                        type="primary"
                        className="bg-indigo-600 hover:bg-indigo-700"
                    >
                        Làm mới
                    </Button>
                </Space>
            </div>
        </div>
    );
};

export default NotificationFilter;
