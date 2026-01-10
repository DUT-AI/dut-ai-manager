import { useState, useEffect } from 'react';
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
import { rbacService } from '@/services/api/rbac.service';
import { RolePermission } from '@/types/rbac.types';
import type { RoleResponse, PermissionResponse } from '@/types/rbac.types';
import { useAuth } from '@/context/AuthContext';
import useToggle from '@/hooks/useToggle';

const { Title, Text } = Typography;

const RoleManagementPage = () => {
    const { hasPermission } = useAuth();
    const [roles, setRoles] = useState<RoleResponse[]>([]);
    const [permissions, setPermissions] = useState<PermissionResponse[]>([]);
    const [loading, setLoading] = useState(false);
    const [isModalOpen, toggleModal] = useToggle(false);
    const [editingRole, setEditingRole] = useState<RoleResponse | null>(null);
    const [form] = Form.useForm();

    const [isPermModalOpen, togglePermModal] = useToggle(false);
    const [currentRoleForPerms, setCurrentRoleForPerms] = useState<RoleResponse | null>(null);
    const [targetKeys, setTargetKeys] = useState<string[]>([]);

    const canCreateRole = hasPermission(RolePermission.CREATE);
    const canUpdateRole = hasPermission(RolePermission.UPDATE);
    const canDeleteRole = hasPermission(RolePermission.DELETE);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [rolesRes, permsRes] = await Promise.all([
                rbacService.getRoles(),
                rbacService.getPermissions()
            ]);
            if (rolesRes.is_success) setRoles(rolesRes.data || []);
            if (permsRes.is_success) setPermissions(permsRes.data || []);
        } catch (error) {
            message.error('Failed to fetch RBAC data');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleCreateOrUpdate = async (values: any) => {
        try {
            if (editingRole) {
                await rbacService.updateRole(editingRole.id, values);
                message.success('Role updated successfully');
            } else {
                await rbacService.createRole(values);
                message.success('Role created successfully');
            }
            toggleModal(false);
            form.resetFields();
            fetchData();
        } catch (error) {
            message.error('Operation failed');
        }
    };

    const handleDelete = async (id: number) => {
        try {
            await rbacService.deleteRole(id);
            message.success('Role deleted successfully');
            fetchData();
        } catch (error) {
            message.error('Delete failed');
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
            setLoading(true);
            for (const key of moveKeys) {
                const permId = parseInt(key as string);
                if (direction === 'right') {
                    await rbacService.addPermissionToRole(currentRoleForPerms.id, permId);
                } else {
                    await rbacService.removePermissionFromRole(currentRoleForPerms.id, permId);
                }
            }
            message.success('Permissions updated');
            setTargetKeys(nextTargetKeys as string[]);
            fetchData();
        } catch (error) {
            message.error('Failed to update permissions');
        } finally {
            setLoading(false);
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
                    loading={loading}
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
