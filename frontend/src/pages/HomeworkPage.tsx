import React, { useEffect, useState } from 'react';
import {
    Table, Button, Tabs, Space, message, Popconfirm, Typography, Tag
} from 'antd';
import {
    PlusOutlined, UploadOutlined, EyeOutlined, EditOutlined, DeleteOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { useAuth } from '@/context/AuthContext';
import {
    useHomeworks,
    useMyHomeworks,
    useDeleteHomework,
    useSubmissions,
    useUsers,
    useTeams
} from '@/hooks';
import { homeworkService } from '@/services/api/homework.service';
import type { Homework } from '@/types/homework.types';
import { HomeworkPermission } from '@/types/rbac.types';
import type { ColumnsType } from 'antd/es/table';
import { HomeworkFormModal, SubmitHomeworkModal, SubmissionsDrawer } from '@/components/homework';

const { Title, Text } = Typography;

export const HomeworkPage: React.FC = () => {
    const { hasPermission, isAdminOrLeader } = useAuth();
    const [activeTab, setActiveTab] = useState('1');

    // TanStack Query hooks
    const { data: myHomeworks = [], isLoading: myLoading, refetch: refetchMyHomeworks } = useMyHomeworks();
    const { data: allHomeworks = [], isLoading: allLoading, refetch: refetchAllHomeworks } = useHomeworks();
    const { data: users = [] } = useUsers();
    const { data: teams = [] } = useTeams();
    const deleteHomework = useDeleteHomework();

    // Modal States
    const [isFormModalOpen, setIsFormModalOpen] = useState(false);
    const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);
    const [isSubmissionsDrawerOpen, setIsSubmissionsDrawerOpen] = useState(false);

    // Selected Items
    const [selectedHomework, setSelectedHomework] = useState<Homework | null>(null);
    const [editingHomework, setEditingHomework] = useState<Homework | null>(null);
    const [currentAssignees, setCurrentAssignees] = useState<number[]>([]);

    const loading = activeTab === '1' ? myLoading : allLoading;
    const homeworks = activeTab === '1' ? myHomeworks : allHomeworks;

    const refreshData = () => {
        if (activeTab === '1') {
            refetchMyHomeworks();
        } else {
            refetchAllHomeworks();
        }
    };

    // Open Create Modal
    const handleOpenCreate = () => {
        setEditingHomework(null);
        setIsFormModalOpen(true);
    };

    // Open Edit Modal
    const handleOpenEdit = async (homework: Homework) => {
        setEditingHomework(homework);
        // Fetch current assignees from submissions
        try {
            const submissions = await homeworkService.getSubmissions(homework.id);
            setCurrentAssignees(submissions?.map((s: any) => s.owner_id) || []);
        } catch {
            setCurrentAssignees([]);
        }
        setIsFormModalOpen(true);
    };

    // Delete Homework
    const handleDelete = async (id: number) => {
        try {
            await deleteHomework.mutateAsync(id);
            message.success('Xóa bài tập thành công');
        } catch (error: any) {
            message.error(error?.response?.data?.message || 'Xóa bài tập thất bại');
        }
    };

    // Open Submit Modal
    const handleOpenSubmit = (homework: Homework) => {
        setSelectedHomework(homework);
        setIsSubmitModalOpen(true);
    };

    // Open Submissions Drawer
    const handleViewSubmissions = (homework: Homework) => {
        setSelectedHomework(homework);
        setIsSubmissionsDrawerOpen(true);
    };

    // Form Modal Success
    const handleFormSuccess = () => {
        setIsFormModalOpen(false);
        setEditingHomework(null);
        refreshData();
    };

    // Submit Modal Success
    const handleSubmitSuccess = () => {
        setIsSubmitModalOpen(false);
        refetchMyHomeworks();
    };

    const myColumns: ColumnsType<Homework> = [
        {
            title: 'Tiêu đề',
            dataIndex: 'title',
            key: 'title',
            render: (text: string) => <Text strong>{text}</Text>,
        },
        {
            title: 'Mô tả',
            dataIndex: 'description',
            key: 'description',
            ellipsis: true,
        },
        {
            title: 'Hạn nộp',
            dataIndex: 'deadline',
            key: 'deadline',
            render: (date: string) => {
                const isOverdue = dayjs().isAfter(dayjs(date));
                return (
                    <Text type={isOverdue ? 'danger' : 'secondary'}>
                        {dayjs(date).format('DD/MM/YYYY HH:mm')}
                        {isOverdue && <Tag color="red" className="ml-2">Quá hạn</Tag>}
                    </Text>
                );
            },
        },
        {
            title: 'Hành động',
            key: 'action',
            render: (_: any, record: Homework) => (
                <Button type="primary" icon={<UploadOutlined />} onClick={() => handleOpenSubmit(record)}>
                    Nộp bài / Xem
                </Button>
            ),
        }
    ];

    const adminColumns: ColumnsType<Homework> = [
        {
            title: 'Tiêu đề',
            dataIndex: 'title',
            key: 'title',
            width: 200,
        },
        {
            title: 'Mô tả',
            dataIndex: 'description',
            key: 'description',
            ellipsis: true,
            width: 250,
        },
        {
            title: 'Hạn nộp',
            dataIndex: 'deadline',
            key: 'deadline',
            width: 150,
            render: (date: string) => {
                const isOverdue = dayjs().isAfter(dayjs(date));
                return (
                    <Text type={isOverdue ? 'danger' : undefined}>
                        {dayjs(date).format('DD/MM/YYYY HH:mm')}
                    </Text>
                );
            },
        },
        {
            title: 'Action',
            key: 'action',
            width: 280,
            render: (_: any, record: Homework) => (
                <Space>
                    <Button icon={<EyeOutlined />} onClick={() => handleViewSubmissions(record)}>
                        Bài nộp
                    </Button>
                    {hasPermission(HomeworkPermission.UPDATE) && (
                        <Button icon={<EditOutlined />} onClick={() => handleOpenEdit(record)} />
                    )}
                    {hasPermission(HomeworkPermission.DELETE) && (
                        <Popconfirm
                            title="Xóa bài tập này?"
                            description="Hành động này không thể hoàn tác"
                            onConfirm={() => handleDelete(record.id)}
                            okText="Xóa"
                            cancelText="Hủy"
                            okButtonProps={{ danger: true }}
                        >
                            <Button danger icon={<DeleteOutlined />} />
                        </Popconfirm>
                    )}
                </Space>
            ),
        },
    ];

    return (
        <div className="bg-white p-6 rounded-lg shadow-sm">
            <div className="flex justify-between items-center mb-6">
                <Title level={3} className="!mb-0">Quản lý bài tập</Title>
                {hasPermission(HomeworkPermission.CREATE) && (
                    <Button
                        type="primary"
                        icon={<PlusOutlined />}
                        onClick={handleOpenCreate}
                        className="bg-indigo-600 hover:bg-indigo-700"
                    >
                        Tạo bài tập mới
                    </Button>
                )}
            </div>

            <Tabs activeKey={activeTab} onChange={setActiveTab} type="card">
                <Tabs.TabPane tab="Bài tập của tôi" key="1">
                    <Table
                        dataSource={myHomeworks}
                        columns={myColumns}
                        rowKey="id"
                        loading={myLoading}
                        locale={{ emptyText: "Không có bài tập nào được giao" }}
                    />
                </Tabs.TabPane>

                {isAdminOrLeader() && (
                    <Tabs.TabPane tab="Tất cả bài tập (Quản lý)" key="2">
                        <Table
                            dataSource={allHomeworks}
                            columns={adminColumns}
                            rowKey="id"
                            loading={allLoading}
                        />
                    </Tabs.TabPane>
                )}
            </Tabs>

            {/* Create/Edit Modal */}
            <HomeworkFormModal
                open={isFormModalOpen}
                editingItem={editingHomework}
                users={users}
                teams={teams}
                currentAssignees={currentAssignees}
                onSuccess={handleFormSuccess}
                onCancel={() => setIsFormModalOpen(false)}
            />

            {/* Submit Modal */}
            <SubmitHomeworkModal
                open={isSubmitModalOpen}
                homework={selectedHomework}
                onSuccess={handleSubmitSuccess}
                onCancel={() => setIsSubmitModalOpen(false)}
            />

            {/* Submissions Drawer */}
            <SubmissionsDrawer
                open={isSubmissionsDrawerOpen}
                homework={selectedHomework}
                onClose={() => setIsSubmissionsDrawerOpen(false)}
            />
        </div>
    );
};

export default HomeworkPage;
