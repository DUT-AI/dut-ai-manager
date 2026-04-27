import { useState } from 'react';
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
    Tooltip,
    Avatar,
    Grid,
    List
} from 'antd';
import {
    PlusOutlined,
    EditOutlined,
    DeleteOutlined,
    TeamOutlined,
    UserOutlined
} from '@ant-design/icons';
import { useTeams, useCreateTeam, useUpdateTeam, useDeleteTeam, useUsers } from '@/hooks';
import { useAuth } from '@/context/AuthContext';
import type { TeamResponse, TeamCreate } from '@/types/team.types';
import dayjs from 'dayjs';
import { motion, type Variants } from 'motion/react';

const { Title, Text } = Typography;
const { Option } = Select;

const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.1
        }
    }
};

const itemVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
        opacity: 1,
        y: 0,
        transition: { duration: 0.4, ease: "easeOut" }
    }
};

interface MobileListViewProps {
    teams: TeamResponse[];
    isLoading: boolean;
    onEdit: (item: TeamResponse) => void;
    onDelete: (id: number) => void;
}

const MobileListView = ({ teams, isLoading, onEdit, onDelete }: MobileListViewProps) => (
    <div className="mt-4 px-3">
        <List
            dataSource={teams}
            loading={isLoading}
            split={false}
            renderItem={(record) => (
                <List.Item className="px-2 !mb-4 !border-0">
                    <Card
                        className="w-full shadow-sm border-gray-100 overflow-hidden"
                        styles={{ body: { padding: '16px' } }}
                        actions={[
                            <Button
                                key="edit"
                                type="text"
                                icon={<EditOutlined />}
                                onClick={() => onEdit(record)}
                            >
                                Sửa
                            </Button>,
                            <Popconfirm
                                key="delete"
                                title="Xóa nhóm này?"
                                description="Hành động này không thể hoàn tác"
                                onConfirm={() => onDelete(record.id)}
                                okText="Xóa"
                                cancelText="Hủy"
                            >
                                <Button type="text" danger icon={<DeleteOutlined />}>Xóa</Button>
                            </Popconfirm>
                        ]}
                    >
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-500 shrink-0">
                                <TeamOutlined className="text-xl" />
                            </div>
                            <div className="flex flex-col min-w-0 flex-1">
                                <Text strong className="text-base truncate">{record.team_name}</Text>
                                <Text type="secondary" className="text-xs">{record.member_count} thành viên</Text>
                            </div>
                        </div>

                        <div>
                            <Text type="secondary" className="block mb-2 text-xs uppercase font-bold tracking-wider">Thành viên</Text>
                            <Avatar.Group max={{ count: 6, style: { color: '#f56a00', backgroundColor: '#fde3cf' } }}>
                                {record.members.map(m => (
                                    <Tooltip title={m.user_name} key={m.user_id}>
                                        <Avatar src={m.user_avatar} icon={<UserOutlined />} />
                                    </Tooltip>
                                ))}
                            </Avatar.Group>
                        </div>

                        <div className="mt-4 pt-3 border-t border-gray-50 flex justify-between items-center text-gray-400 text-[10px]">
                            <span>Ngày tạo: {dayjs(record.created_at).format('DD/MM/YYYY')}</span>
                        </div>
                    </Card>
                </List.Item>
            )}
        />
    </div>
);

const TeamManagementPage = () => {
    useAuth();
    const screens = Grid.useBreakpoint();
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingItem, setEditingItem] = useState<TeamResponse | null>(null);
    const [form] = Form.useForm();

    // TanStack Query hooks
    const { data, isLoading } = useTeams();
    const teams = data || [];
    const { data: users = [] } = useUsers();
    const createTeam = useCreateTeam();
    const updateTeam = useUpdateTeam();
    const deleteTeam = useDeleteTeam();

    const handleCreateOrUpdate = async (values: any) => {
        try {
            const payload: TeamCreate = {
                team_name: values.team_name,
                member_ids: values.member_ids
            };

            if (editingItem) {
                await updateTeam.mutateAsync({ id: editingItem.id, data: payload });
                message.success('Cập nhật nhóm thành công');
            } else {
                await createTeam.mutateAsync(payload);
                message.success('Tạo nhóm mới thành công');
            }
            setIsModalOpen(false);
            form.resetFields();
        } catch (error: any) {
            message.error(error?.response?.data?.message || 'Thao tác thất bại');
        }
    };

    const handleDelete = async (id: number) => {
        try {
            await deleteTeam.mutateAsync(id);
            message.success('Xóa nhóm thành công');
        } catch (error: any) {
            message.error(error?.response?.data?.message || 'Xóa thất bại');
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
                    <Avatar.Group max={{ count: 5, style: { color: '#f56a00', backgroundColor: '#fde3cf' } }} size="small">
                        {record.members.map(m => (
                            <Tooltip title={m.user_name} key={m.user_id}>
                                <Avatar src={m.user_avatar} icon={<UserOutlined />} />
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
        <motion.div 
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="p-4 md:p-6"
        >
            <Card className={!screens.md ? "bg-transparent shadow-none border-none" : "shadow-sm border-gray-100 rounded-xl overflow-hidden"} styles={{ body: { padding: !screens.md ? 0 : undefined } }}>
                <motion.div variants={itemVariants} className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6 px-3 md:px-0">
                    <Space size="middle">
                        <div className="hidden md:flex w-12 h-12 rounded-xl bg-indigo-50 items-center justify-center text-indigo-500">
                            <TeamOutlined className="text-2xl" />
                        </div>
                        <div>
                            <Title level={3} className="text-xl md:text-2xl mt-4 text-indigo-600">Quản lý Nhóm</Title>
                            <Text type="secondary" className="text-xs md:text-sm">Tổ chức thành viên vào các nhóm chức năng</Text>
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
                        className="w-full md:w-auto bg-linear-to-r from-indigo-500 to-purple-600 border-none shadow-md h-10 px-6 font-semibold"
                    >
                        Tạo Nhóm mới
                    </Button>
                </motion.div>

                {!screens.md ? (
                    <motion.div variants={itemVariants}>
                        <MobileListView
                            teams={teams}
                            isLoading={isLoading}
                            onEdit={(item) => {
                                setEditingItem(item);
                                form.setFieldsValue({
                                    team_name: item.team_name,
                                    member_ids: item.members.map(m => m.user_id)
                                });
                                setIsModalOpen(true);
                            }}
                            onDelete={handleDelete}
                        />
                    </motion.div>
                ) : (
                    <motion.div variants={itemVariants}>
                        <Table
                            columns={columns}
                            dataSource={teams}
                            rowKey="id"
                            loading={isLoading}
                            className="custom-table"
                        />
                    </motion.div>
                )}
            </Card>

            <Modal
                title={editingItem ? 'Chỉnh sửa Nhóm' : 'Tạo Nhóm mới'}
                open={isModalOpen}
                onCancel={() => setIsModalOpen(false)}
                onOk={() => form.submit()}
                centered
                confirmLoading={createTeam.isPending || updateTeam.isPending}
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
                            placeholder="Chọn thành viên"
                            optionFilterProp="children"
                        >
                            {users.map(u => (
                                <Option key={u.id} value={u.id}>{u.name} ({u.email})</Option>
                            ))}
                        </Select>
                    </Form.Item>
                </Form>
            </Modal>
        </motion.div>
    );
};

export default TeamManagementPage;
