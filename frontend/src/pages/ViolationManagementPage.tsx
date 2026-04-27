import { useState } from 'react';
import { Button, Card, Space, Form, message, Typography, Grid } from 'antd';
import { PlusOutlined, WarningOutlined } from '@ant-design/icons';
import { useViolations, useCreateViolation, useUpdateViolation, useDeleteViolation, useUsers } from '@/hooks';
import { useAuth } from '@/context/AuthContext';
import { ViolationPermission } from '@/types/rbac.types';
import type { ViolationResponse, ViolationCreate } from '@/types/activity.types';
import dayjs from 'dayjs';
import { motion, type Variants } from 'motion/react';

// Sub-components
import ViolationFilter from './violations/components/ViolationFilter';
import ViolationTable from './violations/components/ViolationTable';
import ViolationMobileList from './violations/components/ViolationMobileList';
import ViolationFormModal from './violations/components/ViolationFormModal';
import ViolationDetailDrawer from './violations/components/ViolationDetailDrawer';

const { Title, Text } = Typography;

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

const ViolationManagementPage = () => {
    const { hasPermission } = useAuth();
    const screens = Grid.useBreakpoint();

    // Filters
    const [filterUserId, setFilterUserId] = useState<number | undefined>(undefined);
    const [filterDate, setFilterDate] = useState<dayjs.Dayjs | null>(null);

    // TanStack Query hooks
    const { data: violations = [], isLoading } = useViolations({
        userId: filterUserId,
        month: filterDate ? filterDate.month() + 1 : undefined,
        year: filterDate ? filterDate.year() : undefined,
    });
    const { data: users = [] } = useUsers();
    const createViolation = useCreateViolation();
    const updateViolation = useUpdateViolation();
    const deleteViolation = useDeleteViolation();

    // Modal Create/Edit
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingItem, setEditingItem] = useState<ViolationResponse | null>(null);
    const [form] = Form.useForm();

    // Drawer View Detail
    const [detailItem, setDetailItem] = useState<ViolationResponse | null>(null);
    const [isDetailOpen, setIsDetailOpen] = useState(false);

    const canCreate = hasPermission(ViolationPermission.CREATE);
    const canUpdate = hasPermission(ViolationPermission.UPDATE);
    const canDelete = hasPermission(ViolationPermission.DELETE);

    const handleCreateOrUpdate = async (values: any) => {
        try {
            if (editingItem) {
                const updateData = {
                    reason: values.reason,
                    date: values.date.toISOString(),
                };
                await updateViolation.mutateAsync({ id: editingItem.id, data: updateData });
                message.success('Cập nhật vi phạm thành công');
            } else {
                const formattedValues: ViolationCreate = {
                    user_ids: values.user_ids,
                    reason: values.reason,
                    date: values.date.toISOString(),
                };
                await createViolation.mutateAsync(formattedValues);
                message.success('Ghi nhận vi phạm thành công');
            }
            setIsModalOpen(false);
            form.resetFields();
        } catch (error: any) {
            message.error(error?.response?.data?.message || 'Thao tác thất bại');
        }
    };

    const handleDelete = async (id: number) => {
        try {
            await deleteViolation.mutateAsync(id);
            message.success('Xóa vi phạm thành công');
            setIsDetailOpen(false);
        } catch (error: any) {
            message.error(error?.response?.data?.message || 'Xóa thất bại');
        }
    };

    const handleOpenEdit = (item: ViolationResponse) => {
        setEditingItem(item);
        form.setFieldsValue({
            ...item,
            user_name: item.owner?.name || item.user_name || 'Unknown',
            date: dayjs(item.date)
        });
        setIsModalOpen(true);
        setIsDetailOpen(false);
    };

    const handleOpenDetail = (item: ViolationResponse) => {
        setDetailItem(item);
        setIsDetailOpen(true);
    };

    return (
        <motion.div 
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="p-4 md:p-6"
        >
            <Card 
                className={!screens.md ? "bg-transparent shadow-none border-none" : "shadow-sm border-gray-100 rounded-xl overflow-hidden"} 
                styles={{ body: { padding: !screens.md ? 0 : undefined } }}
            >
                {/* Header */}
                <motion.div variants={itemVariants} className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6 px-3 md:px-0">
                    <Space size="middle">
                        <div className="hidden md:flex w-12 h-12 rounded-xl bg-red-50 items-center justify-center text-red-500">
                            <WarningOutlined className="text-2xl" />
                        </div>
                        <div>
                            <Title level={3} className="text-xl md:text-2xl mt-4 text-red-600">Quản lý Vi phạm</Title>
                            <Text type="secondary" className="text-xs md:text-sm">Danh sách và công cụ xử lý các vi phạm</Text>
                        </div>
                    </Space>
                    {canCreate && (
                        <Button
                            type="primary"
                            icon={<PlusOutlined />}
                            onClick={() => {
                                setEditingItem(null);
                                form.resetFields();
                                form.setFieldsValue({ date: dayjs() });
                                setIsModalOpen(true);
                            }}
                            className="w-full md:w-auto bg-linear-to-r from-red-500 to-orange-500 border-none shadow-md h-10 px-6 font-semibold"
                        >
                            Thêm Vi phạm
                        </Button>
                    )}
                </motion.div>

                {/* Filter Bar */}
                <motion.div variants={itemVariants}>
                    <ViolationFilter
                        filterUserId={filterUserId}
                        setFilterUserId={setFilterUserId}
                        filterDate={filterDate}
                        setFilterDate={setFilterDate}
                        users={users}
                    />
                </motion.div>

                {/* Content Area */}
                {!screens.md ? (
                    <motion.div variants={itemVariants}>
                        <ViolationMobileList
                            violations={violations}
                            isLoading={isLoading}
                            canUpdate={canUpdate}
                            canDelete={canDelete}
                            onViewDetail={handleOpenDetail}
                            onEdit={handleOpenEdit}
                            onDelete={handleDelete}
                        />
                    </motion.div>
                ) : (
                    <motion.div variants={itemVariants}>
                        <ViolationTable
                            violations={violations}
                            isLoading={isLoading}
                            canUpdate={canUpdate}
                            canDelete={canDelete}
                            onEdit={handleOpenEdit}
                            onDelete={handleDelete}
                            onRowClick={handleOpenDetail}
                        />
                    </motion.div>
                )}
            </Card>

            {/* Modals & Drawers */}
            <ViolationFormModal
                isOpen={isModalOpen}
                onCancel={() => setIsModalOpen(false)}
                onFinish={handleCreateOrUpdate}
                editingItem={editingItem}
                loading={createViolation.isPending || updateViolation.isPending}
                users={users}
                form={form}
                isMobile={!screens.md}
            />

            <ViolationDetailDrawer
                isOpen={isDetailOpen}
                onClose={() => setIsDetailOpen(false)}
                detailItem={detailItem}
                canUpdate={canUpdate}
                canDelete={canDelete}
                onEdit={handleOpenEdit}
                onDelete={handleDelete}
                isMobile={!screens.md}
            />
        </motion.div>
    );
};

export default ViolationManagementPage;
