import { useMemo, useReducer, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileExcelOutlined, LockOutlined, PlusOutlined, UserOutlined } from '@ant-design/icons';
import { Button, Card, Grid, message, Space, Typography } from 'antd';
import { motion, type Variants } from 'motion/react';
import { useAuth } from '../../auth/context/AuthContext';
import { useRoles } from '@/features/rbac';
import { UserPermission } from '../../rbac/types/rbac.types';
import {
    useCreateUser,
    useDeleteUser,
    useUpdateUser,
    useUsers,
} from '../hooks/useUsers';
import {
    ImportUserModal,
    UserFilterBar,
    UserFormModal,
    UserMobileList,
    UserTable,
} from '../components';
import { UserStatus, type UserResponse } from '../types/user.types';

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

    // Permissions
    const canCreate = hasPermission(UserPermission.CREATE);
    const canUpdate = hasPermission(UserPermission.UPDATE);
    const canDelete = hasPermission(UserPermission.DELETE);

    // Filtered users
    const filteredUsers = useMemo(() => {
        return users.filter((user) => {
            const matchSearch =
                searchText === '' ||
                user.name?.toLowerCase().includes(searchText.toLowerCase()) ||
                user.email?.toLowerCase().includes(searchText.toLowerCase()) ||
                user.phone_number?.toLowerCase().includes(searchText.toLowerCase());

            const matchRole = !filterRole || (user.role_names && user.role_names.includes(filterRole));
            const matchStatus = !filterStatus || user.status === filterStatus;

            return matchSearch && matchRole && matchStatus;
        });
    }, [users, searchText, filterRole, filterStatus]);

    const handleCreateOrUpdate = async (values: Record<string, unknown>) => {
        try {
            if (editingUser) {
                await updateUser.mutateAsync({ id: editingUser.id, data: values as any });
                message.success('User updated successfully');
            } else {
                await createUser.mutateAsync(values as any);
                message.success('User created successfully');
            }
            dispatch({ type: 'CLOSE_USER_MODAL' });
        } catch (error: unknown) {
            const err = error as { response?: { data?: { message?: string } } };
            message.error(err?.response?.data?.message || 'Operation failed');
        }
    };

    const handleDelete = async (id: number) => {
        try {
            await deleteUser.mutateAsync(id);
            message.success('User deleted successfully');
        } catch {
            message.error('Delete failed');
        }
    };

    const handleResetFilters = () => {
        setSearchText('');
        setFilterRole(undefined);
        setFilterStatus(undefined);
    };

    return (
        <motion.div variants={containerVariants} initial="hidden" animate="visible" className="p-4 md:p-6">
            <Card
                className={
                    !screens.md
                        ? 'bg-transparent shadow-none border-none'
                        : 'shadow-sm border-gray-100 rounded-xl overflow-hidden'
                }
                styles={{ body: { padding: !screens.md ? 0 : undefined } }}
            >
                {/* Header Section */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6 px-3 md:px-0">
                    <Space size="middle">
                        <div className="hidden md:flex w-12 h-12 rounded-xl bg-indigo-50 items-center justify-center text-indigo-500">
                            <UserOutlined className="text-2xl" />
                        </div>
                        <div>
                            <Title level={3} className="text-xl md:text-2xl mt-3 text-[#4f46e5]">
                                Quản lý Thành viên
                            </Title>
                            <Text type="secondary" className="text-xs md:text-sm">
                                Quản lý tài khoản, vai trò và thông tin đội ngũ
                            </Text>
                        </div>
                    </Space>
                    {canCreate && (
                        <div className="flex gap-2 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
                            <Button
                                icon={<FileExcelOutlined />}
                                onClick={() => dispatch({ type: 'OPEN_IMPORT_MODAL' })}
                                className="flex-1 md:flex-none border-green-600 text-green-600 hover:text-green-500 hover:border-green-500"
                            >
                                Import
                            </Button>
                            <Button
                                type="primary"
                                icon={<PlusOutlined />}
                                onClick={() => dispatch({ type: 'OPEN_USER_MODAL' })}
                                className="flex-1 md:flex-none bg-linear-to-r from-[#667eea] to-[#764ba2] border-none shadow-md h-10 font-semibold"
                            >
                                {screens.md ? 'Add New User' : 'Add User'}
                            </Button>
                        </div>
                    )}
                </div>

                {/* Search & Filter Bar */}
                <motion.div variants={itemVariants}>
                    <UserFilterBar
                        searchText={searchText}
                        onSearchTextChange={setSearchText}
                        filterRole={filterRole}
                        onFilterRoleChange={setFilterRole}
                        filterStatus={filterStatus}
                        onFilterStatusChange={setFilterStatus}
                        roles={roles}
                        onResetFilters={handleResetFilters}
                    />
                </motion.div>

                {/* Read-only Access Warning */}
                {!canUpdate && (
                    <motion.div
                        variants={itemVariants}
                        className="mb-4 bg-yellow-50 p-4 rounded-lg border border-yellow-100 flex items-center mx-3 md:mx-0"
                    >
                        <LockOutlined className="text-yellow-600 mr-3 text-lg" />
                        <Text type="warning" className="text-xs md:text-base">
                            Read-only access. Contact admin to modify.
                        </Text>
                    </motion.div>
                )}

                {/* User Content: Mobile List or Desktop Table */}
                {!screens.md ? (
                    <motion.div variants={itemVariants}>
                        <UserMobileList
                            filteredUsers={filteredUsers}
                            isLoading={isLoading}
                            canUpdate={canUpdate}
                            canDelete={canDelete}
                            onNavigate={(id) => navigate(`/dashboard/profile/${id}`)}
                            onEdit={(user) => dispatch({ type: 'OPEN_USER_MODAL', payload: user })}
                            onDelete={handleDelete}
                        />
                    </motion.div>
                ) : (
                    <motion.div variants={itemVariants}>
                        <UserTable
                            users={filteredUsers}
                            isLoading={isLoading}
                            canUpdate={canUpdate}
                            canDelete={canDelete}
                            onNavigateProfile={(id) => navigate(`/dashboard/profile/${id}`)}
                            onEdit={(user) => dispatch({ type: 'OPEN_USER_MODAL', payload: user })}
                            onDelete={handleDelete}
                        />
                    </motion.div>
                )}
            </Card>

            {/* User Form Modal (Create / Edit) */}
            <UserFormModal
                open={isUserModalOpen}
                editingUser={editingUser}
                roles={roles}
                isSubmitting={createUser.isPending || updateUser.isPending}
                onCancel={() => dispatch({ type: 'CLOSE_USER_MODAL' })}
                onSubmit={handleCreateOrUpdate}
            />

            {/* Import User Modal (Excel) */}
            <ImportUserModal
                open={isImportModalOpen}
                onCancel={() => dispatch({ type: 'CLOSE_IMPORT_MODAL' })}
            />
        </motion.div>
    );
};

export default UserManagementPage;
