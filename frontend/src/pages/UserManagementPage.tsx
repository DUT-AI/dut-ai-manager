import { useState, useMemo, useReducer } from 'react';
import {
    Table,
    Button,
    Card,
    Tag,
    Space,
    Modal,
    Form,
    Input,
    message,
    Popconfirm,
    Typography,
    Select,
    Badge,
    Row,
    Col,
    Avatar,
    Upload,
    Alert,
    Grid,
    List
} from 'antd';
import {
    PlusOutlined,
    EditOutlined,
    DeleteOutlined,
    UserOutlined,
    LockOutlined,
    MailOutlined,
    PhoneOutlined,
    CheckCircleOutlined,
    StopOutlined,
    SearchOutlined,
    FilterOutlined,
    DiscordOutlined,
    PictureOutlined,
    UploadOutlined,
    FileExcelOutlined
} from '@ant-design/icons';
import { useUsers, useCreateUser, useUpdateUser, useDeleteUser, useRoles, useImportUsers } from '@/hooks';
import { useAuth } from '../context/AuthContext';
import { UserPermission } from '../types/rbac.types';
import type { UserResponse } from '../types/user.types';

import { useNavigate } from 'react-router-dom';

const { Title, Text } = Typography;
const { Option } = Select;

interface MobileListViewProps {
    filteredUsers: UserResponse[];
    isLoading: boolean;
    canUpdate: boolean;
    canDelete: boolean;
    onNavigate: (userId: number) => void;
    onEdit: (user: UserResponse) => void;
    onDelete: (id: number) => void;
}

