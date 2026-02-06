import React, { useState } from 'react';
import {
    Table, Button, Tabs, Space, message, Popconfirm, Typography, Tag, Grid, List, Card
} from 'antd';
import {
    PlusOutlined, UploadOutlined, EyeOutlined, EditOutlined, DeleteOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { useAuth } from '@/context/AuthContext';
import {
    useMyHomeworks,
    useDeleteHomework,
    useUsers,
    useTeams,
    useHomeworks
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
    const { data: myData, isLoading: myLoading, refetch: refetchMyHomeworks } = useMyHomeworks();
    const { data: allData, isLoading: allLoading, refetch: refetchAllHomeworks } = useHomeworks();
    const { data: usersData = [] } = useUsers();
    const { data: teamsData = [] } = useTeams();

    const myHomeworks = myData || [];
    const allHomeworks = allData || [];
    const users = usersData || [];
    const teams = teamsData || [];

    const deleteHomework = useDeleteHomework();

    // Modal States
    const [isFormModalOpen, setIsFormModalOpen] = useState(false);
    const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);
    const [isSubmissionsDrawerOpen, setIsSubmissionsDrawerOpen] = useState(false);

    // Selected Items
    const [selectedHomework, setSelectedHomework] = useState<Homework | null>(null);
    const [editingHomework, setEditingHomework] = useState<Homework | null>(null);
    const [currentAssignees, setCurrentAssignees] = useState<number[]>([]);

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
        setCurrentAssignees([]);
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

    const screens = Grid.useBreakpoint();

    const HomeworkMobileList = ({ dataSource, loading, emptyText }: { dataSource: Homework[], loading: boolean, emptyText?: string }) => (
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
                                <Text strong className="text-base truncate">{record.title}</Text>
                                {dayjs().isAfter(dayjs(record.deadline)) && (
                                    <Tag color="red" className="m-0">Quá hạn</Tag>
                                )}
                            </div>

                            <div className="mb-4">
                                <Text type="secondary" className="block text-xs truncate">
                                    {record.description || 'Không có mô tả'}
                                </Text>
                            </div>

                            <div className="flex items-center gap-2 mb-4 text-xs">
                                <Text type="secondary">Hạn nộp:</Text>
                                <Text className={dayjs().isAfter(dayjs(record.deadline)) ? 'text-red-500' : ''}>
                                    {dayjs(record.deadline).format('DD/MM/YYYY HH:mm')}
                                </Text>
                            </div>

                            <div className="flex justify-end gap-2 pt-3 border-t border-gray-50 bg-gray-50 -mx-4 -mb-4 px-4 py-3">
                                {activeTab === '1' ? (
                                    <Button type="primary" size="small" icon={<UploadOutlined />} onClick={() => handleOpenSubmit(record)}>
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

    return (
        <div className="p-4 md:p-6 bg-white md:rounded-xl shadow-xs min-h-full">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4 px-3 md:px-0">
                <div>
                    <Title level={3} className="!m-0 text-xl md:text-2xl text-[#4f46e5] mt-4">Quản lý bài tập</Title>
                    <Text type="secondary" className="text-xs md:text-sm">Giao và nộp bài tập, theo dõi tiến độ</Text>
                </div>
                {hasPermission(HomeworkPermission.CREATE) && (
                    <Button
                        type="primary"
                        icon={<PlusOutlined />}
                        onClick={handleOpenCreate}
                        className="w-full md:w-auto bg-indigo-600 hover:bg-indigo-700 h-10 font-semibold"
                    >
                        Tạo bài tập mới
                    </Button>
                )}
            </div>

            <div className="overflow-x-auto no-scrollbar">
                <Tabs
                    activeKey={activeTab}
                    onChange={setActiveTab}
                    type="card"
                    className="homework-tabs"
                    tabBarStyle={{
                        paddingLeft: !screens.md ? '16px' : '0',
                        paddingRight: !screens.md ? '16px' : '0',
                        marginBottom: 0,
                        minWidth: !screens.md ? 'max-content' : '100%'
                    }}
                    items={[
                        {
                            key: '1',
                            label: 'Bài tập của tôi',
                            children: !screens.md ? (
                                <HomeworkMobileList
                                    dataSource={myHomeworks}
                                    loading={myLoading}
                                    emptyText="Không có bài tập nào được giao"
                                />
                            ) : (
                                <Table
                                    dataSource={myHomeworks}
                                    columns={myColumns}
                                    rowKey="id"
                                    loading={myLoading}
                                    locale={{ emptyText: "Không có bài tập nào được giao" }}
                                />
                            )
                        },
                        ...(isAdminOrLeader() ? [{
                            key: '2',
                            label: 'Quản lý bài tập',
                            children: !screens.md ? (
                                <HomeworkMobileList
                                    dataSource={allHomeworks}
                                    loading={allLoading}
                                />
                            ) : (
                                <Table
                                    dataSource={allHomeworks}
                                    columns={adminColumns}
                                    rowKey="id"
                                    loading={allLoading}
                                />
                            )
                        }] : [])
                    ]}
                />

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
        </div>
    );
};

export default HomeworkPage;
