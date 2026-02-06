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
    Transfer,
    Grid,
    List,
    Checkbox,
    Spin
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

    const handleMobilePermToggle = async (permId: number, checked: boolean) => {
        if (!currentRoleForPerms) return;
        try {
            setPermLoading(true);
            if (checked) {
                await addPermissionToRole.mutateAsync({ roleId: currentRoleForPerms.id, permId });
            } else {
                await removePermissionFromRole.mutateAsync({ roleId: currentRoleForPerms.id, permId });
            }
            const newKeys = checked
                ? [...targetKeys, permId.toString()]
                : targetKeys.filter(k => k !== permId.toString());
            setTargetKeys(newKeys);
            message.success('Permission updated');
        } catch (error: any) {
            message.error(error?.response?.data?.message || 'Failed to update permission');
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

    const screens = Grid.useBreakpoint();

    const MobileListView = () => (
        <div className="mt-4 px-3">
            <List
                dataSource={roles}
                loading={isLoading}
                split={false}
                renderItem={(role) => (
                    <List.Item className="px-2 !mb-4 !border-0">
                        <Card
                            className="w-full shadow-sm border-gray-100 overflow-hidden"
                            styles={{ body: { padding: '16px' } }}
                            actions={[
                                <Button
                                    type="text"
                                    icon={<KeyOutlined />}
                                    onClick={() => openPermissionModal(role)}
                                    disabled={!canUpdateRole}
                                >
                                    Perms
                                </Button>,
                                <Button
                                    type="text"
                                    icon={<EditOutlined />}
                                    onClick={() => {
                                        setEditingRole(role);
                                        form.setFieldsValue(role);
                                        toggleModal(true);
                                    }}
                                    disabled={!canUpdateRole}
                                >
                                    Edit
                                </Button>,
                                <Popconfirm
                                    title="Delete this role?"
                                    onConfirm={() => handleDelete(role.id)}
                                    disabled={!canDeleteRole}
                                >
                                    <Button type="text" danger icon={<DeleteOutlined />} disabled={!canDeleteRole}>Delete</Button>
                                </Popconfirm>
                            ]}
                        >
                            <div className="flex items-center justify-between mb-4">
                                <Tag color={role.name === 'admin' ? 'volcano' : role.name === 'leader' ? 'blue' : 'green'} className="uppercase font-bold m-0 text-base py-1 px-3">
                                    {role.name}
                                </Tag>
                            </div>

                            <div className="mb-4">
                                <Text type="secondary" className="block mb-1 text-xs uppercase font-bold tracking-wider">Description</Text>
                                <Text>{role.description || 'No description provided.'}</Text>
                            </div>

                            <div>
                                <Text type="secondary" className="block mb-2 text-xs uppercase font-bold tracking-wider">Permissions ({role.permissions.length})</Text>
                                <div className="flex flex-wrap gap-1">
                                    {role.permissions.length > 0 ? (
                                        role.permissions.slice(0, 5).map(p => (
                                            <Tag key={p.id} color="blue" className="mr-0 mb-1">
                                                {p.resource}:{p.action}
                                            </Tag>
                                        ))
                                    ) : (
                                        <Text type="secondary" italic className="text-xs">No permissions assigned</Text>
                                    )}
                                    {role.permissions.length > 5 && (
                                        <Tag className="mr-0 mb-1">+{role.permissions.length - 5} more</Tag>
                                    )}
                                </div>
                            </div>
                        </Card>
                    </List.Item>
                )}
            />
        </div>
    );

    return (
        <div className="p-4 md:p-6">
            <Card className={!screens.md ? "bg-transparent shadow-none border-none" : "shadow-sm border-gray-100 rounded-xl overflow-hidden"} styles={{ body: { padding: !screens.md ? 0 : undefined } }}>
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6 px-3 md:px-0">
                    <Space>
                        <SafetyCertificateOutlined className="text-2xl text-[#667eea]" />
                        <Title level={3} className="mt-4 text-xl md:text-2xl">Role Management</Title>
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
                            className="w-full md:w-auto bg-linear-to-r from-[#667eea] to-[#764ba2] border-none font-semibold h-10"
                        >
                            New Role
                        </Button>
                    )}
                </div>

                {!canUpdateRole && (
                    <div className="mb-4 bg-yellow-50 p-4 rounded-lg border border-yellow-100 mx-3 md:mx-0">
                        <Text type="warning" className="flex items-center text-sm">
                            <LockOutlined className="mr-2" />
                            <span>Read-only mode. Contact admin for access.</span>
                        </Text>
                    </div>
                )}

                {!screens.md ? (
                    <MobileListView />
                ) : (
                    <Table
                        columns={columns}
                        dataSource={roles}
                        rowKey="id"
                        loading={isLoading}
                        pagination={false}
                        className="border border-gray-100 rounded-lg"
                    />
                )}
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
                title={`Permissions: ${currentRoleForPerms?.name.toUpperCase()}`}
                open={isPermModalOpen}
                onCancel={() => togglePermModal(false)}
                width={screens.md ? 700 : '95%'}
                footer={null}
                centered
                styles={{ body: { maxHeight: '70vh', overflowY: 'auto', padding: screens.md ? '24px' : '12px' } }}
            >
                <div className="mt-2">
                    {screens.md ? (
                        <div className="flex justify-center">
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
                    ) : (
                        <Spin spinning={permLoading}>
                            <List
                                dataSource={permissions}
                                renderItem={p => (
                                    <List.Item className="!px-0">
                                        <Checkbox
                                            checked={targetKeys.includes(p.id.toString())}
                                            onChange={(e) => handleMobilePermToggle(p.id, e.target.checked)}
                                            className="w-full"
                                        >
                                            <div className="flex flex-col ml-2">
                                                <Text strong>{p.resource}:{p.action}</Text>
                                                {p.description && <Text type="secondary" className="text-xs">{p.description}</Text>}
                                            </div>
                                        </Checkbox>
                                    </List.Item>
                                )}
                            />
                        </Spin>
                    )}
                </div>
            </Modal>
        </div>
    );
};

export default RoleManagementPage;
