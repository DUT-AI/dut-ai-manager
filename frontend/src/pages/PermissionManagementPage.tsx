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
    useDeletePermissionRequest
} from '@/hooks';
import { useAuth } from '@/context/AuthContext';
import { PermissionRequestPermission } from '@/types/rbac.types';
import type { PermissionRequestResponse, PermissionCreate } from '@/types/activity.types';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const CATEGORY_COLORS: Record<string, string> = {
    'vắng sinh hoạt': 'volcano',
    'đi trễ sinh hoạt': 'gold',
    'tạm hoãn bài tập': 'geekblue',
    'khác': 'default',
};

const PermissionManagementPage = () => {
    const { hasPermission } = useAuth();
    const screens = Grid.useBreakpoint();

    // TanStack Query hooks
    const { data: permissions = [], isLoading } = usePermissionRequests();
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
        const formattedValues: PermissionCreate = {
            ...values,
            date: values.date.format('YYYY-MM-DD'),
            start_time: values.start_time.format('HH:mm:ss'),
            end_time: values.end_time.format('HH:mm:ss'),
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
                        src={record.user_avatar}
                        icon={<UserOutlined />}
                        className="bg-linear-to-br from-indigo-500 to-purple-500 shadow-sm"
                        size="small"
                    />
                    <div>
                        <Text strong className="block">
                            {record.user_name || (record.created_by ? `#${record.created_by}` : 'N/A')}
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
                    {category.toUpperCase()}
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
                    <Text>{record.start_time.substring(0, 5)} - {record.end_time.substring(0, 5)}</Text>
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
                                start_time: dayjs(record.start_time, 'HH:mm:ss'),
                                end_time: dayjs(record.end_time, 'HH:mm:ss'),
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

    const MobileListView = () => (
        <div className="mt-4 px-3">
            <List
                dataSource={permissions}
                loading={isLoading}
                split={false}
                renderItem={(record) => (
                    <List.Item className="px-2 !mb-4 !border-0">
                        <Card
                            className="w-full shadow-sm border-gray-100 overflow-hidden"
                            styles={{ body: { padding: '16px' } }}
                            onClick={() => {
                                setDetailItem(record);
                                setIsDetailOpen(true);
                            }}
                        >
                            <div className="flex items-center justify-between mb-4">
                                <Tag color={CATEGORY_COLORS[record.category.toLowerCase()] || 'default'} className="m-0 font-medium px-3 rounded-full">
                                    {record.category.toUpperCase()}
                                </Tag>
                                <Space className="text-gray-400 text-xs">
                                    <CalendarOutlined />
                                    <span>{dayjs(record.date).format('DD/MM')}</span>
                                </Space>
                            </div>

                            <div className="flex items-center gap-3 mb-4">
                                <Avatar
                                    src={record.user_avatar}
                                    icon={<UserOutlined />}
                                    className="bg-linear-to-br from-indigo-500 to-purple-500 shadow-sm shrink-0"
                                    size="large"
                                />
                                <div className="flex flex-col min-w-0 flex-1">
                                    <Text strong className="truncate text-base">
                                        {record.user_name || (record.created_by ? `#${record.created_by}` : 'N/A')}
                                    </Text>
                                    <Text type="secondary" className="text-xs flex items-center gap-1">
                                        <ClockCircleOutlined />
                                        {record.start_time.substring(0, 5)} - {record.end_time.substring(0, 5)}
                                    </Text>
                                </div>
                            </div>

                            <div className="flex justify-end items-center pt-3 border-t border-gray-50 bg-gray-50 -mx-4 -mb-4 px-4 py-3 gap-2" onClick={(e) => e.stopPropagation()}>
                                <Button
                                    icon={<EditOutlined />}
                                    size="small"
                                    onClick={() => {
                                        setEditingItem(record);
                                        form.setFieldsValue({
                                            ...record,
                                            date: dayjs(record.date),
                                            start_time: dayjs(record.start_time, 'HH:mm:ss'),
                                            end_time: dayjs(record.end_time, 'HH:mm:ss'),
                                        });
                                        setIsModalOpen(true);
                                    }}
                                    disabled={!canUpdate}
                                >
                                    Sửa
                                </Button>
                                <Popconfirm
                                    title="Xóa đơn này?"
                                    onConfirm={() => handleDelete(record.id)}
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
                                    category: 'vắng sinh hoạt'
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
                    <MobileListView />
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
                        <Select>
                            <Option value="vắng sinh hoạt">Vắng sinh hoạt</Option>
                            <Option value="đi trễ sinh hoạt">Đi trễ sinh hoạt</Option>
                            <Option value="tạm hoãn bài tập">Tạm hoãn bài tập</Option>
                            <Option value="khác">Khác</Option>
                        </Select>
                    </Form.Item>

                    <Form.Item name="date" label="Ngày xin phép" rules={[{ required: true, message: 'Vui lòng chọn ngày!' }]}>
                        <DatePicker format="DD/MM/YYYY" className="w-full" />
                    </Form.Item>

                    <div className="grid grid-cols-2 gap-4">
                        <Form.Item name="start_time" label="Giờ bắt đầu" rules={[{ required: true }]}>
                            <TimePicker format="HH:mm" className="w-full" />
                        </Form.Item>
                        <Form.Item name="end_time" label="Giờ kết thúc" rules={[{ required: true }]}>
                            <TimePicker format="HH:mm" className="w-full" />
                        </Form.Item>
                    </div>

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
                        <div className="flex-1">
                            <Descriptions column={1} bordered size="small" className="mb-6">
                                <Descriptions.Item label="Người tạo">
                                    <Space>
                                        <UserOutlined />
                                        <Text strong>{detailItem.user_name || `#${detailItem.created_by}`}</Text>
                                    </Space>
                                </Descriptions.Item>
                                <Descriptions.Item label="Loại phép">
                                    <Tag color={CATEGORY_COLORS[detailItem.category.toLowerCase()] || 'default'}>{detailItem.category.toUpperCase()}</Tag>
                                </Descriptions.Item>
                                <Descriptions.Item label="Thời gian">
                                    {dayjs(detailItem.date).format('DD/MM/YYYY')} <br />
                                    {detailItem.start_time.substring(0, 5)} - {detailItem.end_time.substring(0, 5)}
                                </Descriptions.Item>
                            </Descriptions>

                            <Divider style={{ textAlign: 'left' }} className="!mb-4">Nội dung / Lý do</Divider>
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
                                            start_time: dayjs(detailItem.start_time, 'HH:mm:ss'),
                                            end_time: dayjs(detailItem.end_time, 'HH:mm:ss'),
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
