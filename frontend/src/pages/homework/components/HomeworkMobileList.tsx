import React from 'react';
import { List, Card, Button, Space, Popconfirm, Typography } from 'antd';
import { UploadOutlined, EyeOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import type { Homework } from '@/types/homework.types';
import { HomeworkPermission } from '@/types/rbac.types';
import { SubmissionStatusTag } from './SubmissionStatusTag';
import { DeadlineText } from './DeadlineText';

import { useAuth } from '@/context/AuthContext';

const { Text } = Typography;

interface HomeworkMobileListProps {
    dataSource: Homework[];
    loading: boolean;
    emptyText?: string;
    activeTab: string;
    handlers: {
        handleOpenSubmit: (homework: Homework) => void;
        handleViewSubmissions: (homework: Homework) => void;
        handleOpenEdit: (homework: Homework) => void;
        handleDelete: (id: number) => void;
    };
}

export const HomeworkMobileList: React.FC<HomeworkMobileListProps> = ({
    dataSource,
    loading,
    emptyText,
    activeTab,
    handlers
}) => {
    const { hasPermission } = useAuth();
    const { handleOpenSubmit, handleViewSubmissions, handleOpenEdit, handleDelete } = handlers;

    return (
        <div className="mt-4 px-3">
            <List
                dataSource={dataSource}
                loading={loading}
                split={false}
                locale={{ emptyText }}
                renderItem={(record) => (
                    <List.Item className="px-2 !mb-4 !border-0">
                        <Card
                            className="w-full shadow-sm border-gray-100 overflow-hidden"
                            styles={{ body: { padding: '16px' } }}
                        >
                            <div className="flex items-center justify-between mb-4">
                                <Text strong className="text-base truncate max-w-[70%]">{record.title}</Text>
                                <SubmissionStatusTag record={record} />
                            </div>

                            <div className="flex items-center gap-2 mb-4 text-xs">
                                <Text type="secondary">Hạn nộp:</Text>
                                <DeadlineText date={record.deadline} record={record} showOverdueTag={false} />
                            </div>

                            <div className="flex justify-end gap-2 pt-3 border-t border-gray-50 bg-gray-50 -mx-4 -mb-4 px-4 py-3">
                                {activeTab === '1' ? (
                                    <Button
                                        type="primary"
                                        size="small"
                                        icon={<UploadOutlined />}
                                        onClick={() => handleOpenSubmit(record)}
                                        className="bg-indigo-600"
                                    >
                                        Nộp bài
                                    </Button>
                                ) : (
                                    <Space size="small">
                                        <Button size="small" icon={<EyeOutlined />} onClick={() => handleViewSubmissions(record)}>
                                            Bài nộp
                                        </Button>
                                        {hasPermission(HomeworkPermission.UPDATE) && (
                                            <Button size="small" icon={<EditOutlined />} onClick={() => handleOpenEdit(record)} />
                                        )}
                                        {hasPermission(HomeworkPermission.DELETE) && (
                                            <Popconfirm
                                                title="Xóa bài tập?"
                                                onConfirm={() => handleDelete(record.id)}
                                                okText="Xóa"
                                                cancelText="Hủy"
                                            >
                                                <Button size="small" danger icon={<DeleteOutlined />} />
                                            </Popconfirm>
                                        )}
                                    </Space>
                                )}
                            </div>
                        </Card>
                    </List.Item>
                )}
            />
        </div>
    );
};
