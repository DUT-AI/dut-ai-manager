import { useState, useMemo } from 'react';
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
    TeamOutlined,
    ClockCircleOutlined,
    AppstoreOutlined,
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
import {
    BonusPointType,
    BONUS_POINT_TYPE_LABELS,
    type BonusPointResponse,
} from '@/features/activity/types/activity.types';

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
    const [filterType, setFilterType] = useState<string | undefined>(undefined);
    const [filterDate, setFilterDate] = useState<Dayjs | null>(null);

    // Queries & Mutations
    const { data: bonusPoints = [], isLoading } = useBonusPoints({
        userId: filterUserId,
        type: filterType,
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

    // Summary statistics (2 types: CLUB_ACTIVITY and OTHER)
    const stats = useMemo(() => {
        let totalPoints = 0;
        let clubPoints = 0;
        let clubCount = 0;
        let otherPoints = 0;
        let otherCount = 0;

        bonusPoints.forEach((item) => {
            const pts = item.points || 0;
            totalPoints += pts;
            const t = item.type || (item.reason?.toLowerCase().includes('hoạt động tại clb') || item.reason?.toLowerCase().includes('lab') ? BonusPointType.CLUB_ACTIVITY : BonusPointType.OTHER);

            if (t === BonusPointType.CLUB_ACTIVITY) {
                clubPoints += pts;
                clubCount += 1;
            } else {
                otherPoints += pts;
                otherCount += 1;
            }
        });

        return {
            totalPoints,
            totalCount: bonusPoints.length,
            clubPoints,
            clubCount,
            otherPoints,
            otherCount,
        };
    }, [bonusPoints]);

    const handleCreateOrUpdate = async (values: any) => {
        try {
            if (editingItem) {
                await updateBonusPoint.mutateAsync({
                    id: editingItem.id,
                    data: {
                        points: values.points,
                        type: values.type,
                        reason: values.reason,
                        date: values.date,
                    },
                });
                message.success('Cập nhật điểm cộng thành công');
            } else {
                await createBonusPoint.mutateAsync({
                    user_ids: values.user_ids,
                    points: values.points,
                    type: values.type,
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
                const name = record.owner?.name || (record as any).user?.name || `User #${record.user_id}`;
                const avatar = record.owner?.avatar_url || (record as any).user?.avatar_url;
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
            title: 'Phân loại',
            dataIndex: 'type',
            key: 'type',
            width: 170,
            render: (type: string, record: BonusPointResponse) => {
                const isClubActivity = type === BonusPointType.CLUB_ACTIVITY || (!type && (record.reason?.toLowerCase().includes('hoạt động tại clb') || record.reason?.toLowerCase().includes('clb:') || record.reason?.toLowerCase().includes('lab')));
                if (isClubActivity) {
                    return (
                        <Tag color="blue" className="px-2.5 py-1 rounded-md text-xs font-medium inline-flex items-center gap-1.5 border-blue-200">
                            <ClockCircleOutlined />
                            {BONUS_POINT_TYPE_LABELS[BonusPointType.CLUB_ACTIVITY]?.label || 'Hoạt động CLB'}
                        </Tag>
                    );
                }
                return (
                    <Tag color="purple" className="px-2.5 py-1 rounded-md text-xs font-medium inline-flex items-center gap-1.5 border-purple-200">
                        <TrophyOutlined />
                        {BONUS_POINT_TYPE_LABELS[BonusPointType.OTHER]?.label || 'Điểm cộng khác'}
                    </Tag>
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
                const creatorName = record.creator?.name || ((record as any).created_by ? `User #${(record as any).created_by}` : '-');
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
            {/* Classification Stats Cards (3 Cards) */}
            <motion.div variants={itemVariants} className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
                <Card className="rounded-xl border border-emerald-100 dark:border-emerald-950/40 bg-gradient-to-br from-emerald-50/50 to-white dark:from-emerald-950/20 dark:to-gray-900 shadow-sm">
                    <div className="flex items-center justify-between">
                        <div>
                            <Text type="secondary" className="text-xs uppercase tracking-wider font-semibold">Tổng điểm cộng</Text>
                            <div className="text-2xl font-bold text-emerald-700 dark:text-emerald-400 mt-1">+{stats.totalPoints}</div>
                            <Text type="secondary" className="text-xs">{stats.totalCount} lượt ghi nhận</Text>
                        </div>
                        <div className="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-900/50 text-emerald-600 flex items-center justify-center text-lg">
                            <TrophyOutlined />
                        </div>
                    </div>
                </Card>

                <Card className="rounded-xl border border-blue-100 dark:border-blue-950/40 bg-gradient-to-br from-blue-50/50 to-white dark:from-blue-950/20 dark:to-gray-900 shadow-sm">
                    <div className="flex items-center justify-between">
                        <div>
                            <Text type="secondary" className="text-xs uppercase tracking-wider font-semibold">Hoạt động tại CLB</Text>
                            <div className="text-2xl font-bold text-blue-700 dark:text-blue-400 mt-1">+{stats.clubPoints}</div>
                            <Text type="secondary" className="text-xs">{stats.clubCount} lượt rèn luyện</Text>
                        </div>
                        <div className="w-10 h-10 rounded-xl bg-blue-100 dark:bg-blue-900/50 text-blue-600 flex items-center justify-center text-lg">
                            <ClockCircleOutlined />
                        </div>
                    </div>
                </Card>

                <Card className="rounded-xl border border-purple-100 dark:border-purple-950/40 bg-gradient-to-br from-purple-50/50 to-white dark:from-purple-950/20 dark:to-gray-900 shadow-sm">
                    <div className="flex items-center justify-between">
                        <div>
                            <Text type="secondary" className="text-xs uppercase tracking-wider font-semibold">Điểm cộng khác</Text>
                            <div className="text-2xl font-bold text-purple-700 dark:text-purple-400 mt-1">+{stats.otherPoints}</div>
                            <Text type="secondary" className="text-xs">{stats.otherCount} lượt khác (sinh hoạt, thưởng)</Text>
                        </div>
                        <div className="w-10 h-10 rounded-xl bg-purple-100 dark:bg-purple-900/50 text-purple-600 flex items-center justify-center text-lg">
                            <TrophyOutlined />
                        </div>
                    </div>
                </Card>
            </motion.div>

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
                            <Text type="secondary" className="text-xs md:text-sm">Danh sách khen thưởng và phân loại điểm cộng thành viên</Text>
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
                    <div className="w-full sm:w-60">
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

                    <div className="w-full sm:w-52">
                        <Select
                            allowClear
                            placeholder="Lọc loại điểm cộng"
                            className="w-full"
                            value={filterType}
                            onChange={(val) => setFilterType(val)}
                        >
                            <Option value={BonusPointType.CLUB_ACTIVITY}>
                                <span className="flex items-center gap-2">
                                    <ClockCircleOutlined className="text-blue-500" />
                                    {BONUS_POINT_TYPE_LABELS[BonusPointType.CLUB_ACTIVITY]?.label}
                                </span>
                            </Option>
                            <Option value={BonusPointType.OTHER}>
                                <span className="flex items-center gap-2">
                                    <TrophyOutlined className="text-purple-500" />
                                    {BONUS_POINT_TYPE_LABELS[BonusPointType.OTHER]?.label}
                                </span>
                            </Option>
                        </Select>
                    </div>

                    <div className="w-full sm:w-44">
                        <DatePicker
                            picker="month"
                            placeholder="Lọc theo Tháng/Năm"
                            className="w-full"
                            value={filterDate}
                            onChange={(val) => setFilterDate(val)}
                            format="MM/YYYY"
                        />
                    </div>

                    {(filterUserId !== undefined || filterType !== undefined || filterDate !== null) && (
                        <Button
                            type="link"
                            onClick={() => {
                                setFilterUserId(undefined);
                                setFilterType(undefined);
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
