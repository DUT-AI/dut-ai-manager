import { useState } from 'react';
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
    Transfer
} from 'antd';
import type { TransferProps } from 'antd';
import {
    PlusOutlined,
    EditOutlined,
    DeleteOutlined,
    SafetyCertificateOutlined,
    LockOutlined,
    KeyOutlined
} from '@ant-design/icons';
import {
    useRoles,
    usePermissions,
    useCreateRole,
    useUpdateRole,
    useDeleteRole,
    useAddPermissionToRole,
    useRemovePermissionFromRole
} from '@/hooks';
import { RolePermission } from '@/types/rbac.types';
import type { RoleResponse } from '@/types/rbac.types';
import { useAuth } from '@/context/AuthContext';
import useToggle from '@/hooks/useToggle';

const { Title, Text } = Typography;

const RoleManagementPage = () => {
    const { hasPermission } = useAuth();
    const [form] = Form.useForm();

    // TanStack Query hooks
    const { data: roles = [], isLoading } = useRoles();
    const { data: permissions = [] } = usePermissions();
    const createRole = useCreateRole();
    const updateRole = useUpdateRole();
    const deleteRole = useDeleteRole();
    const addPermissionToRole = useAddPermissionToRole();
    const removePermissionFromRole = useRemovePermissionFromRole();

    // Modal states
    const [isModalOpen, toggleModal] = useToggle(false);
    const [editingRole, setEditingRole] = useState<RoleResponse | null>(null);
    const [isPermModalOpen, togglePermModal] = useToggle(false);
    const [currentRoleForPerms, setCurrentRoleForPerms] = useState<RoleResponse | null>(null);
    const [targetKeys, setTargetKeys] = useState<string[]>([]);
    const [permLoading, setPermLoading] = useState(false);

    const canCreateRole = hasPermission(RolePermission.CREATE);
    const canUpdateRole = hasPermission(RolePermission.UPDATE);
    const canDeleteRole = hasPermission(RolePermission.DELETE);

    const handleCreateOrUpdate = async (values: any) => {
        try {
            if (editingRole) {
                await updateRole.mutateAsync({ id: editingRole.id, data: values });
                message.success('Role updated successfully');
            } else {
                await createRole.mutateAsync(values);
                message.success('Role created successfully');
            }
            toggleModal(false);
            form.resetFields();
        } catch (error: any) {
            message.error(error?.response?.data?.message || 'Operation failed');
        }
    };

    const handleDelete = async (id: number) => {
        try {
            await deleteRole.mutateAsync(id);
            message.success('Role deleted successfully');
        } catch (error: any) {
            message.error(error?.response?.data?.message || 'Delete failed');
        }
    };

    const openPermissionModal = (role: RoleResponse) => {
        setCurrentRoleForPerms(role);
        const assignedKeys = role.permissions.map(p => p.id.toString());
        setTargetKeys(assignedKeys);
        togglePermModal(true);
    };

    const handlePermTransfer: TransferProps['onChange'] = async (nextTargetKeys, direction, moveKeys) => {
        if (!currentRoleForPerms) return;

        try {
            setPermLoading(true);
            for (const key of moveKeys) {
                const permId = parseInt(key as string);
                if (direction === 'right') {
                    await addPermissionToRole.mutateAsync({ roleId: currentRoleForPerms.id, permId });
                } else {
                    await removePermissionFromRole.mutateAsync({ roleId: currentRoleForPerms.id, permId });
                }
            }
            message.success('Permissions updated');
            setTargetKeys(nextTargetKeys as string[]);
        } catch (error: any) {
            message.error(error?.response?.data?.message || 'Failed to update permissions');
        } finally {
            setPermLoading(false);
        }
    };

    const columns = [
        {
            title: 'Role Name',
            dataIndex: 'name',
            key: 'name',
            render: (name: string) => (
                <Tag color={name === 'admin' ? 'volcano' : name === 'leader' ? 'blue' : 'green'} className="uppercase font-bold">
                    {name}
                </Tag>
            ),
        },
        {
            title: 'Description',
            dataIndex: 'description',
            key: 'description',
        },
        {
            title: 'Permissions',
            key: 'permissions',
            render: (_: any, record: RoleResponse) => (
                <Space wrap>
                    {record.permissions.length > 0 ? (
                        record.permissions.map(p => (
                            <Tag key={p.id} color="blue">
                                {p.resource}:{p.action}
                            </Tag>
                        ))
                    ) : (
                        <Text type="secondary" italic>No permissions</Text>
                    )}
                </Space>
            ),
        },
        {
            title: 'Actions',
            key: 'actions',
            render: (_: any, record: RoleResponse) => (
                <Space>
                    <Button
                        icon={<KeyOutlined />}
                        onClick={() => openPermissionModal(record)}
                        disabled={!canUpdateRole}
                    >
                        Manage Perms
                    </Button>
                    <Button
                        icon={<EditOutlined />}
                        onClick={() => {
                            setEditingRole(record);
                            form.setFieldsValue(record);
                            toggleModal(true);
                        }}
                        disabled={!canUpdateRole}
                    />
                    <Popconfirm
                        title="Are you sure to delete this role?"
                        onConfirm={() => handleDelete(record.id)}
                        disabled={!canDeleteRole}
                    >
                        <Button icon={<DeleteOutlined />} danger disabled={!canDeleteRole} />
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    return (
        <div className="p-6">
            <Card className="shadow-sm border-gray-100 rounded-xl overflow-hidden">
                <div className="flex justify-between items-center mb-6">
                    <Space>
                        <SafetyCertificateOutlined className="text-2xl text-[#667eea]" />
                        <Title level={3} className="!m-0">Role Management</Title>
                    </Space>
                    {canCreateRole && (
                        <Button
                            type="primary"
                            icon={<PlusOutlined />}
                            onClick={() => {
                                setEditingRole(null);
                                form.resetFields();
                                toggleModal(true);
                            }}
                            className="bg-linear-to-r from-[#667eea] to-[#764ba2] border-none"
                        >
                            New Role
                        </Button>
                    )}
                </div>

                {!canUpdateRole && (
                    <div className="mb-4 bg-yellow-50 p-4 rounded-lg border border-yellow-100">
                        <Text type="warning" className="flex items-center">
                            <LockOutlined className="mr-2" />
                            You are in read-only mode. Only administrators can modify roles and permissions.
                        </Text>
                    </div>
                )}

                <Table
                    columns={columns}
                    dataSource={roles}
                    rowKey="id"
                    loading={isLoading}
                    pagination={false}
                    className="border border-gray-100 rounded-lg"
                />
            </Card>

            {/* Role Create/Update Modal */}
            <Modal
                title={editingRole ? 'Edit Role' : 'Create Role'}
                open={isModalOpen}
                onCancel={() => toggleModal(false)}
                onOk={() => form.submit()}
                confirmLoading={createRole.isPending || updateRole.isPending}
            >
                <Form form={form} layout="vertical" onFinish={handleCreateOrUpdate} className="mt-4">
                    <Form.Item name="name" label="Role Name" rules={[{ required: true }]}>
                        <Input placeholder="e.g. admin, leader, teammate" />
                    </Form.Item>
                    <Form.Item name="description" label="Description">
                        <Input.TextArea placeholder="Describe what this role is for" />
                    </Form.Item>
                </Form>
            </Modal>

            {/* Permission Assignment Modal */}
            <Modal
                title={`Assign Permissions to ${currentRoleForPerms?.name.toUpperCase()}`}
                open={isPermModalOpen}
                onCancel={() => togglePermModal(false)}
                width={700}
                footer={null}
            >
                <div className="mt-4 flex justify-center">
                    <Transfer
                        dataSource={permissions.map(p => ({
                            key: p.id.toString(),
                            title: `${p.resource}:${p.action}`,
                            description: p.description || '',
                        }))}
                        titles={['Available', 'Assigned']}
                        targetKeys={targetKeys}
                        onChange={handlePermTransfer}
                        render={item => item.title}
                        disabled={permLoading}
                        listStyle={{
                            width: 300,
                            height: 400,
                        }}
                    />
                </div>
            </Modal>
        </div>
    );
};

export default RoleManagementPage;
