import React from 'react';
import { Modal, Descriptions, Tag, Button, Space } from 'antd';
import { LinkOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { useNavigate } from 'react-router-dom';
import type { Notification } from '../types/notification.types';

interface NotificationDetailModalProps {
    notification: Notification | null;
    open: boolean;
    onClose: () => void;
    onMarkAsRead: (id: number) => void;
}

const NotificationDetailModal: React.FC<NotificationDetailModalProps> = ({
    notification,
    open,
    onClose,
    onMarkAsRead,
}) => {
    const navigate = useNavigate();

    if (!notification) return null;

    const handleNavigate = () => {
        if (!notification.is_read) {
            onMarkAsRead(notification.id);
        }
        onClose();
        if (notification.action_url) {
            if (notification.action_url.startsWith('http')) {
                window.open(notification.action_url, '_blank');
            } else {
                navigate(notification.action_url);
            }
        }
    };

    return (
        <Modal
            title={<span className="text-lg font-bold text-slate-800 dark:text-slate-100">{notification.title}</span>}
            open={open}
            onCancel={onClose}
            footer={[
                <Button key="close" onClick={onClose}>
                    Đóng
                </Button>,
                notification.action_url && (
                    <Button
                        key="action"
                        type="primary"
                        icon={<LinkOutlined />}
                        onClick={handleNavigate}
                        className="bg-indigo-600 hover:bg-indigo-700"
                    >
                        Chuyển đến trang nhiệm vụ
                    </Button>
                ),
            ]}
        >
            <div className="py-2">
                <Descriptions column={1} bordered size="small" className="mb-4">
                    <Descriptions.Item label="Phân loại">
                        <Tag color="blue">{notification.category}</Tag>
                    </Descriptions.Item>
                    <Descriptions.Item label="Mức độ">
                        <Tag color={notification.level === 'CRITICAL' ? 'red' : 'orange'}>
                            {notification.level}
                        </Tag>
                    </Descriptions.Item>
                    <Descriptions.Item label="Thời gian">
                        {dayjs(notification.created_at).format('DD/MM/YYYY HH:mm:ss')}
                    </Descriptions.Item>
                    <Descriptions.Item label="Trạng thái">
                        <Tag color={notification.is_read ? 'green' : 'volcano'}>
                            {notification.is_read ? 'Đã đọc' : 'Chưa đọc'}
                        </Tag>
                    </Descriptions.Item>
                </Descriptions>

                <div className="bg-slate-50 dark:bg-slate-900/50 p-4 rounded-xl border border-slate-200 dark:border-slate-800">
                    <div className="text-xs uppercase font-bold text-slate-400 mb-1">Nội dung chi tiết</div>
                    <div className="whitespace-pre-wrap text-sm text-slate-700 dark:text-slate-200 leading-relaxed">
                        {notification.content}
                    </div>
                </div>
            </div>
        </Modal>
    );
};

export default NotificationDetailModal;
