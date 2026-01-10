import React, { useEffect, useState } from 'react';
import {
    Table, Button, Modal, Form, Input, DatePicker, Tag, Tabs, Space,
    message, Drawer, Select, Typography, Card, Statistic
} from 'antd';
import {
    PlusOutlined, UploadOutlined, EyeOutlined, LinkOutlined, EditOutlined, DeleteOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { useAuth } from '@/context/AuthContext';
import { homeworkService } from '@/services/api/homework.service';
import { userService } from '@/services/api/user.service';
import type { Homework, HomeworkSubmission } from '@/types/homework.types';
import type { UserResponse } from '@/types/user.types';
import { HomeworkStatus } from '@/types/homework.types';
import { HomeworkPermission } from '@/types/rbac.types';
import type { ColumnsType } from 'antd/es/table';

const { TextArea } = Input;
const { Option } = Select;
const { Title, Text } = Typography;

export const HomeworkPage: React.FC = () => {
    const { hasPermission } = useAuth();
    const [activeTab, setActiveTab] = useState('1');
    const [loading, setLoading] = useState(false);

    // Data States
    const [homeworks, setHomeworks] = useState<Homework[]>([]);
    const [myHomeworks, setMyHomeworks] = useState<Homework[]>([]);
    const [submissions, setSubmissions] = useState<HomeworkSubmission[]>([]);
    const [users, setUsers] = useState<UserResponse[]>([]);

    // Modal States
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);
    const [isSubmissionsDrawerOpen, setIsSubmissionsDrawerOpen] = useState(false);

    // Selected Items
    const [selectedHomework, setSelectedHomework] = useState<Homework | null>(null);
    const [mySubmission, setMySubmission] = useState<HomeworkSubmission | null>(null);

    const [form] = Form.useForm();
    const [submitForm] = Form.useForm();

    const fetchUsers = async () => {
        try {
            const res = await userService.getUsers();
            if (res && res.data) {
                setUsers(res.data);
            }
        } catch (error) {
            console.error(error);
        }
    }

    const fetchMyHomeworks = async () => {
        setLoading(true);
        try {
            const data = await homeworkService.getMyHomeworks();
            setMyHomeworks(data || []);
        } catch (error) {
            message.error('Không thể tải bài tập của bạn');
        } finally {
            setLoading(false);
        }
    };

    const fetchAllHomeworks = async () => {
        setLoading(true);
        try {
            const data = await homeworkService.getAll();
            setHomeworks(data || []);
        } catch (error) {
            message.error('Không thể tải danh sách bài tập');
        } finally {
            setLoading(false);
        }
    };

    const fetchSubmissions = async (homeworkId: number) => {
        try {
            const data = await homeworkService.getSubmissions(homeworkId);
            setSubmissions(data || []);
        } catch (error) {
            message.error('Không thể tải danh sách nộp bài');
        }
    };

    useEffect(() => {
        if (activeTab === '1') {
            fetchMyHomeworks();
        } else if (activeTab === '2') {
            fetchAllHomeworks();
        }
    }, [activeTab]);

    useEffect(() => {
        if (hasPermission(HomeworkPermission.CREATE) && users.length === 0) {
            fetchUsers();
        }
    }, [hasPermission]);

    // Handle Create Homework
    const handleCreateHomework = async (values: any) => {
        try {
            await homeworkService.create({
                title: values.title,
                description: values.description,
                deadline: values.deadline.toISOString(),
                assignee_ids: values.assignee_ids,
            });
            message.success('Tạo bài tập thành công');
            setIsCreateModalOpen(false);
            form.resetFields();
            if (activeTab === '2') fetchAllHomeworks();
            else setActiveTab('2');
        } catch (error: any) {
            message.error(error.message || 'Tạo bài tập thất bại');
        }
    };

    // Handle Open Submit Modal
    const handleOpenSubmit = async (homework: Homework) => {
        setSelectedHomework(homework);
        setIsSubmitModalOpen(true);
        submitForm.resetFields();
        setMySubmission(null);

        // Fetch current submission if exists
        try {
            const submission = await homeworkService.getMySubmission(homework.id);
            if (submission) {
                setMySubmission(submission);
                submitForm.setFieldsValue({ link: submission.link });
            }
        } catch (error) {
            // Ignore 404
        }
    };

    // Handle Submit
    const handleSubmit = async (values: any) => {
        if (!selectedHomework) return;
        try {
            await homeworkService.submit(selectedHomework.id, {
                link: values.link
            });
            message.success('Nộp bài thành công');
            setIsSubmitModalOpen(false);
            // Refresh logic if needed
            fetchMyHomeworks();
        } catch (error: any) {
            message.error(error.message || 'Nộp bài thất bại');
        }
    };

    // Handle View Submissions (Admin/Leader)
    const handleViewSubmissions = (homework: Homework) => {
        setSelectedHomework(homework);
        fetchSubmissions(homework.id);
        setIsSubmissionsDrawerOpen(true);
    };

    // Handle Update Status
    const handleUpdateStatus = async (submissionId: number, status: HomeworkStatus) => {
        try {
            await homeworkService.updateStatus(submissionId, status);
            message.success('Cập nhật trạng thái thành công');
            // Update local state
            setSubmissions(prev => prev.map(s => s.id === submissionId ? { ...s, status } : s));
        } catch (error: any) {
            message.error(error.message || 'Cập nhật trạng thái thất bại');
        }
    };

    // Render Status Tag
    const renderStatusTag = (status: HomeworkStatus, isLate: boolean) => {
        let color = 'default';
        if (isLate) color = 'error';
        else if (status === HomeworkStatus.SUBMITTED) color = 'processing';
        else if (status === HomeworkStatus.LeaderChecked) color = 'warning';
        else if (status === HomeworkStatus.FINISHED) color = 'success';

        return (
            <Space>
                <Tag color={color}>{status}</Tag>
                {isLate && <Tag color="red">Nộp trễ</Tag>}
            </Space>
        );
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
            render: (date: string) => <Text type="secondary">{dayjs(date).format('DD/MM/YYYY HH:mm')}</Text>,
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
            title: 'Hạn nộp',
            dataIndex: 'deadline',
            key: 'deadline',
            width: 150,
            render: (date: string) => dayjs(date).format('DD/MM/YYYY HH:mm'),
        },
        {
            title: 'Thống kê',
            key: 'stats',
            render: () => (
                <Space size="small" direction="vertical" style={{ fontSize: '12px' }}>
                    <Text type="secondary">Quản lý chung</Text>
                </Space>
            )
        },
        {
            title: 'Action',
            key: 'action',
            render: (_: any, record: Homework) => (
                <Space>
                    <Button icon={<EyeOutlined />} onClick={() => handleViewSubmissions(record)}>
                        Bài nộp
                    </Button>
                    {/* Placeholder for future features */}
                    <Button icon={<EditOutlined />} disabled />
                    <Button icon={<DeleteOutlined />} disabled />
                </Space>
            ),
        },
    ];

    const submissionColumns: ColumnsType<HomeworkSubmission> = [
        {
            title: 'Học viên',
            key: 'user',
            render: (record: HomeworkSubmission) => <Text strong>{record.user_name || `Member #${record.created_by || record.user_id}`}</Text>
        },
        {
            title: 'Link',
            dataIndex: 'link',
            key: 'link',
            render: (link: string) => {
                let isValid = false;
                try {
                    new URL(link);
                    isValid = true;
                } catch {
                    isValid = false;
                }

                if (!isValid) {
                    return <Text type="secondary" italic>Link không hợp lệ</Text>;
                }
                return <a href={link} target="_blank" rel="noopener noreferrer"><LinkOutlined /> Mở link</a>;
            }
        },
        {
            title: 'Ngày nộp',
            dataIndex: 'updated_at',
            key: 'updated_at',
            render: (date: string) => dayjs(date).format('DD/MM HH:mm'),
        },
        {
            title: 'Trạng thái',
            key: 'status',
            render: (_: any, record: HomeworkSubmission) => renderStatusTag(record.status, record.is_late),
        },
        {
            title: 'Action',
            key: 'action',
            render: (_: any, record: HomeworkSubmission) => (
                <Select
                    defaultValue={record.status}
                    style={{ width: 160 }}
                    onChange={(val) => handleUpdateStatus(record.id, val)}
                    size="small"
                >
                    <Option value={HomeworkStatus.SUBMITTED}>Đã nộp</Option>
                    <Option value={HomeworkStatus.LeaderChecked}>Leader Check</Option>
                    <Option value={HomeworkStatus.FINISHED}>Finish</Option>
                </Select>
            )
        }
    ];

    return (
        <div className="bg-white p-6 rounded-lg shadow-sm">
            <div className="flex justify-between items-center mb-6">
                <Title level={3} className="!mb-0">Quản lý bài tập</Title>
                {hasPermission(HomeworkPermission.CREATE) && (
                    <Button
                        type="primary"
                        icon={<PlusOutlined />}
                        onClick={() => setIsCreateModalOpen(true)}
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
                        loading={loading}
                        locale={{ emptyText: "Không có bài tập nào được giao" }}
                    />
                </Tabs.TabPane>

                {(hasPermission(HomeworkPermission.CREATE) || hasPermission(HomeworkPermission.READ)) && (
                    <Tabs.TabPane tab="Tất cả bài tập (Quản lý)" key="2">
                        <Table
                            dataSource={homeworks}
                            columns={adminColumns}
                            rowKey="id"
                            loading={loading}
                        />
                    </Tabs.TabPane>
                )}
            </Tabs>

            {/* Create Modal */}
            <Modal
                title="Tạo bài tập mới"
                open={isCreateModalOpen}
                onCancel={() => setIsCreateModalOpen(false)}
                onOk={form.submit}
            >
                <Form form={form} layout="vertical" onFinish={handleCreateHomework}>
                    <Form.Item name="title" label="Tiêu đề" rules={[{ required: true }]}>
                        <Input />
                    </Form.Item>
                    <Form.Item name="deadline" label="Hạn nộp" rules={[{ required: true }]}>
                        <DatePicker showTime className="w-full" />
                    </Form.Item>
                    <Form.Item name="assignee_ids" label="Giao cho (Để trống nếu giao cho tất cả)">
                        <Select
                            mode="multiple"
                            placeholder="Chọn thành viên..."
                            allowClear
                            filterOption={(input: string, option: any) =>
                                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                            }
                            options={users.map(u => ({ label: `${u.name} (${u.email})`, value: u.id }))}
                        />
                    </Form.Item>
                    <Form.Item name="description" label="Mô tả / Đề bài">
                        <TextArea rows={4} placeholder="Markdown supported..." />
                    </Form.Item>
                </Form>
            </Modal>

            {/* Submit Modal */}
            <Modal
                title={`Nộp bài: ${selectedHomework?.title}`}
                open={isSubmitModalOpen}
                onCancel={() => setIsSubmitModalOpen(false)}
                onOk={submitForm.submit}
                okText="Nộp bài"
            >
                {selectedHomework && (
                    <div className="mb-4">
                        <div className="bg-gray-50 p-3 rounded mb-4">
                            <Text strong>Đề bài:</Text>
                            <div className="whitespace-pre-wrap mt-1 text-gray-700">
                                {selectedHomework.description}
                            </div>
                            <div className="mt-2 text-xs text-red-500">
                                Deadline: {dayjs(selectedHomework.deadline).format('DD/MM/YYYY HH:mm')}
                            </div>
                        </div>

                        {mySubmission && (
                            <Card size="small" className="mb-4 border-blue-200 bg-blue-50">
                                <Statistic
                                    title="Trạng thái hiện tại"
                                    value={mySubmission.status}
                                    valueStyle={{ fontSize: 16, color: '#1890ff' }}
                                />
                                <Text type="secondary" style={{ fontSize: 12 }}>
                                    Cập nhật lần cuối: {dayjs(mySubmission.updated_at).format('DD/MM HH:mm')}
                                </Text>
                            </Card>
                        )}
                    </div>
                )}

                <Form form={submitForm} layout="vertical" onFinish={handleSubmit}>
                    <Form.Item
                        name="link"
                        label="Link bài làm (Github, Drive...)"
                        rules={[
                            { required: true, message: 'Vui lòng nhập link bài làm' },
                            { type: 'url', message: 'Link không hợp lệ! Vui lòng nhập đúng định dạng URL (vd: https://...)' }
                        ]}
                    >
                        <Input prefix={<LinkOutlined />} placeholder="https://..." />
                    </Form.Item>
                </Form>
            </Modal>

            {/* Submissions Drawer */}
            <Drawer
                title={`Danh sách bài nộp: ${selectedHomework?.title}`}
                size={720}
                open={isSubmissionsDrawerOpen}
                onClose={() => setIsSubmissionsDrawerOpen(false)}
            >
                <Table
                    dataSource={submissions}
                    columns={submissionColumns}
                    rowKey="id"
                />
            </Drawer>
        </div>
    );
};

export default HomeworkPage;