const MobileListView = ({ filteredUsers, isLoading, canUpdate, canDelete, onNavigate, onEdit, onDelete }: MobileListViewProps) => (
    <div className="mt-4 px-3">
        <List
            dataSource={filteredUsers}
            loading={isLoading}
            split={false}
            renderItem={(record) => (
                <List.Item className="px-2 !mb-4 !border-0" onClick={() => onNavigate(record.id)}>
                    <Card
                        className="w-full shadow-sm border-gray-100 overflow-hidden"
                        styles={{ body: { padding: '16px' } }}
                    >
                        <div className="flex items-center justify-between mb-4">
                            <Tag color={record.role_name === 'admin' ? 'volcano' : record.role_name === 'leader' ? 'blue' : 'green'} className="uppercase font-bold m-0 px-3 rounded-full">
                                {record.role_name || 'NO ROLE'}
                            </Tag>
                            <Badge
                                status={record.status === 'active' ? 'success' : 'error'}
                                text={<span className={record.status === 'active' ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>{record.status?.toUpperCase()}</span>}
                            />
                        </div>

                        <div className="flex items-center gap-3 mb-4">
                            <Avatar
                                size={52}
                                src={record.avatar_url}
                                icon={<UserOutlined />}
                                className="bg-linear-to-br from-[#4f46e5] to-[#7c3aed] shrink-0 shadow-sm"
                            />
                            <div className="flex flex-col min-w-0 flex-1">
                                <Text strong className="truncate text-base">{record.name}</Text>
                                <div className="flex items-center gap-1.5 text-gray-400">
                                    <MailOutlined className="text-xs" />
                                    <Text type="secondary" className="text-xs truncate">{record.email}</Text>
                                </div>
                                {record.discord_id && (
                                    <div className="flex items-center gap-1.5 text-indigo-400">
                                        <DiscordOutlined className="text-xs" />
                                        <Text className="text-[10px] text-indigo-400">{record.discord_id}</Text>
                                    </div>
                                )}
                            </div>
                        </div>

                        <div role="presentation" className="flex justify-between items-center pt-3 border-t border-gray-50 bg-gray-50 -mx-4 -mb-4 px-4 py-3 gap-2" onClick={(e) => e.stopPropagation()} onKeyDown={(e) => e.stopPropagation()}>
                            <Space>
                                <PhoneOutlined className="text-gray-400" />
                                <Text className="text-xs">{record.phone_number || 'No phone'}</Text>
                            </Space>
                            <Space onClick={(e) => e.stopPropagation()}>
                                <Button
                                    icon={<EditOutlined />}
                                    size="small"
                                    onClick={() => onEdit(record)}
                                    disabled={!canUpdate}
                                >
                                    Sửa
                                </Button>
                                <Popconfirm
                                    title="Xóa thành viên này?"
                                    onConfirm={() => onDelete(record.id)}
                                    disabled={!canDelete}
                                    okText="Xóa"
                                    cancelText="Hủy"
                                >
                                    <Button icon={<DeleteOutlined />} size="small" danger disabled={!canDelete} />
                                </Popconfirm>
                            </Space>
                        </div>
                    </Card>
                </List.Item>
            )}
        />
    </div>
);

// --- Modal state management via useReducer ---
type ModalState = {
    isUserModalOpen: boolean;
    isImportModalOpen: boolean;
    editingUser: UserResponse | null;
};

type ModalAction =
    | { type: 'OPEN_USER_MODAL'; payload?: UserResponse }
    | { type: 'CLOSE_USER_MODAL' }
    | { type: 'OPEN_IMPORT_MODAL' }
    | { type: 'CLOSE_IMPORT_MODAL' };

const modalInitialState: ModalState = {
    isUserModalOpen: false,
    isImportModalOpen: false,
    editingUser: null,
};

function modalReducer(state: ModalState, action: ModalAction): ModalState {
    switch (action.type) {
        case 'OPEN_USER_MODAL':
            return { ...state, isUserModalOpen: true, editingUser: action.payload ?? null };
        case 'CLOSE_USER_MODAL':
            return { ...state, isUserModalOpen: false, editingUser: null };
        case 'OPEN_IMPORT_MODAL':
            return { ...state, isImportModalOpen: true };
        case 'CLOSE_IMPORT_MODAL':
            return { ...state, isImportModalOpen: false };
        default:
            return state;
    }
}

const UserManagementPage = () => {
    const navigate = useNavigate();
    const { hasPermission } = useAuth();
    const [modalState, dispatch] = useReducer(modalReducer, modalInitialState);
    const { isUserModalOpen, isImportModalOpen, editingUser } = modalState;
    const [form] = Form.useForm();
    const screens = Grid.useBreakpoint();

    // Search & Filter states
    const [searchText, setSearchText] = useState('');
    const [filterRole, setFilterRole] = useState<string | undefined>(undefined);
    const [filterStatus, setFilterStatus] = useState<string | undefined>(undefined);

    // TanStack Query hooks
    const { data: users = [], isLoading } = useUsers();
    const { data: roles = [] } = useRoles();
    const createUser = useCreateUser();
    const updateUser = useUpdateUser();
    const deleteUser = useDeleteUser();

    // Filtered users
    const filteredUsers = useMemo(() => {
        return users.filter(user => {
            // Search filter (name, email, phone)
            const matchSearch = searchText === '' ||
                user.name?.toLowerCase().includes(searchText.toLowerCase()) ||
                user.email?.toLowerCase().includes(searchText.toLowerCase()) ||
                user.phone_number?.toLowerCase().includes(searchText.toLowerCase());

            // Role filter
            const matchRole = !filterRole || user.role_name === filterRole;

            // Status filter
            const matchStatus = !filterStatus || user.status === filterStatus;

            return matchSearch && matchRole && matchStatus;
        });
    }, [users, searchText, filterRole, filterStatus]);

    const canCreate = hasPermission(UserPermission.CREATE);
    const canUpdate = hasPermission(UserPermission.UPDATE);
    const canDelete = hasPermission(UserPermission.DELETE);

    const handleCreateOrUpdate = async (values: any) => {
        try {
            if (editingUser) {
                await updateUser.mutateAsync({ id: editingUser.id, data: values });
                message.success('User updated successfully');
            } else {
                await createUser.mutateAsync(values);
                message.success('User created successfully');
            }
            dispatch({ type: 'CLOSE_USER_MODAL' });
            form.resetFields();
        } catch (error: any) {
            message.error(error?.response?.data?.message || 'Operation failed');
        }
    };

    const handleDelete = async (id: number) => {
        try {
            await deleteUser.mutateAsync(id);
            message.success('User deleted successfully');
        } catch (error) {
            message.error('Delete failed');
        }
    };

    const columns = [
        {
            title: 'Thành viên',
            key: 'user',
            fixed: 'left' as const,
            render: (_: any, record: UserResponse) => (
                <Space>
                    <Avatar
                        src={record.avatar_url}
                        icon={<UserOutlined />}
                        className="bg-linear-to-br from-[#4f46e5] to-[#7c3aed] flex items-center justify-center text-white shadow-sm"
                    />
                    <div>
                        <Text strong className="block">{record.name}</Text>
                        {record.discord_id && (
                            <Text type="secondary" className="text-[10px] flex items-center gap-1">
                                <DiscordOutlined className="text-indigo-400" />
                                {record.discord_id}
                            </Text>
                        )}
                    </div>
                </Space>
            ),
        },
        {
            title: 'Liên hệ',
            key: 'contact',
            render: (_: any, record: UserResponse) => (
                <div className="flex flex-col gap-0.5">
                    <div className="flex items-center text-xs">
                        <MailOutlined className="mr-2 text-gray-400 text-[10px]" />
                        <Text className="text-xs">{record.email}</Text>
                    </div>
                    <div className="flex items-center text-xs">
                        <PhoneOutlined className="mr-2 text-gray-400 text-[10px]" />
                        <Text className="text-xs">{record.phone_number || 'N/A'}</Text>
                    </div>
                </div>
            ),
        },
        {
            title: 'Vai trò',
            dataIndex: 'role_name',
            key: 'role',
            render: (role: string) => (
                <Tag color={role === 'admin' ? 'volcano' : role === 'leader' ? 'blue' : 'green'} className="uppercase font-bold min-w-[80px] text-center">
                    {role || 'NO ROLE'}
                </Tag>
            ),
        },
        {
            title: 'Trạng thái',
            dataIndex: 'status',
            key: 'status',
            render: (status: string) => (
                <Badge
                    status={status === 'active' ? 'success' : 'error'}
                    text={status === 'active' ? <Tag color="success">ACTIVE</Tag> : <Tag color="error">INACTIVE</Tag>}
                />
            ),
        },
        {
            title: 'Thao tác',
            key: 'actions',
            fixed: 'right' as const,
            width: 150,
            render: (_: any, record: UserResponse) => (
                <Space>
                    <Button
                        icon={<UserOutlined />}
                        onClick={() => navigate(`/dashboard/profile/${record.id}`)}
                        className="hover:text-indigo-500 hover:border-indigo-500"
                        title="Xem hồ sơ"
                    />
                    <Button
                        icon={<EditOutlined />}
                        onClick={() => {
                            form.setFieldsValue(record);
                            dispatch({ type: 'OPEN_USER_MODAL', payload: record });
                        }}
                        disabled={!canUpdate}
                        className="hover:text-blue-500 hover:border-blue-500"
                        title="Chỉnh sửa"
                    />
                    <Popconfirm
                        title="Xóa thành viên này?"
                        description="Hành động này không thể hoàn tác."
                        onConfirm={() => handleDelete(record.id)}
                        disabled={!canDelete}
                        okText="Xóa"
                        cancelText="Hủy"
                    >
                        <Button icon={<DeleteOutlined />} danger disabled={!canDelete} title="Xóa" />
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    return (
        <div className="p-4 md:p-6">
            <Card className={!screens.md ? "bg-transparent shadow-none border-none" : "shadow-sm border-gray-100 rounded-xl overflow-hidden"} styles={{ body: { padding: !screens.md ? 0 : undefined } }}>
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6 px-3 md:px-0">
                    <Space size="middle">
                        <div className="hidden md:flex w-12 h-12 rounded-xl bg-indigo-50 items-center justify-center text-indigo-500">
                            <UserOutlined className="text-2xl" />
                        </div>
                        <div>
                            <Title level={3} className="text-xl md:text-2xl mt-3 text-[#4f46e5]">Quản lý Thành viên</Title>
                            <Text type="secondary" className="text-xs md:text-sm">Quản lý tài khoản, vai trò và thông tin đội ngũ</Text>
                        </div>
                    </Space>
                    {canCreate && (
                        <div className="flex gap-2 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
                            <Button
                                icon={<FileExcelOutlined />}
                                onClick={() => dispatch({ type: 'OPEN_IMPORT_MODAL' })}
                                className="flex-1 md:flex-none border-green-600 text-green-600 hover:!text-green-500 hover:!border-green-500"
                            >
                                Import
                            </Button>
                            <Button
                                type="primary"
                                icon={<PlusOutlined />}
                                onClick={() => {
                                    form.resetFields();
                                    form.setFieldsValue({ status: 'active' });
                                    dispatch({ type: 'OPEN_USER_MODAL' });
                                }}
                                className="flex-1 md:flex-none bg-linear-to-r from-[#667eea] to-[#764ba2] border-none shadow-md h-10 font-semibold"
                            >
                                {screens.md ? 'Add New User' : 'Add User'}
                            </Button>
                        </div>
                    )}
                </div>

                {/* Search & Filter Bar */}
                <div className="px-3 md:px-0 mb-4">
                    <Row gutter={[12, 12]}>
                        <Col xs={24} md={8}>
                            <Input
                                placeholder="Tìm kiếm tên, email, SĐT..."
                                prefix={<SearchOutlined className="text-gray-400" />}
                                value={searchText}
                                onChange={(e) => setSearchText(e.target.value)}
                                allowClear
                                className="w-full"
                            />
                        </Col>
                        <Col xs={12} md={5}>
                            <Select
                                placeholder="Vai trò"
                                value={filterRole}
                                onChange={setFilterRole}
                                allowClear
                                className="w-full"
                                suffixIcon={<FilterOutlined />}
                            >
                                {roles.map(role => (
                                    <Option key={role.id} value={role.name}>
                                        {role.name.toUpperCase()}
                                    </Option>
                                ))}
                            </Select>
                        </Col>
                        <Col xs={12} md={5}>
                            <Select
                                placeholder="Trạng thái"
                                value={filterStatus}
                                onChange={setFilterStatus}
                                allowClear
                                className="w-full"
                                suffixIcon={<FilterOutlined />}
                            >
                                <Option value="active">Active</Option>
                                <Option value="inactive">Inactive</Option>
                            </Select>
                        </Col>
                        {(searchText || filterRole || filterStatus) && (
                            <Col xs={24} md={6}>
                                <Button
                                    onClick={() => {
                                        setSearchText('');
                                        setFilterRole(undefined);
                                        setFilterStatus(undefined);
                                    }}
                                    block
                                    icon={<DeleteOutlined className="text-xs" />}
                                >
                                    Xóa lọc
                                </Button>
                            </Col>
                        )}
                    </Row>
                </div>

                {!canUpdate && (
                    <div className="mb-4 bg-yellow-50 p-4 rounded-lg border border-yellow-100 flex items-center mx-3 md:mx-0">
                        <LockOutlined className="text-yellow-600 mr-3 text-lg" />
                        <Text type="warning" className="text-xs md:text-base">
                            Read-only access. Contact admin to modify.
                        </Text>
                    </div>
                )}

                {!screens.md ? (
                    <MobileListView
                        filteredUsers={filteredUsers}
                        isLoading={isLoading}
                        canUpdate={canUpdate}
                        canDelete={canDelete}
                        onNavigate={(id) => navigate(`/dashboard/profile/${id}`)}
                        onEdit={(user) => {
                            form.setFieldsValue(user);
                            dispatch({ type: 'OPEN_USER_MODAL', payload: user });
                        }}
                        onDelete={handleDelete}
                    />
                ) : (
                    <Table
                        columns={columns}
                        dataSource={filteredUsers}
                        rowKey="id"
                        loading={isLoading}
                        className="border border-gray-100 rounded-lg custom-table"
                        pagination={{ pageSize: 10 }}
                        scroll={{ x: 1000 }}
                    />
                )}
            </Card>

            <Modal
                title={
                    <Space>
                        {editingUser ? <EditOutlined /> : <PlusOutlined />}
                        <span>{editingUser ? 'Edit User Information' : 'Create New User Account'}</span>
                    </Space>
                }
                open={isUserModalOpen}
                onCancel={() => dispatch({ type: 'CLOSE_USER_MODAL' })}
                onOk={() => form.submit()}
                width={screens.xs ? '100%' : 600}
                centered
                okText={editingUser ? 'Save Changes' : 'Create User'}
                confirmLoading={createUser.isPending || updateUser.isPending}
                destroyOnHidden
            >
                <Form form={form} layout="vertical" onFinish={handleCreateOrUpdate} className="mt-6">
                    <div className="grid grid-cols-2 gap-4">
                        <Form.Item name="name" label="Full Name" rules={[{ required: true, message: 'Please input the full name!' }]}>
                            <Input prefix={<UserOutlined className="text-gray-400" />} placeholder="John Doe" />
                        </Form.Item>
                        <Form.Item name="email" label="Email Address" rules={[{ required: true, type: 'email', message: 'Please input a valid email!' }]}>
                            <Input prefix={<MailOutlined className="text-gray-400" />} placeholder="john@example.com" disabled={!!editingUser} />
                        </Form.Item>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <Form.Item name="phone_number" label="Phone Number">
                            <Input prefix={<PhoneOutlined className="text-gray-400" />} placeholder="+84 123 456 789" />
                        </Form.Item>
                        <Form.Item name="role_id" label="System Role" rules={[{ required: true, message: 'Please select a role!' }]}>
                            <Select placeholder="Select a role">
                                {roles.map(role => (
                                    <Option key={role.id} value={role.id}>
                                        <Tag color={role.name === 'admin' ? 'volcano' : role.name === 'leader' ? 'blue' : 'green'}>
                                            {role.name.toUpperCase()}
                                        </Tag>
                                    </Option>
                                ))}
                            </Select>
                        </Form.Item>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <Form.Item name="status" label="Account Status" rules={[{ required: true }]}>
                            <Select>
                                <Option value="active">
                                    <Space><CheckCircleOutlined className="text-green-500" />Active</Space>
                                </Option>
                                <Option value="inactive">
                                    <Space><StopOutlined className="text-red-500" />Inactive</Space>
                                </Option>
                            </Select>
                        </Form.Item>
                        <Form.Item name="discord_id" label="Discord ID">
                            <Input prefix={<DiscordOutlined className="text-gray-400" />} placeholder="123456789" />
                        </Form.Item>
                    </div>

                    <Form.Item name="avatar_url" label="Avatar URL">
                        <Input prefix={<PictureOutlined className="text-gray-400" />} placeholder="https://example.com/avatar.jpg" />
                    </Form.Item>
                </Form>
            </Modal>

            <ImportUserModal
                open={isImportModalOpen}
                onCancel={() => dispatch({ type: 'CLOSE_IMPORT_MODAL' })}
            />
        </div>
    );
};

const ImportUserModal = ({ open, onCancel }: { open: boolean; onCancel: () => void }) => {
    const importUsers = useImportUsers();
    const [file, setFile] = useState<File | null>(null);
    const [result, setResult] = useState<any | null>(null);

    const handleImport = async () => {
        if (!file) return;
        try {
            const res = await importUsers.mutateAsync(file);
            setResult(res.data);
            message.success('Import process completed');
        } catch (error: any) {
            message.error(error?.response?.data?.message || 'Import failed');
        }
    };

    const handleClose = () => {
        setFile(null);
        setResult(null);
        onCancel();
    };

    return (
        <Modal
            title={<Space><UploadOutlined /> Import Users from Excel</Space>}
            open={open}
            onCancel={handleClose}
            footer={[
                <Button key="close" onClick={handleClose}>Close</Button>,
                !result && (
                    <Button
                        key="import"
                        type="primary"
                        onClick={handleImport}
                        disabled={!file}
                        loading={importUsers.isPending}
                    >
                        Import
                    </Button>
                )
            ]}
            width={600}
        >
            {!result ? (
                <div className="py-4">
                    <Alert
                        message="File Format Requirement"
                        description={
                            <ul className="list-disc pl-4 mt-2">
                                <li>Format: .xlsx or .csv</li>
                                <li>Required Columns: <b>name</b>, <b>email</b>, <b>phone_number</b></li>
                                <li>Default Role: <b>Teammate</b></li>
                            </ul>
                        }
                        type="info"
                        showIcon
                        className="mb-4"
                    />
                    <Upload.Dragger
                        beforeUpload={(file) => {
                            setFile(file);
                            return false;
                        }}
                        fileList={file ? [file as any] : []}
                        onRemove={() => setFile(null)}
                        accept=".xlsx, .xls, .csv"
                        maxCount={1}
                    >
                        <p className="ant-upload-drag-icon">
                            <UploadOutlined className="text-4xl text-gray-400" />
                        </p>
                        <p className="ant-upload-text">Click or drag file to this area to upload</p>
                        <p className="ant-upload-hint">
                            Support for a single upload. Strictly prohibited from uploading company data or other banned files.
                        </p>
                    </Upload.Dragger>
                </div>
            ) : (
                <div className="py-4 space-y-4">
                    <Alert
                        message="Import Completed"
                        description={`Total: ${result.total} | Success: ${result.success_count} | Error: ${result.error_count}`}
                        type={result.error_count > 0 ? "warning" : "success"}
                        showIcon
                    />

                    {result.errors && result.errors.length > 0 && (
                        <div className="max-h-60 overflow-y-auto border rounded p-2 bg-red-50">
                            <Typography.Text type="danger" strong>Error Details:</Typography.Text>
                            <ul className="list-disc pl-4 mt-1 text-sm text-red-600">
                                {result.errors.map((err: string) => (
                                    <li key={err}>{err}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}
        </Modal>
    );
};

export default UserManagementPage;
