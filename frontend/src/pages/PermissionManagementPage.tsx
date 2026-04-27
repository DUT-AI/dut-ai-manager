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
    Select,
    DatePicker,
    TimePicker,
    Drawer,
    Descriptions,
    Divider,
    Avatar,
    Grid,
    List,
    Row,
    Col
} from 'antd';
import {
    PlusOutlined,
    EditOutlined,
    DeleteOutlined,
    FileTextOutlined,
    UserOutlined,
    ClockCircleOutlined,
    InfoCircleOutlined
} from '@ant-design/icons';
import {
    usePermissionRequests,
    useCreatePermissionRequest,
    useUpdatePermissionRequest,
    useDeletePermissionRequest,
    useHomeworks,
    useMeetings,
    useUsers
} from '@/hooks';
import { useAuth } from '@/context/AuthContext';
import { PermissionRequestPermission } from '@/types/rbac.types';
import type { PermissionRequestResponse } from '@/types/activity.types';
import dayjs from 'dayjs';
import { motion, type Variants } from 'motion/react';

const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

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

interface MobileListViewProps {
    permissions: PermissionRequestResponse[];
    isLoading: boolean;
    canUpdate: boolean;
    canDelete: boolean;
    onViewDetail: (item: PermissionRequestResponse) => void;
    onEdit: (item: PermissionRequestResponse) => void;
    onDelete: (id: number) => void;
}

const CATEGORY_COLORS: Record<string, string> = {
    'absence': 'volcano',
    'late': 'gold',
    'postpone': 'geekblue',
    'other': 'default',
};

const CATEGORY_LABELS: Record<string, string> = {
    'absence': 'Vắng sinh hoạt',
    'late': 'Đi trễ sinh hoạt',
    'postpone': 'Tạm hoãn bài tập',
    'other': 'Khác',
};

const MobileListView = ({ permissions, isLoading, canUpdate, canDelete, onViewDetail, onEdit, onDelete }: MobileListViewProps) => (
    <div className="mt-4 px-3">
        <List
            dataSource={permissions}
            loading={isLoading}
            split={false}
            renderItem={(record) => (
                <List.Item className="px-2 mb-4! border-0!">
                    <Card
                        className="w-full shadow-sm border-gray-100 overflow-hidden"
                        styles={{ body: { padding: '16px' } }}
                        onClick={() => onViewDetail(record)}
                    >
                        <div className="flex items-center justify-between mb-4">
                            <Tag color={CATEGORY_COLORS[record.category.toLowerCase()] || 'default'} className="m-0 font-medium px-3 rounded-full">
                                {CATEGORY_LABELS[record.category.toLowerCase()] || record.category}
                            </Tag>
                            <Space className="text-gray-400 text-xs">
                                <InfoCircleOutlined />
                                <span className="max-w-[120px] truncate">
                                    {record.category === 'POSTPONE' ? record.homework?.title : record.meeting?.title || '--'}
                                </span>
                            </Space>
                        </div>

                        <div className="flex items-center gap-3 mb-4">
                            <Avatar
                                src={record.user?.avatar_url || record.user_avatar}
                                icon={<UserOutlined />}
                                className="bg-linear-to-br from-indigo-500 to-purple-500 shadow-sm shrink-0"
                                size="large"
                            />
                            <div className="flex flex-col min-w-0 flex-1">
                                <Text strong className="truncate text-base">
                                    {record.user?.name || record.user_name || (record.created_by ? `#${record.created_by}` : 'N/A')}
                                </Text>
                            </div>
                        </div>

                        <div role="presentation" className="flex justify-end items-center pt-3 border-t border-gray-50 bg-gray-50 -mx-4 -mb-4 px-4 py-3 gap-2" onClick={(e) => e.stopPropagation()} onKeyDown={(e) => e.stopPropagation()}>
                            <Button
                                icon={<EditOutlined />}
                                size="small"
                                onClick={() => onEdit(record)}
                                disabled={!canUpdate}
                            >
                                Sửa
                            </Button>
                            <Popconfirm
                                title="Xóa đơn này?"
                                onConfirm={() => onDelete(record.id)}
                                disabled={!canDelete}
                                okText="Xóa"
                                cancelText="Hủy"
                            >
                                <Button icon={<DeleteOutlined />} size="small" danger disabled={!canDelete}>Xóa</Button>
                            </Popconfirm>
                        </div>
                    </Card>
                </List.Item>
            )}
        />
    </div>
);

