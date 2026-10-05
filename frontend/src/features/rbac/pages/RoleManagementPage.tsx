import { useState } from 'react';
import { Button, Card, Grid, message, Space, Typography } from 'antd';
import { LockOutlined, PlusOutlined, SafetyCertificateOutlined } from '@ant-design/icons';
import { motion, type Variants } from 'motion/react';
import { useAuth } from '@/features/auth';
import useToggle from '@/hooks/useToggle';
import ApiKeyModal from '@/features/robot/components/ApiKeyModal';
import {
    useCreateRole,
    useDeleteRole,
    useRoles,
    useUpdateRole,
} from '../hooks/useRbac';
import {
    RoleFormModal,
    RoleMobileList,
    RolePermissionModal,
    RoleTable,
} from '../components';
import { RolePermission, type RoleResponse } from '../types/rbac.types';

const { Title, Text } = Typography;

const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.1,
        },
    },
};

const itemVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
        opacity: 1,
        y: 0,
        transition: { duration: 0.4, ease: 'easeOut' },
    },
};

const RoleManagementPage = () => {
    const { hasPermission } = useAuth();
    const screens = Grid.useBreakpoint();

    // Query roles without permissions (no heavy table joins)
    const { data: roles = [], isLoading } = useRoles();
    const createRole = useCreateRole();
    const updateRole = useUpdateRole();
    const deleteRole = useDeleteRole();

    // Role Create/Edit Modal state
    const [isRoleModalOpen, toggleRoleModal] = useToggle(false);
    const [editingRole, setEditingRole] = useState<RoleResponse | null>(null);

    // Permission Modal state (lazy query role permissions only when opened)
    const [isPermModalOpen, togglePermModal] = useToggle(false);
    const [selectedRoleForPerms, setSelectedRoleForPerms] = useState<RoleResponse | null>(null);

    // API Key Modal state
    const [isApiKeyModalOpen, toggleApiKeyModal] = useToggle(false);
    const [selectedRoleForApiKeys, setSelectedRoleForApiKeys] = useState<RoleResponse | null>(null);

    const canCreateRole = hasPermission(RolePermission.CREATE);
    const canUpdateRole = hasPermission(RolePermission.UPDATE);
    const canDeleteRole = hasPermission(RolePermission.DELETE);

    const handleCreateOrUpdateRole = async (values: Record<string, unknown>) => {
        try {
            if (editingRole) {
                await updateRole.mutateAsync({ id: editingRole.id, data: values as any });
                message.success('Role updated successfully');
            } else {
                await createRole.mutateAsync(values as any);
                message.success('Role created successfully');
            }
            toggleRoleModal(false);
        } catch (error: unknown) {
            const err = error as { response?: { data?: { message?: string } } };
            message.error(err?.response?.data?.message || 'Operation failed');
        }
    };

    const handleDeleteRole = async (id: number) => {
        try {
            await deleteRole.mutateAsync(id);
            message.success('Role deleted successfully');
        } catch (error: unknown) {
            const err = error as { response?: { data?: { message?: string } } };
            message.error(err?.response?.data?.message || 'Delete failed');
        }
    };

    const handleOpenPermModal = (role: RoleResponse) => {
        setSelectedRoleForPerms(role);
        togglePermModal(true);
    };

    const handleOpenApiKeyModal = (role: RoleResponse) => {
        setSelectedRoleForApiKeys(role);
        toggleApiKeyModal(true);
    };

    const handleOpenEditModal = (role: RoleResponse) => {
        setEditingRole(role);
        toggleRoleModal(true);
    };

    return (
        <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="p-4 md:p-6"
        >
            <Card
                className={
                    !screens.md
                        ? 'bg-transparent shadow-none border-none'
                        : 'shadow-sm border-gray-100 rounded-xl overflow-hidden'
                }
                styles={{ body: { padding: !screens.md ? 0 : undefined } }}
            >
                {/* Header */}
                <motion.div
                    variants={itemVariants}
                    className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6 px-3 md:px-0"
                >
                    <Space size="middle">
                        <div className="hidden md:flex w-12 h-12 rounded-xl bg-purple-50 items-center justify-center text-purple-600 shadow-sm">
                            <SafetyCertificateOutlined className="text-2xl" />
                        </div>
                        <div>
                            <Title level={3} className="text-xl md:text-2xl mt-4 text-purple-600">
                                Quản lý Vai trò
                            </Title>
                            <Text type="secondary" className="text-xs md:text-sm">
                                Phân quyền và quản lý API Keys cho các vai trò
                            </Text>
                        </div>
                    </Space>
                    {canCreateRole && (
                        <Button
                            type="primary"
                            icon={<PlusOutlined />}
                            onClick={() => {
                                setEditingRole(null);
                                toggleRoleModal(true);
                            }}
                            className="w-full md:w-auto bg-linear-to-r from-[#667eea] to-[#764ba2] border-none font-semibold h-10"
                        >
                            New Role
                        </Button>
                    )}
                </motion.div>

                {/* Read-only Alert */}
                {!canUpdateRole && (
                    <motion.div
                        variants={itemVariants}
                        className="mb-4 bg-yellow-50 p-4 rounded-lg border border-yellow-100 mx-3 md:mx-0"
                    >
                        <Text type="warning" className="flex items-center text-sm">
                            <LockOutlined className="mr-2" />
                            <span>Read-only mode. Contact admin for access.</span>
                        </Text>
                    </motion.div>
                )}

                {/* Role List (Mobile or Desktop Table) */}
                {!screens.md ? (
                    <motion.div variants={itemVariants}>
                        <RoleMobileList
                            roles={roles}
                            isLoading={isLoading}
                            canUpdateRole={canUpdateRole}
                            canDeleteRole={canDeleteRole}
                            onOpenPerms={handleOpenPermModal}
                            onOpenApiKeys={handleOpenApiKeyModal}
                            onEdit={handleOpenEditModal}
                            onDelete={handleDeleteRole}
                        />
                    </motion.div>
                ) : (
                    <motion.div variants={itemVariants}>
                        <RoleTable
                            roles={roles}
                            isLoading={isLoading}
                            canUpdateRole={canUpdateRole}
                            canDeleteRole={canDeleteRole}
                            onOpenPerms={handleOpenPermModal}
                            onOpenApiKeys={handleOpenApiKeyModal}
                            onEdit={handleOpenEditModal}
                            onDelete={handleDeleteRole}
                        />
                    </motion.div>
                )}
            </Card>

            {/* Role Create/Edit Modal */}
            <RoleFormModal
                open={isRoleModalOpen}
                editingRole={editingRole}
                isSubmitting={createRole.isPending || updateRole.isPending}
                onCancel={() => toggleRoleModal(false)}
                onSubmit={handleCreateOrUpdateRole}
            />

            {/* Permission Assignment Modal (Lazy loaded permissions) */}
            <RolePermissionModal
                open={isPermModalOpen}
                roleId={selectedRoleForPerms?.id ?? null}
                roleName={selectedRoleForPerms?.name}
                onClose={() => togglePermModal(false)}
            />

            {/* API Key Management Modal */}
            <ApiKeyModal
                role={selectedRoleForApiKeys}
                open={isApiKeyModalOpen}
                onClose={() => toggleApiKeyModal(false)}
            />
        </motion.div>
    );
};

export default RoleManagementPage;
