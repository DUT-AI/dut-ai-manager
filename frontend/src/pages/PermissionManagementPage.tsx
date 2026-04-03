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
    List
} from 'antd';
import {
    PlusOutlined,
    EditOutlined,
    DeleteOutlined,
    FileTextOutlined,
    CalendarOutlined,
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
    useMeetings
} from '@/hooks';
import { useAuth } from '@/context/AuthContext';
import { PermissionRequestPermission } from '@/types/rbac.types';
import type { PermissionRequestResponse } from '@/types/activity.types';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

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
                                <CalendarOutlined />
                                <span>{dayjs(record.date).format('DD/MM')}</span>
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
                                <Text type="secondary" className="text-xs flex items-center gap-1">
                                    <ClockCircleOutlined />
                                    {record.start_time ? record.start_time.substring(0, 5) : '--:--'}
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
    const { data: permissions = [], isLoading } = usePermissionRequests();
    const { data: homeworks = [] } = useHomeworks();
    const { data: meetings = [] } = useMeetings();
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
        const formattedValues: any = {
            ...values,
            date: values.date.format('YYYY-MM-DD'),
            start_time: values.start_time?.format('HH:mm:ss'),
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
            title: 'Ngày',
            dataIndex: 'date',
            key: 'date',
            render: (date: string) => (
                <Space>
                    <CalendarOutlined className="text-gray-400" />
                    <Text>{dayjs(date).format('DD/MM/YYYY')}</Text>
                </Space>
            ),
        },
        {
            title: 'Thời gian',
            key: 'time',
            render: (_: any, record: PermissionRequestResponse) => (
                <Space>
                    <ClockCircleOutlined className="text-gray-400" />
                    <Text>{record.start_time?.substring(0, 5) || '--:--'}</Text>
                </Space>
            ),
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
                                date: dayjs(record.date),
                                start_time: record.start_time ? dayjs(record.start_time, 'HH:mm:ss') : null,
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
        <div className="p-4 md:p-6">
            <Card className={!screens.md ? "bg-transparent shadow-none border-none" : "shadow-sm border-gray-100 rounded-xl overflow-hidden"} styles={{ body: { padding: !screens.md ? 0 : undefined } }}>
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6 px-3 md:px-0">
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
                </div>

                {!screens.md ? (
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
                                date: dayjs(item.date),
                                start_time: item.start_time ? dayjs(item.start_time, 'HH:mm:ss') : null,
                            });
                            setIsModalOpen(true);
                        }}
                        onDelete={handleDelete}
                    />
                ) : (
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
                                                <Option key={m.id} value={m.id}>{m.title} ({dayjs(m.date).format('DD/MM/YYYY')})</Option>
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
                            let dateLabel = "Ngày xin phép";
                            if (category === 'POSTPONE') dateLabel = "Ngày deadline mới";

                            return (
                                <Form.Item name="date" label={dateLabel} rules={[{ required: true, message: 'Vui lòng chọn ngày!' }]}>
                                    <DatePicker format="DD/MM/YYYY" className="w-full" />
                                </Form.Item>
                            );
                        }}
                    </Form.Item>

                    <Form.Item
                        noStyle
                        shouldUpdate={(prevValues, currentValues) => prevValues.category !== currentValues.category}
                    >
                        {({ getFieldValue }) => {
                            const category = getFieldValue('category');
                            if (category === 'ABSENCE' || category === 'OTHER') return null;

                            let timeLabel = "Giờ bắt đầu";
                            if (category === 'POSTPONE') timeLabel = "Giờ deadline mới";
                            if (category === 'LATE') timeLabel = "Giờ có mặt trễ nhất";

                            return (
                                <Form.Item name="start_time" label={timeLabel} rules={[{ required: true }]}>
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
                                <Descriptions.Item label="Ngày">
                                    {dayjs(detailItem.date).format('DD/MM/YYYY')}
                                </Descriptions.Item>
                                {detailItem.start_time && (
                                    <Descriptions.Item label="Thời gian">
                                        {detailItem.start_time.substring(0, 5)}
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
                                            date: dayjs(detailItem.date),
                                            start_time: detailItem.start_time ? dayjs(detailItem.start_time, 'HH:mm:ss') : null,
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
        </div>
    );
};

export default PermissionManagementPage;
