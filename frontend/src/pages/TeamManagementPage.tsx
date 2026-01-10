import { useState, useEffect } from 'react';
import {
    Table,
    Button,
    Card,
    Space,
    Modal,
    Form,
    Input,
    message,
    Popconfirm,
    Typography,
    Select,
    Tag,
    Tooltip,
    Avatar
} from 'antd';
import {
    PlusOutlined,
    EditOutlined,
    DeleteOutlined,
    TeamOutlined,
    UserOutlined,
    SearchOutlined,
    DeleteFilled
} from '@ant-design/icons';
import { teamService } from '@/services/api/team.service';
import { userService } from '@/services/api/user.service';
import { useAuth } from '@/context/AuthContext';
import type { TeamResponse, TeamCreate, TeamUpdate } from '@/types/team.types';
import type { UserResponse } from '@/types/user.types';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;

const TeamManagementPage = () => {
    const { hasPermission } = useAuth();
    const [teams, setTeams] = useState<TeamResponse[]>([]);
    const [users, setUsers] = useState<UserResponse[]>([]);
    const [loading, setLoading] = useState(false);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingItem, setEditingItem] = useState<TeamResponse | null>(null);
    const [form] = Form.useForm();

    const fetchData = async () => {
        setLoading(true);
        try {
            const [teamRes, userRes] = await Promise.all([
                teamService.getTeams(),
                userService.getUsers()
            ]);
            if (teamRes.is_success) setTeams(teamRes.data || []);
            if (userRes.is_success) setUsers(userRes.data || []);
        } catch (error) {
            message.error('Không thể tải dữ liệu');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleCreateOrUpdate = async (values: any) => {
        try {
            const payload: TeamCreate = {
                team_name: values.team_name,
                member_ids: values.member_ids
            };

            if (editingItem) {
                const res = await teamService.updateTeam(editingItem.id, payload);
                if (res.is_success) {
                    message.success('Cập nhật nhóm thành công');
                } else {
                    message.error(res.message);
                }
            } else {
                const res = await teamService.createTeam(payload);
                if (res.is_success) {
                    message.success('Tạo nhóm mới thành công');
                } else {
                    message.error(res.message);
                }
            }
            setIsModalOpen(false);
            form.resetFields();
            fetchData();
        } catch (error) {
            message.error('Thao tác thất bại');
        }
    };

    const handleDelete = async (id: number) => {
        try {
            const res = await teamService.deleteTeam(id);
            if (res.is_success) {
                message.success('Xóa nhóm thành công');
                fetchData();
            } else {
                message.error(res.message);
            }
        } catch (error) {
            message.error('Xóa thất bại');
        }
    };

    const columns = [
        {
            title: 'Tên nhóm',
            dataIndex: 'team_name',
            key: 'team_name',
            render: (text: string) => (
                <Space>
                    <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-500">
                        <TeamOutlined />
                    </div>
                    <Text strong>{text}</Text>
                </Space>
            )
        },
        {
            title: 'Thành viên',
            key: 'members',
            render: (_: any, record: TeamResponse) => (
                <Space direction="vertical" size={4} className="max-w-[300px]">
                    <Avatar.Group maxCount={5} size="small" maxStyle={{ color: '#f56a00', backgroundColor: '#fde3cf' }}>
                        {record.members.map(m => (
                            <Tooltip title={m.user_name} key={m.user_id}>
                                <Avatar style={{ backgroundColor: '#87d068' }} icon={<UserOutlined />} />
                            </Tooltip>
                        ))}
                    </Avatar.Group>
                    <Text type="secondary" className="text-xs">{record.member_count} thành viên</Text>
                </Space>
            )
        },
        {
            title: 'Ngày tạo',
            dataIndex: 'created_at',
            key: 'created_at',
            render: (date: string) => dayjs(date).format('DD/MM/YYYY HH:mm')
        },
        {
            title: 'Thao tác',
            key: 'actions',
            render: (_: any, record: TeamResponse) => (
                <Space>
                    <Button
                        icon={<EditOutlined />}
                        onClick={() => {
                            setEditingItem(record);
                            form.setFieldsValue({
                                team_name: record.team_name,
                                member_ids: record.members.map(m => m.user_id)
                            });
                            setIsModalOpen(true);
                        }}
                    />
                    <Popconfirm
                        title="Xóa nhóm này?"
                        description="Hành động này không thể hoàn tác"
                        onConfirm={() => handleDelete(record.id)}
                        okText="Xóa"
                        cancelText="Hủy"
                    >
                        <Button icon={<DeleteOutlined />} danger />
                    </Popconfirm>
                </Space>
            )
        }
    ];

    return (
        <div className="p-6">
            <Card className="shadow-sm border-gray-100 rounded-xl overflow-hidden">
                <div className="flex justify-between items-center mb-6">
                    <Space size="middle">
                        <div className="w-12 h-12 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-500">
                            <TeamOutlined className="text-2xl" />
                        </div>
                        <div>
                            <Title level={3} className="!m-0">Quản lý Nhóm</Title>
                            <Text type="secondary">Tổ chức thành viên vào các nhóm chức năng</Text>
                        </div>
                    </Space>
                    <Button
                        type="primary"
                        icon={<PlusOutlined />}
                        onClick={() => {
                            setEditingItem(null);
                            form.resetFields();
                            setIsModalOpen(true);
                        }}
                        className="bg-linear-to-r from-indigo-500 to-purple-600 border-none shadow-md h-10 px-6 font-semibold"
                    >
                        Tạo Nhóm mới
                    </Button>
                </div>

                <Table
                    columns={columns}
                    dataSource={teams}
                    rowKey="id"
                    loading={loading}
                    className="custom-table"
                />
            </Card>

            <Modal
                title={editingItem ? 'Chỉnh sửa Nhóm' : 'Tạo Nhóm mới'}
                open={isModalOpen}
                onCancel={() => setIsModalOpen(false)}
                onOk={() => form.submit()}
                centered
                destroyOnHidden
            >
                <Form form={form} layout="vertical" onFinish={handleCreateOrUpdate} className="mt-4">
                    <Form.Item
                        name="team_name"
                        label="Tên nhóm"
                        rules={[{ required: true, message: 'Vui lòng nhập tên nhóm' }]}
                    >
                        <Input placeholder="Ví dụ: Đội AI, Đội Backend..." />
                    </Form.Item>

                    <Form.Item
                        name="member_ids"
                        label="Thành viên"
                    >
                        <Select
                            mode="multiple"
                            allowClear
                            style={{ width: '100%' }}
                            placeholder="Chọn thành viên thức"
                            optionFilterProp="children"
                        >
                            {users.map(u => (
                                <Option key={u.id} value={u.id}>{u.name} ({u.email})</Option>
                            ))}
                        </Select>
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    );
};

export default TeamManagementPage;
