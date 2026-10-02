import { useState } from 'react';
import {
    Button,
    Card,
    Space,
    Table,
    Tag,
    Avatar,
    Typography,
    Grid,
    Popconfirm,
    DatePicker,
    Select,
    message,
    Tooltip,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
    PlusOutlined,
    TrophyOutlined,
    UserOutlined,
    EditOutlined,
    DeleteOutlined,
    CalendarOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import type { Dayjs } from 'dayjs';
import { motion, type Variants } from 'motion/react';
import { useAuth } from '@/features/auth';
import { BonusPointPermission } from '@/features/rbac/types/rbac.types';
import {
    useBonusPoints,
    useCreateBonusPoint,
    useUpdateBonusPoint,
    useDeleteBonusPoint,
} from '@/features/activity';
import { useUsers } from '@/features/users';
import { BonusPointModal } from '@/features/users/components/BonusPointModal';
import type { BonusPointResponse } from '@/features/activity/types/activity.types';

const { Title, Text } = Typography;
const { Option } = Select;

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

export const BonusPointManagementPage = () => {
    const { hasPermission } = useAuth();
    const screens = Grid.useBreakpoint();

    // Filters
    const [filterUserId, setFilterUserId] = useState<number | undefined>(undefined);
    const [filterDate, setFilterDate] = useState<Dayjs | null>(null);

    // Queries & Mutations
    const { data: bonusPoints = [], isLoading } = useBonusPoints({
        userId: filterUserId,
        month: filterDate ? filterDate.month() + 1 : undefined,
        year: filterDate ? filterDate.year() : undefined,
    });
    const { data: users = [] } = useUsers();

    const createBonusPoint = useCreateBonusPoint();
    const updateBonusPoint = useUpdateBonusPoint();
    const deleteBonusPoint = useDeleteBonusPoint();

    // Modal Create / Edit
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingItem, setEditingItem] = useState<BonusPointResponse | null>(null);

    const canCreate = hasPermission(BonusPointPermission.CREATE);
    const canUpdate = hasPermission(BonusPointPermission.UPDATE);
    const canDelete = hasPermission(BonusPointPermission.DELETE);

    const handleCreateOrUpdate = async (values: any) => {
        try {
            if (editingItem) {
                await updateBonusPoint.mutateAsync({
                    id: editingItem.id,
                    data: {
                        points: values.points,
                        reason: values.reason,
                        date: values.date,
                    },
                });
                message.success('Cập nhật điểm cộng thành công');
            } else {
                await createBonusPoint.mutateAsync({
                    user_ids: values.user_ids,
                    points: values.points,
                    reason: values.reason,
                    date: values.date,
                });
                message.success('Thêm điểm cộng thành công');
            }
            setIsModalOpen(false);
            setEditingItem(null);
        } catch (error: any) {
            message.error(error?.response?.data?.message || 'Thao tác thất bại');
        }
    };

    const handleDelete = async (id: number) => {
        try {
            await deleteBonusPoint.mutateAsync(id);
            message.success('Xóa điểm cộng thành công');
        } catch (error: any) {
            message.error(error?.response?.data?.message || 'Xóa thất bại');
        }
    };

    const columns: ColumnsType<BonusPointResponse> = [
        {
            title: 'Thành viên',
            key: 'user',
            width: 220,
            render: (_, record) => {
                const name = record.owner?.name || record.user?.name || `User #${record.user_id}`;
                const avatar = record.owner?.avatar_url || record.user?.avatar_url;
                return (
                    <div className="flex items-center gap-3">
                        <Avatar src={avatar} icon={<UserOutlined />} size="default" className="bg-emerald-500" />
                        <div>
                            <Text strong className="block text-gray-800 dark:text-gray-200">{name}</Text>
                            <Text type="secondary" className="text-xs">ID: {record.user_id}</Text>
                        </div>
                    </div>
                );
            },
        },
        {
            title: 'Điểm cộng',
            dataIndex: 'points',
            key: 'points',
            width: 120,
            render: (points: number) => (
                <Tag color="success" className="font-semibold text-sm px-2 py-0.5 rounded-md border-emerald-200">
                    +{points} điểm
                </Tag>
            ),
            sorter: (a, b) => a.points - b.points,
        },
        {
            title: 'Lý do ghi nhận',
            dataIndex: 'reason',
            key: 'reason',
            render: (reason: string) => (
                <Text className="text-gray-700 dark:text-gray-300 font-medium">
                    {reason || 'Không có lý do cụ thể'}
                </Text>
            ),
        },
        {
            title: 'Ngày ghi nhận',
            dataIndex: 'date',
            key: 'date',
            width: 160,
            render: (date: string) => (
                <div className="flex items-center gap-1.5 text-xs text-gray-600 dark:text-gray-400">
                    <CalendarOutlined />
                    <span>{dayjs(date).format('DD/MM/YYYY HH:mm')}</span>
                </div>
            ),
            sorter: (a, b) => dayjs(a.date).valueOf() - dayjs(b.date).valueOf(),
        },
        {
            title: 'Người tạo',
            key: 'creator',
            width: 160,
            render: (_, record) => {
                const creatorName = record.creator?.name || (record.created_by ? `User #${record.created_by}` : '-');
                return (
                    <Text type="secondary" className="text-xs">
                        {creatorName}
                    </Text>
                );
            },
        },
        ...(canUpdate || canDelete
            ? [
                  {
                      title: 'Hành động',
                      key: 'action',
                      width: 110,
                      render: (_: any, record: BonusPointResponse) => (
                          <Space size="small">
                              {canUpdate && (
                                  <Tooltip title="Chỉnh sửa">
                                      <Button
                                          type="text"
                                          size="small"
                                          icon={<EditOutlined className="text-blue-500 hover:text-blue-600" />}
                                          onClick={() => {
                                              setEditingItem(record);
                                              setIsModalOpen(true);
                                          }}
                                      />
                                  </Tooltip>
                              )}
                              {canDelete && (
                                  <Tooltip title="Xóa">
                                      <Popconfirm
                                          title="Xóa điểm cộng"
                                          description="Bạn có chắc chắn muốn xóa điểm cộng này không?"
                                          onConfirm={() => handleDelete(record.id)}
                                          okText="Xóa"
                                          cancelText="Hủy"
                                          okButtonProps={{ danger: true }}
                                      >
                                          <Button
                                              type="text"
                                              size="small"
                                              icon={<DeleteOutlined className="text-red-500 hover:text-red-600" />}
                                          />
                                      </Popconfirm>
                                  </Tooltip>
                              )}
                          </Space>
                      ),
                  },
              ]
            : []),
    ];

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
                        <div className="hidden md:flex w-12 h-12 rounded-xl bg-emerald-50 items-center justify-center text-emerald-600 shadow-sm">
                            <TrophyOutlined className="text-2xl" />
                        </div>
                        <div>
                            <Title level={3} className="text-xl md:text-2xl mt-4 text-emerald-700">Quản lý Điểm cộng</Title>
                            <Text type="secondary" className="text-xs md:text-sm">Danh sách khen thưởng và ghi nhận điểm cộng thành viên</Text>
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
                            className="w-full md:w-auto bg-gradient-to-r from-emerald-600 to-teal-600 border-none shadow-md h-10 px-6 font-semibold"
                        >
                            Thêm Điểm cộng
                        </Button>
                    )}
                </motion.div>

                {/* Filters */}
                <motion.div variants={itemVariants} className="mb-6 p-4 bg-gray-50/70 dark:bg-gray-800/40 rounded-xl border border-gray-100 dark:border-gray-800 flex flex-wrap gap-4 items-center">
                    <div className="w-full sm:w-64">
                        <Select
                            allowClear
                            showSearch
                            placeholder="Lọc theo thành viên"
                            className="w-full"
                            value={filterUserId}
                            onChange={(val) => setFilterUserId(val)}
                            optionFilterProp="children"
                            filterOption={(input, option) =>
                                String(option?.children ?? '').toLowerCase().includes(input.toLowerCase())
                            }
                        >
                            {users.map((u) => (
                                <Option key={u.id} value={u.id}>
                                    {u.name} ({u.email})
                                </Option>
                            ))}
                        </Select>
                    </div>
                    <div className="w-full sm:w-48">
                        <DatePicker
                            picker="month"
                            placeholder="Lọc theo Tháng/Năm"
                            className="w-full"
                            value={filterDate}
                            onChange={(val) => setFilterDate(val)}
                            format="MM/YYYY"
                        />
                    </div>
                    {(filterUserId !== undefined || filterDate !== null) && (
                        <Button
                            type="link"
                            onClick={() => {
                                setFilterUserId(undefined);
                                setFilterDate(null);
                            }}
                            className="p-0 text-emerald-600 text-xs"
                        >
                            Xóa bộ lọc
                        </Button>
                    )}
                </motion.div>

                {/* Table Content */}
                <motion.div variants={itemVariants}>
                    <Table
                        columns={columns}
                        dataSource={bonusPoints}
                        rowKey="id"
                        loading={isLoading}
                        pagination={{
                            pageSize: 10,
                            showSizeChanger: true,
                            showTotal: (total) => `Tổng số ${total} điểm cộng`,
                        }}
                        className="rounded-lg overflow-hidden border border-gray-100 dark:border-gray-800"
                        locale={{ emptyText: 'Chưa có ghi nhận điểm cộng nào' }}
                    />
                </motion.div>
            </Card>

            {/* Modal Create/Edit */}
            {isModalOpen && (
                <BonusPointModal
                    open={isModalOpen}
                    editingItem={editingItem}
                    initialDate={dayjs()}
                    users={users}
                    onSubmit={handleCreateOrUpdate}
                    onCancel={() => {
                        setIsModalOpen(false);
                        setEditingItem(null);
                    }}
                />
            )}
        </motion.div>
    );
};

export default BonusPointManagementPage;