const PermissionManagementPage = () => {
    const { hasPermission } = useAuth();
    const screens = Grid.useBreakpoint();

    // TanStack Query hooks
    // Filter states
    const [filterDate, setFilterDate] = useState<dayjs.Dayjs | null>(null);
    const [filterMonth, setFilterMonth] = useState<number | undefined>();
    const [filterYear, setFilterYear] = useState<number | undefined>();
    const [filterCategory, setFilterCategory] = useState<string | undefined>();
    const [filterUserId, setFilterUserId] = useState<number | undefined>();

    // TanStack Query hooks
    const { data: permissions = [], isLoading } = usePermissionRequests({
        month: filterMonth,
        year: filterYear,
        category: filterCategory,
        userId: filterUserId
    });
    const { data: homeworks = [] } = useHomeworks();
    const { data: meetings = [] } = useMeetings();
    const { data: usersData = [] } = useUsers();
    // Wrap users data as it might be an object with .data property depending on API
    const users = Array.isArray(usersData) ? usersData : (usersData as any)?.data || [];

    const createPermission = useCreatePermissionRequest();
    const updatePermission = useUpdatePermissionRequest();
    const deletePermission = useDeletePermissionRequest();

    // Modal Create/Edit
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingItem, setEditingItem] = useState<PermissionRequestResponse | null>(null);
    const [form] = Form.useForm();

    // Drawer View Detail
    const [detailItem, setDetailItem] = useState<PermissionRequestResponse | null>(null);
    const [isDetailOpen, setIsDetailOpen] = useState(false);

    const canCreate = hasPermission(PermissionRequestPermission.CREATE);
    const canUpdate = hasPermission(PermissionRequestPermission.UPDATE);
    const canDelete = hasPermission(PermissionRequestPermission.DELETE);

    const handleCreateOrUpdate = async (values: any) => {
        let finalStartTime = undefined;
        if (values.start_time) {
            if (values.category === 'POSTPONE') {
                finalStartTime = values.start_time.format('YYYY-MM-DDTHH:mm:ss');
            } else if (values.category === 'LATE' && values.meeting_id) {
                const meeting = meetings.find((m: any) => m.id === values.meeting_id);
                if (meeting && meeting.start_time) {
                    const dateStr = dayjs(meeting.start_time).format('YYYY-MM-DD');
                    const timeStr = values.start_time.format('HH:mm:ss');
                    finalStartTime = `${dateStr}T${timeStr}`;
                } else {
                    finalStartTime = values.start_time.format('YYYY-MM-DDTHH:mm:ss');
                }
            } else {
                finalStartTime = values.start_time.format('YYYY-MM-DDTHH:mm:ss');
            }
        }

        const formattedValues: any = {
            ...values,
            start_time: finalStartTime,
        };

        try {
            if (editingItem) {
                await updatePermission.mutateAsync({ id: editingItem.id, data: formattedValues });
                message.success('Permission request updated successfully');
            } else {
                await createPermission.mutateAsync(formattedValues);
                message.success('Permission request created successfully');
            }
            setIsModalOpen(false);
            form.resetFields();
        } catch (error: any) {
            message.error(error?.response?.data?.message || 'Operation failed');
        }
    };

    const handleDelete = async (id: number) => {
        try {
            await deletePermission.mutateAsync(id);
            message.success('Permission request deleted successfully');
            setIsDetailOpen(false);
        } catch (error: any) {
            message.error(error?.response?.data?.message || 'Delete failed');
        }
    };

    const columns = [
        {
            title: 'Người tạo',
            key: 'creator',
            render: (_: any, record: PermissionRequestResponse) => (
                <Space>
                    <Avatar
                        src={record.user?.avatar_url || record.user_avatar}
                        icon={<UserOutlined />}
                        className="bg-linear-to-br from-indigo-500 to-purple-500 shadow-sm"
                        size="small"
                    />
                    <div>
                        <Text strong className="block">
                            {record.user?.name || record.user_name || (record.created_by ? `#${record.created_by}` : 'N/A')}
                        </Text>
                    </div>
                </Space>
            ),
        },
        {
            title: 'Loại phép',
            dataIndex: 'category',
            key: 'category',
            render: (category: string) => (
                <Tag color={CATEGORY_COLORS[category.toLowerCase()] || 'default'} className="font-medium px-3 rounded-full">
                    {CATEGORY_LABELS[category.toLowerCase()] || category}
                </Tag>
            ),
        },
        {
            title: 'Mục tiêu',
            key: 'target',
            render: (_: any, record: PermissionRequestResponse) => {
                if (record.category === 'POSTPONE' && record.homework) {
                    return (
                        <Space>
                            <FileTextOutlined className="text-indigo-400" />
                            <Text strong className="text-indigo-600">{record.homework.title}</Text>
                        </Space>
                    );
                }
                if ((record.category === 'ABSENCE' || record.category === 'LATE') && record.meeting) {
                    return (
                        <Space>
                            <ClockCircleOutlined className="text-purple-400" />
                            <Text strong className="text-purple-600">{record.meeting.title}</Text>
                        </Space>
                    );
                }
                return <Text type="secondary">--</Text>;
            },
        },
        {
            title: 'Thao tác',
            key: 'actions',
            width: 120,
            render: (_: any, record: PermissionRequestResponse) => (
                <Space onClick={(e) => e.stopPropagation()}>
                    <Button
                        icon={<EditOutlined />}
                        size="small"
                        onClick={() => {
                            setEditingItem(record);
                            form.setFieldsValue({
                                ...record,
                                start_time: record.start_time ? dayjs(record.start_time) : null,
                            });
                            setIsModalOpen(true);
                        }}
                        disabled={!canUpdate}
                    />
                    <Popconfirm
                        title="Xóa đơn này?"
                        onConfirm={() => handleDelete(record.id)}
                        disabled={!canDelete}
                        okText="Xóa"
                        cancelText="Hủy"
                    >
                        <Button icon={<DeleteOutlined />} size="small" danger disabled={!canDelete} />
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    return (
        <motion.div 
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="p-4 md:p-6"
        >
            <Card className={!screens.md ? "bg-transparent shadow-none border-none" : "shadow-sm border-gray-100 rounded-xl overflow-hidden"} styles={{ body: { padding: !screens.md ? 0 : undefined } }}>
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
                                form.resetFields();
                                form.setFieldsValue({
                                    date: dayjs(),
                                    category: 'ABSENCE'
                                });
                                setIsModalOpen(true);
                            }}
                            className="w-full md:w-auto bg-linear-to-r from-indigo-500 to-purple-600 border-none shadow-md h-10 px-6 font-semibold"
                        >
                            Tạo Đơn mới
                        </Button>
                    )}
                </motion.div>

                <motion.div variants={itemVariants} className="bg-gray-50/50 p-4 rounded-xl mb-6 border border-gray-100">
                    <Row gutter={[16, 16]} align="middle">
                        <Col xs={24} sm={12} md={6}>
                            <DatePicker
                                picker="month"
                                className="w-full h-10 rounded-lg"
                                placeholder="Lọc theo tháng năm"
                                format="MM/YYYY"
                                value={filterDate}
                                onChange={(date) => {
                                    setFilterDate(date);
                                    setFilterMonth(date ? date.month() + 1 : undefined);
                                    setFilterYear(date ? date.year() : undefined);
                                }}
                            />
                        </Col>
                        <Col xs={24} sm={12} md={6}>
                            <Select
                                className="w-full h-10 rounded-lg custom-select"
                                placeholder="Loại đơn xin phép"
                                allowClear
                                value={filterCategory}
                                onChange={(val) => setFilterCategory(val)}
                            >
                                <Option value="ABSENCE">Vắng sinh hoạt</Option>
                                <Option value="LATE">Đi trễ sinh hoạt</Option>
                                <Option value="POSTPONE">Tạm hoãn bài tập</Option>
                                <Option value="OTHER">Khác</Option>
                            </Select>
                        </Col>
                        <Col xs={24} sm={12} md={6}>
                            <Select
                                showSearch
                                className="w-full h-10 rounded-lg"
                                placeholder="Lọc theo User"
                                allowClear
                                value={filterUserId}
                                optionFilterProp="label"
                                onChange={(val) => setFilterUserId(val)}
                                options={users.map((u: any) => ({
                                    label: u.name,
                                    value: u.id
                                }))}
                            />
                        </Col>
                        <Col xs={24} sm={12} md={6}>
                            <Button 
                                className="w-full h-10 rounded-lg" 
                                ghost
                                type="primary"
                                onClick={() => {
                                    setFilterDate(null);
                                    setFilterMonth(undefined);
                                    setFilterYear(undefined);
                                    setFilterCategory(undefined);
                                    setFilterUserId(undefined);
                                }}
                            >
                                Đặt lại bộ lọc
                            </Button>
                        </Col>
                    </Row>
                </motion.div>

                {!screens.md ? (
                    <motion.div variants={itemVariants}>
                        <MobileListView
                            permissions={permissions}
                            isLoading={isLoading}
                            canUpdate={canUpdate}
                            canDelete={canDelete}
                            onViewDetail={(item) => { setDetailItem(item); setIsDetailOpen(true); }}
                            onEdit={(item) => {
                                setEditingItem(item);
                                form.setFieldsValue({
                                    ...item,
                                    start_time: item.start_time ? dayjs(item.start_time) : null,
                                });
                                setIsModalOpen(true);
                            }}
                            onDelete={handleDelete}
                        />
                    </motion.div>
                ) : (
                    <motion.div variants={itemVariants}>
                        <Table
                            columns={columns}
                            dataSource={permissions}
                            rowKey="id"
                            loading={isLoading}
                            className="border border-gray-100 rounded-lg custom-table cursor-pointer"
                            pagination={{ pageSize: 10 }}
                            onRow={(record) => ({
                                onClick: () => {
                                    setDetailItem(record);
                                    setIsDetailOpen(true);
                                },
                                style: { cursor: 'pointer' }
                            })}
                        />
                    </motion.div>
                )}
            </Card>

            {/* Create/Edit Modal */}
            <Modal
                title={editingItem ? 'Chỉnh sửa Đơn xin phép' : 'Tạo Đơn xin phép mới'}
                open={isModalOpen}
                onCancel={() => setIsModalOpen(false)}
                onOk={() => form.submit()}
                centered
                confirmLoading={createPermission.isPending || updatePermission.isPending}
                destroyOnHidden
                okText={editingItem ? 'Lưu thay đổi' : 'Gửi đơn'}
                cancelText="Hủy"
                width={screens.md ? 500 : '100%'}
            >
                <Form form={form} layout="vertical" onFinish={handleCreateOrUpdate} className="mt-6">
                    <Form.Item name="category" label="Loại đơn" rules={[{ required: true }]}>
                        <Select onChange={() => form.setFieldsValue({ homework_id: undefined, meeting_id: undefined })}>
                            <Option value="ABSENCE">Vắng sinh hoạt</Option>
                            <Option value="LATE">Đi trễ sinh hoạt</Option>
                            <Option value="POSTPONE">Tạm hoãn bài tập</Option>
                            <Option value="OTHER">Khác</Option>
                        </Select>
                    </Form.Item>

                    <Form.Item
                        noStyle
                        shouldUpdate={(prevValues, currentValues) => prevValues.category !== currentValues.category}
                    >
                        {({ getFieldValue }) => {
                            const category = getFieldValue('category');
                            if (category === 'POSTPONE') {
                                return (
                                    <Form.Item name="homework_id" label="Bài tập" rules={[{ required: true, message: 'Vui lòng chọn bài tập!' }]}>
                                        <Select placeholder="Chọn bài tập">
                                            {(homeworks || []).map((hw: any) => (
                                                <Option key={hw.id} value={hw.id}>{hw.title}</Option>
                                            ))}
                                        </Select>
                                    </Form.Item>
                                );
                            }
                            if (category === 'ABSENCE' || category === 'LATE') {
                                return (
                                    <Form.Item name="meeting_id" label="Buổi sinh hoạt" rules={[{ required: true, message: 'Vui lòng chọn buổi sinh hoạt!' }]}>
                                        <Select placeholder="Chọn buổi sinh hoạt">
                                            {(meetings || []).map((m: any) => (
                                                <Option key={m.id} value={m.id}>{m.title} ({dayjs(m.start_time).format('DD/MM/YYYY')})</Option>
                                            ))}
                                        </Select>
                                    </Form.Item>
                                );
                            }
                            return null;
                        }}
                    </Form.Item>


                    <Form.Item
                        noStyle
                        shouldUpdate={(prevValues, currentValues) => prevValues.category !== currentValues.category}
                    >
                        {({ getFieldValue }) => {
                            const category = getFieldValue('category');
                            if (category === 'ABSENCE' || category === 'OTHER') return null;

                            if (category === 'POSTPONE') {
                                return (
                                    <Form.Item name="start_time" label="Deadline mới (ngày và giờ)" rules={[{ required: true }]}>
                                        <DatePicker showTime format="DD/MM/YYYY HH:mm" className="w-full" placeholder="Chọn ngày và giờ" />
                                    </Form.Item>
                                );
                            }
                            if (category === 'LATE') {
                                return (
                                    <Form.Item name="start_time" label="Giờ có mặt trễ nhất" rules={[{ required: true }]}>
                                        <TimePicker format="HH:mm" className="w-full" />
                                    </Form.Item>
                                );
                            }

                            return (
                                <Form.Item name="start_time" label="Giờ bắt đầu" rules={[{ required: true }]}>
                                    <TimePicker format="HH:mm" className="w-full" />
                                </Form.Item>
                            );
                        }}
                    </Form.Item>

                    <Form.Item name="note" label="Lý do/Ghi chú" rules={[{ required: true, message: 'Vui lòng nhập lý do!' }]}>
                        <TextArea rows={4} placeholder="Mô tả chi tiết lý do..." />
                    </Form.Item>
                </Form>
            </Modal>

            {/* Detail Drawer */}
            <Drawer
                title={
                    <Space>
                        <InfoCircleOutlined className="text-indigo-500" />
                        <span>Chi tiết Đơn xin phép</span>
                    </Space>
                }
                placement="right"
                onClose={() => setIsDetailOpen(false)}
                open={isDetailOpen}
                width={screens.md ? 500 : '100%'}
            >
                {detailItem && (
                    <div className="flex flex-col h-full">
                        <div className="flex-1 overflow-y-auto px-1">
                            <Descriptions column={1} bordered size="small" className="mb-6 bg-white rounded-lg shadow-xs overflow-hidden">
                                <Descriptions.Item label="Người tạo">
                                    <Space>
                                        <Avatar size="small" src={detailItem.user?.avatar_url || detailItem.user_avatar} icon={<UserOutlined />} />
                                        <Text strong>{detailItem.user?.name || detailItem.user_name || `#${detailItem.created_by}`}</Text>
                                    </Space>
                                </Descriptions.Item>
                                <Descriptions.Item label="Loại phép">
                                    <Tag color={CATEGORY_COLORS[detailItem.category.toLowerCase()] || 'default'} className="rounded-full px-3">
                                        {CATEGORY_LABELS[detailItem.category.toLowerCase()] || detailItem.category}
                                    </Tag>
                                </Descriptions.Item>
                                {detailItem.start_time && (
                                    <Descriptions.Item label="Thời gian">
                                        {dayjs(detailItem.start_time).format('DD/MM/YYYY HH:mm')}
                                    </Descriptions.Item>
                                )}
                            </Descriptions>

                            {(detailItem.homework || detailItem.meeting) && (
                                <>
                                    <Divider style={{ textAlign: 'left' }} className="mb-4!">Liên quan</Divider>
                                    <div className="mb-6">
                                        {detailItem.homework && (
                                            <Card size="small" className="bg-indigo-50/30 border-indigo-100 rounded-lg">
                                                <Title level={5} className="mb-1! text-indigo-700">
                                                    <Space><FileTextOutlined /> {detailItem.homework.title}</Space>
                                                </Title>
                                                <Text type="secondary" className="text-xs">Deadline: {dayjs(detailItem.homework.deadline).format('DD/MM/YYYY HH:mm')}</Text>
                                            </Card>
                                        )}
                                        {detailItem.meeting && (
                                            <Card size="small" className="bg-purple-50/30 border-purple-100 rounded-lg">
                                                <Title level={5} className="mb-1! text-purple-700">
                                                    <Space><ClockCircleOutlined /> {detailItem.meeting.title}</Space>
                                                </Title>
                                                <Text type="secondary" className="text-xs">Ngày: {dayjs(detailItem.meeting.start_time).format('DD/MM/YYYY')}</Text>
                                            </Card>
                                        )}
                                    </div>
                                </>
                            )}

                            <Divider style={{ textAlign: 'left' }} className="mb-4!">Nội dung / Lý do</Divider>
                            <div className="bg-gray-50 p-4 rounded-lg border border-gray-100 text-gray-700 whitespace-pre-wrap">
                                {detailItem.note}
                            </div>

                            <Divider style={{ textAlign: 'left' }}>Thông tin hệ thống</Divider>
                            <Descriptions column={1} size="small" className="text-gray-500">
                                <Descriptions.Item label="Ngày tạo">
                                    {dayjs(detailItem.created_at).format('DD/MM/YYYY HH:mm:ss')}
                                </Descriptions.Item>
                                {detailItem.updated_at !== detailItem.created_at && (
                                    <Descriptions.Item label="Cập nhật lần cuối">
                                        {dayjs(detailItem.updated_at).format('DD/MM/YYYY HH:mm:ss')}
                                    </Descriptions.Item>
                                )}
                                {detailItem.creator_name && (
                                    <Descriptions.Item label="Created by">
                                        {detailItem.creator_name}
                                    </Descriptions.Item>
                                )}
                                {detailItem.updater_name && (
                                    <Descriptions.Item label="Updated by">
                                        {detailItem.updater_name}
                                    </Descriptions.Item>
                                )}
                            </Descriptions>
                        </div>

                        <div className="pt-4 border-t border-gray-100 flex justify-end gap-2">
                            {canUpdate && (
                                <Button
                                    icon={<EditOutlined />}
                                    onClick={() => {
                                        setEditingItem(detailItem);
                                        form.setFieldsValue({
                                            ...detailItem,
                                            start_time: detailItem.start_time ? dayjs(detailItem.start_time) : null,
                                        });
                                        setIsModalOpen(true);
                                        setIsDetailOpen(false);
                                    }}
                                >
                                    Chỉnh sửa
                                </Button>
                            )}
                            {canDelete && (
                                <Popconfirm
                                    title="Xóa đơn này?"
                                    onConfirm={() => handleDelete(detailItem.id)}
                                    okText="Xóa"
                                    cancelText="Hủy"
                                >
                                    <Button danger icon={<DeleteOutlined />}>Xóa đơn</Button>
                                </Popconfirm>
                            )}
                        </div>
                    </div>
                )}
            </Drawer>
        </motion.div>
    );
};

export default PermissionManagementPage;
