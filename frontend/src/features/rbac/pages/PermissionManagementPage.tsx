import React, { useState } from 'react';
import { Card, Button, Typography, Space, Grid, message } from 'antd';
import { PlusOutlined, FileTextOutlined } from '@ant-design/icons';
import type dayjs from 'dayjs';
import { motion, type Variants } from 'motion/react';

import { useAuth } from '@/features/auth';
import { useUsers } from '@/features/users';
import { PermissionRequestPermission } from '@/features/rbac/types/rbac.types';
import type { PermissionRequestResponse } from '@/features/activity/types/activity.types';

import {
    usePermissionRequests,
    useCreatePermissionRequest,
    useUpdatePermissionRequest,
    useDeletePermissionRequest,
} from '../hooks/usePermissionRequests';

import {
    PermissionFilterBar,
    PermissionTable,
    PermissionMobileList,
    PermissionFormModal,
    PermissionDetailDrawer,
} from '../components/permissions';

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

const PermissionManagementPage: React.FC = () => {
    const { hasPermission } = useAuth();
    const screens = Grid.useBreakpoint();

    // Filter states
    const [filterDate, setFilterDate] = useState<dayjs.Dayjs | null>(null);
    const [filterMonth, setFilterMonth] = useState<number | undefined>();
    const [filterYear, setFilterYear] = useState<number | undefined>();
    const [filterCategory, setFilterCategory] = useState<string | undefined>();
    const [filterUserId, setFilterUserId] = useState<number | undefined>();

    // Modal & Drawer states
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingItem, setEditingItem] = useState<PermissionRequestResponse | null>(null);
    const [detailItem, setDetailItem] = useState<PermissionRequestResponse | null>(null);
    const [isDetailOpen, setIsDetailOpen] = useState(false);

    // Queries & Mutations
    const { data: permissions = [], isLoading } = usePermissionRequests({
        month: filterMonth,
        year: filterYear,
        category: filterCategory,
        userId: filterUserId,
    });
    const { data: usersData = [] } = useUsers();
    const users = Array.isArray(usersData) ? usersData : (usersData as any)?.data || [];

    const createPermission = useCreatePermissionRequest();
    const updatePermission = useUpdatePermissionRequest();
    const deletePermission = useDeletePermissionRequest();

    // Permissions
    const canCreate = hasPermission(PermissionRequestPermission.CREATE);
    const canUpdate = hasPermission(PermissionRequestPermission.UPDATE);
    const canDelete = hasPermission(PermissionRequestPermission.DELETE);

    const handleCreateOrUpdate = async (formattedValues: any) => {
        try {
            if (editingItem) {
                await updatePermission.mutateAsync({ id: editingItem.id, data: formattedValues });
                message.success('Cập nhật đơn xin phép thành công');
            } else {
                await createPermission.mutateAsync(formattedValues);
                message.success('Tạo đơn xin phép thành công');
            }
            setIsModalOpen(false);
            setEditingItem(null);
        } catch (error: any) {
            message.error(error?.response?.data?.message || 'Thao tác thất bại');
            throw error;
        }
    };

    const handleDelete = async (id: number) => {
        try {
            await deletePermission.mutateAsync(id);
            message.success('Xóa đơn xin phép thành công');
            setIsDetailOpen(false);
        } catch (error: any) {
            message.error(error?.response?.data?.message || 'Xóa thất bại');
        }
    };

    const handleOpenEdit = (item: PermissionRequestResponse) => {
        setEditingItem(item);
        setIsModalOpen(true);
    };

    const handleViewDetail = (item: PermissionRequestResponse) => {
        setDetailItem(item);
        setIsDetailOpen(true);
    };

    const handleResetFilter = () => {
        setFilterDate(null);
        setFilterMonth(undefined);
        setFilterYear(undefined);
        setFilterCategory(undefined);
        setFilterUserId(undefined);
    };

    return (
        <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="p-4 md:p-6"
        >
            <Card
                className={!screens.md ? 'bg-transparent shadow-none border-none' : 'shadow-sm border-gray-100 rounded-xl overflow-hidden'}
                styles={{ body: { padding: !screens.md ? 0 : undefined } }}
            >
                {/* Header */}
                <motion.div variants={itemVariants} className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6 px-3 md:px-0">
                    <Space size="middle">
                        <div className="hidden md:flex w-12 h-12 rounded-xl bg-indigo-50 items-center justify-center text-indigo-500">
                            <FileTextOutlined className="text-2xl" />
                        </div>
                        <div>
                            <Title level={3} className="text-xl md:text-2xl mt-4 text-[#4f46e5]">Quản lý Đơn xin phép</Title>
                            <Text type="secondary" className="text-xs md:text-sm">Danh sách và công cụ quản lý các yêu cầu</Text>
                        </div>
                    </Space>
                    {canCreate && (
                        <Button
                            type="primary"
                            icon={<PlusOutlined />}
                            onClick={() => {
                                setEditingItem(null);
                                setIsModalOpen(true);
                            }}
                            className="w-full md:w-auto bg-linear-to-r from-indigo-500 to-purple-600 border-none shadow-md h-10 px-6 font-semibold"
                        >
                            Tạo Đơn mới
                        </Button>
                    )}
                </motion.div>

                {/* Filter Bar */}
                <motion.div variants={itemVariants}>
                    <PermissionFilterBar
                        filterDate={filterDate}
                        filterCategory={filterCategory}
                        filterUserId={filterUserId}
                        users={users}
                        onDateChange={(date) => {
                            setFilterDate(date);
                            setFilterMonth(date ? date.month() + 1 : undefined);
                            setFilterYear(date ? date.year() : undefined);
                        }}
                        onCategoryChange={(val) => setFilterCategory(val)}
                        onUserChange={(val) => setFilterUserId(val)}
                        onReset={handleResetFilter}
                    />
                </motion.div>

                {/* List / Table */}
                <motion.div variants={itemVariants}>
                    {!screens.md ? (
                        <PermissionMobileList
                            permissions={permissions}
                            isLoading={isLoading}
                            canUpdate={canUpdate}
                            canDelete={canDelete}
                            onViewDetail={handleViewDetail}
                            onEdit={handleOpenEdit}
                            onDelete={handleDelete}
                        />
                    ) : (
                        <PermissionTable
                            permissions={permissions}
                            isLoading={isLoading}
                            canUpdate={canUpdate}
                            canDelete={canDelete}
                            onViewDetail={handleViewDetail}
                            onEdit={handleOpenEdit}
                            onDelete={handleDelete}
                        />
                    )}
                </motion.div>
            </Card>

            {/* Create/Edit Modal */}
            <PermissionFormModal
                isOpen={isModalOpen}
                editingItem={editingItem}
                confirmLoading={createPermission.isPending || updatePermission.isPending}
                onClose={() => {
                    setIsModalOpen(false);
                    setEditingItem(null);
                }}
                onSubmit={handleCreateOrUpdate}
            />

            {/* Detail Drawer */}
            <PermissionDetailDrawer
                isOpen={isDetailOpen}
                item={detailItem}
                canUpdate={canUpdate}
                canDelete={canDelete}
                onClose={() => setIsDetailOpen(false)}
                onEdit={(item) => {
                    handleOpenEdit(item);
                    setIsDetailOpen(false);
                }}
                onDelete={handleDelete}
            />
        </motion.div>
    );
};

export default PermissionManagementPage;
