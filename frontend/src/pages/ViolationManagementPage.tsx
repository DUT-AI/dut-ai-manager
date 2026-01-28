import { useState } from 'react';
import {
    Table,
    Button,
    Card,
    Space,
    Modal,
    Form,
    Input,
    message,
    Popconfirm,
    Typography,
    Select,
    DatePicker,
    Drawer,
    Descriptions,
    Divider,
    Avatar
} from 'antd';
import {
    PlusOutlined,
    EditOutlined,
    DeleteOutlined,
    WarningOutlined,
    CalendarOutlined,
    UserOutlined,
    InfoCircleOutlined
} from '@ant-design/icons';
import { useViolations, useCreateViolation, useUpdateViolation, useDeleteViolation, useUsers } from '@/hooks';
import { useAuth } from '@/context/AuthContext';
import { ViolationPermission } from '@/types/rbac.types';
import type { ViolationResponse, ViolationCreate } from '@/types/activity.types';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const ViolationManagementPage = () => {
    const { hasPermission } = useAuth();

    // TanStack Query hooks
    const { data: violations = [], isLoading } = useViolations();
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
                // For edit, we stick to original violation update if backend supports it.
                // Note: ViolationUpdate schema does NOT have user_id(s). So we can't update users here anyway.
                // We just send date and reason.
                const updateData = {
                    reason: values.reason,
                    date: values.date.toISOString(),
                };
                await updateViolation.mutateAsync({ id: editingItem.id, data: updateData });
                message.success('Violation updated successfully');
            } else {
                // Create mode uses user_ids
                const formattedValues: ViolationCreate = {
                    user_ids: values.user_ids, // Expect array
                    reason: values.reason,
                    date: values.date.toISOString(),
                };
                await createViolation.mutateAsync(formattedValues);
                message.success('Violation recorded successfully');
            }
            setIsModalOpen(false);
            form.resetFields();
        } catch (error: any) {
            message.error(error?.response?.data?.message || 'Operation failed');
        }
    };

    const handleDelete = async (id: number) => {
        try {
            await deleteViolation.mutateAsync(id);
            message.success('Violation deleted successfully');
            setIsDetailOpen(false);
        } catch (error: any) {
            message.error(error?.response?.data?.message || 'Delete failed');
        }
    };



    const columns = [
        {
            title: 'Thành viên',
            key: 'user',
            render: (_: any, record: ViolationResponse) => (
                <Space>
                    <Avatar
                        src={record.user_avatar}
                        icon={<UserOutlined />}
                        className="bg-linear-to-br from-red-500 to-orange-500 shadow-sm"
                        size="small"
                    />
                    <div>
                        <Text strong className="block">{record.user_name || 'Unknown'}</Text>
                    </div>
                </Space>
            ),
        },
        {
            title: 'Lý do vi phạm',
            dataIndex: 'reason',
            key: 'reason',
            render: (reason: string) => (
                <Text className="max-w-[300px] block truncate" title={reason}>{reason}</Text>
            ),
        },
        {
            title: 'Thời gian',
            dataIndex: 'date',
            key: 'date',
            render: (date: string) => (
                <Space>
                    <CalendarOutlined className="text-gray-400" />
                    <Text>{dayjs(date).format('DD/MM/YYYY HH:mm')}</Text>
                </Space>
            ),
        },
        {
            title: 'Thao tác',
            key: 'actions',
            width: 120,
            render: (_: any, record: ViolationResponse) => (
                <Space onClick={(e) => e.stopPropagation()}>
                    <Button
                        icon={<EditOutlined />}
                        size="small"
                        onClick={() => {
                            setEditingItem(record);
                            form.setFieldsValue({
                                ...record,
                                user_name: record.user_name || 'Unknown', // Set for display
                                date: dayjs(record.date)
                            });
                            setIsModalOpen(true);
                        }}
                        disabled={!canUpdate}
                    />
                    <Popconfirm
                        title="Xóa vi phạm này?"
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
        <div className="p-6">
            <Card className="shadow-sm border-gray-100 rounded-xl overflow-hidden">
                <div className="flex justify-between items-center mb-6">
                    <Space size="middle">
                        <div className="w-12 h-12 rounded-xl bg-red-50 flex items-center justify-center text-red-500">
                            <WarningOutlined className="text-2xl" />
                        </div>
                        <div>
                            <Title level={3} className="!m-0">Quản lý Vi phạm</Title>
                            <Text type="secondary">Danh sách và công cụ xử lý các vi phạm của thành viên</Text>
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
                            className="bg-linear-to-r from-red-500 to-orange-500 border-none shadow-md h-10 px-6 font-semibold"
                        >
                            Thêm Vi phạm
                        </Button>
                    )}
                </div>

                <Table
                    columns={columns}
                    dataSource={violations}
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
            </Card>

            {/* Create/Edit Modal */}
            <Modal
                title={editingItem ? 'Chỉnh sửa Vi phạm' : 'Ghi nhận Vi phạm mới'}
                open={isModalOpen}
                onCancel={() => setIsModalOpen(false)}
                onOk={() => form.submit()}
                centered
                confirmLoading={createViolation.isPending || updateViolation.isPending}
                destroyOnHidden
                okText={editingItem ? 'Lưu thay đổi' : 'Ghi nhận'}
                cancelText="Hủy"
                width={500}
            >
                <Form form={form} layout="vertical" onFinish={handleCreateOrUpdate} className="mt-6">
                    {editingItem ? (
                        <Form.Item name="user_name" label="Thành viên vi phạm">
                            <Input disabled />
                        </Form.Item>
                    ) : (
                        <Form.Item name="user_ids" label="Thành viên vi phạm" rules={[{ required: true, message: 'Vui lòng chọn thành viên!' }]}>
                            <Select
                                mode="multiple"
                                showSearch
                                placeholder="Tìm kiếm thành viên"
                                optionFilterProp="children"
                                filterOption={(input, option) =>
                                    String(option?.children ?? '').toLowerCase().includes(input.toLowerCase())
                                }
                            >
                                {users.map(u => (
                                    <Option key={u.id} value={u.id}>{u.name} ({u.email})</Option>
                                ))}
                            </Select>
                        </Form.Item>
                    )}

                    <Form.Item name="date" label="Thời gian vi phạm" rules={[{ required: true, message: 'Vui lòng chọn thời gian!' }]}>
                        <DatePicker showTime format="DD/MM/YYYY HH:mm" className="w-full" />
                    </Form.Item>

                    <Form.Item name="reason" label="Lý do vi phạm" rules={[{ required: true, message: 'Vui lòng nhập lý do!' }]}>
                        <TextArea rows={4} placeholder="Mô tả chi tiết vi phạm..." />
                    </Form.Item>
                </Form>
            </Modal>

            {/* Detail Drawer */}
            <Drawer
                title={
                    <Space>
                        <InfoCircleOutlined className="text-red-500" />
                        <span>Chi tiết Vi phạm</span>
                    </Space>
                }
                placement="right"
                onClose={() => setIsDetailOpen(false)}
                open={isDetailOpen}
                width={500}
            >
                {detailItem && (
                    <div className="flex flex-col h-full">
                        <div className="flex-1">
                            <Descriptions column={1} bordered size="small" className="mb-6">
                                <Descriptions.Item label="Thành viên">
                                    <Space>
                                        <UserOutlined />
                                        <Text strong>{detailItem.user_name || 'Unknown'}</Text>
                                    </Space>
                                </Descriptions.Item>
                                <Descriptions.Item label="Thời gian">
                                    {dayjs(detailItem.date).format('DD/MM/YYYY HH:mm')}
                                </Descriptions.Item>
                            </Descriptions>

                            <Divider style={{ textAlign: 'left' }} className="!mb-4">Lý do / Nội dung</Divider>
                            <div className="bg-red-50 p-4 rounded-lg border border-red-100 text-gray-700 whitespace-pre-wrap">
                                {detailItem.reason}
                            </div>

                            <Divider style={{ textAlign: 'left' }} className="!mb-4">Thông tin hệ thống</Divider>
                            <Descriptions column={1} size="small" className="text-gray-500">
                                <Descriptions.Item label="Ngày ghi nhận">
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
                                            date: dayjs(detailItem.date)
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
                                    title="Xóa vi phạm này?"
                                    onConfirm={() => handleDelete(detailItem.id)}
                                    okText="Xóa"
                                    cancelText="Hủy"
                                >
                                    <Button danger icon={<DeleteOutlined />}>Xóa</Button>
                                </Popconfirm>
                            )}
                        </div>
                    </div>
                )}
            </Drawer>
        </div>
    );
};

export default ViolationManagementPage;
