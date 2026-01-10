import { useState, useEffect } from 'react';
import {
    Calendar,
    Badge,
    Card,
    Drawer,
    Typography,
    List,
    Tag,
    Divider,
    Empty,
    Spin,
    message,
    Button,
    Modal,
    Form,
    Input,
    Select,
    DatePicker,
    TimePicker,
    InputNumber,
    Popconfirm,
    Tooltip
} from 'antd';
import {
    CalendarOutlined,
    CheckCircleOutlined,
    WarningOutlined,
    FileTextOutlined,
    ClockCircleOutlined,
    PlusCircleOutlined,
    PlusOutlined,
    EditOutlined,
    DeleteOutlined
} from '@ant-design/icons';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';
import { permissionService } from '@/services/api/permission.service';
import { bonusPointService } from '@/services/api/bonus-point.service';
import { userService } from '@/services/api/user.service';
import type { DailySummaryResponse } from '@/types/activity.types';
import { violationService } from '@/services/api/violation.service';
import { activityService } from '@/services/api/activity.service';

const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const ActivityCalendarPage = () => {
    // State
    const [selectedDate, setSelectedDate] = useState<Dayjs>(dayjs());
    const [drawerVisible, setDrawerVisible] = useState(false);
    const [dailyData, setDailyData] = useState<DailySummaryResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [activeDates, setActiveDates] = useState<string[]>([]);
    const [users, setUsers] = useState<any[]>([]); // Users list for Select

    // Modals State
    const [isPermissionModalOpen, setIsPermissionModalOpen] = useState(false);
    const [isBonusModalOpen, setIsBonusModalOpen] = useState(false);
    const [isViolationModalOpen, setIsViolationModalOpen] = useState(false);
    const [editingItem, setEditingItem] = useState<any>(null); // Polymorphic state for editing

    // Form Hooks
    const [permissionForm] = Form.useForm();
    const [bonusForm] = Form.useForm();
    const [violationForm] = Form.useForm();

    // Fetch Data
    const fetchMonthlyData = async (date: Dayjs) => {
        try {
            const res = await activityService.getMonthlyStats(date.month() + 1, date.year());
            if (res.is_success) {
                setActiveDates(res.data || []);
            }
        } catch (error) {
            console.error('Failed to fetch monthly stats', error);
        }
    };

    const fetchDailyDetail = async (date: Dayjs) => {
        setLoading(true);
        try {
            const dateStr = date.format('YYYY-MM-DD');
            const res = await activityService.getDailySummary(dateStr);
            if (res.is_success) {
                setDailyData(res.data || null);
                // Open drawer if not already open (handled by selection logic)
            } else {
                message.error(res.message || 'Failed to fetch details');
            }
        } catch (error) {
            message.error('Connection error');
        } finally {
            setLoading(false);
        }
    };

    // Fetch Users Helper
    const fetchAllUsers = async () => {
        try {
            const res = await userService.getUsers();
            if (res.is_success) {
                setUsers(res.data || []);
            } else {
                message.error(res.message || 'Failed to fetch users');
            }
        } catch (error) {
            message.error('Connection error while fetching users');
        }
    };

    useEffect(() => {
        fetchMonthlyData(selectedDate);
        fetchAllUsers();
    }, [selectedDate.month(), selectedDate.year()]);

    const dateCellRender = (value: Dayjs) => {
        const dateStr = value.format('YYYY-MM-DD');
        const hasActivity = activeDates.includes(dateStr);
        if (hasActivity) {
            return (
                <div className="flex justify-center mt-1">
                    <Badge status="processing" color="#667eea" />
                </div>
            );
        }
        return null;
    };

    const onSelect = (newValue: Dayjs) => {
        setSelectedDate(newValue);
        fetchDailyDetail(newValue);
        setDrawerVisible(true);
    };

    // --- CRUD Handlers ---

    // 1. Permissions
    const handlePermissionSubmit = async (values: any) => {
        const formattedValues = {
            ...values,
            date: values.date.format('YYYY-MM-DD'),
            start_time: values.start_time.format('HH:mm:ss'),
            end_time: values.end_time.format('HH:mm:ss'),
        };

        try {
            if (editingItem) {
                await permissionService.updatePermission(editingItem.id, formattedValues);
                message.success('Permission updated');
            } else {
                await permissionService.createPermission(formattedValues);
                message.success('Permission created');
            }
            setIsPermissionModalOpen(false);
            fetchDailyDetail(selectedDate);
            fetchMonthlyData(selectedDate); // Refresh dots
        } catch (error) {
            message.error('Failed to save permission');
        }
    };

    const handleDeletePermission = async (id: number) => {
        try {
            await permissionService.deletePermission(id);
            message.success('Deleted successfully');
            fetchDailyDetail(selectedDate);
            fetchMonthlyData(selectedDate);
        } catch (error) {
            message.error('Failed to delete');
        }
    };

    // 2. Bonus Points
    const handleBonusSubmit = async (values: any) => {
        const formattedValues = {
            user_id: values.user_id,
            points: values.points,
            reason: values.reason,
            date: values.date.toISOString()
        };

        try {
            if (editingItem) {
                await bonusPointService.updateBonusPoint(editingItem.id, formattedValues);
                message.success('Bonus point updated');
            } else {
                await bonusPointService.createBonusPoint(formattedValues);
                message.success('Bonus point added');
            }
            setIsBonusModalOpen(false);
            fetchDailyDetail(selectedDate);
            fetchMonthlyData(selectedDate);
        } catch (error) {
            message.error('Failed to save bonus point');
        }
    };

    const handleDeleteBonus = async (id: number) => {
        try {
            await bonusPointService.deleteBonusPoint(id);
            message.success('Deleted successfully');
            fetchDailyDetail(selectedDate);
            fetchMonthlyData(selectedDate);
        } catch (error) {
            message.error('Failed to delete');
        }
    };

    // 3. Violations
    const handleViolationSubmit = async (values: any) => {
        const formattedValues = {
            user_id: values.user_id,
            reason: values.reason,
            date: values.date.toISOString()
        };

        try {
            if (editingItem) {
                await violationService.updateViolation(editingItem.id, formattedValues);
                message.success('Violation updated');
            } else {
                await violationService.createViolation(formattedValues);
                message.success('Violation recorded');
            }
            setIsViolationModalOpen(false);
            fetchDailyDetail(selectedDate);
            fetchMonthlyData(selectedDate);
        } catch (error) {
            message.error('Failed to save violation');
        }
    };

    const handleDeleteViolation = async (id: number) => {
        try {
            await violationService.deleteViolation(id);
            message.success('Deleted successfully');
            fetchDailyDetail(selectedDate);
            fetchMonthlyData(selectedDate);
        } catch (error) {
            message.error('Failed to delete');
        }
    };

    // Open Modals helper
    const openAddModal = (type: 'permission' | 'bonus' | 'violation') => {
        setEditingItem(null);
        const initialDate = selectedDate.isSame(dayjs(), 'day')
            ? dayjs()
            : selectedDate.hour(dayjs().hour()).minute(dayjs().minute());

        if (type === 'permission') {
            permissionForm.resetFields();
            permissionForm.setFieldValue('date', initialDate);
            setIsPermissionModalOpen(true);
        } else if (type === 'bonus') {
            bonusForm.resetFields();
            bonusForm.setFieldValue('date', initialDate);
            setIsBonusModalOpen(true);
        } else {
            violationForm.resetFields();
            violationForm.setFieldValue('date', initialDate);
            setIsViolationModalOpen(true);
        }
    };

    const openEditModal = (type: 'permission' | 'bonus' | 'violation', item: any) => {
        setEditingItem(item);
        if (type === 'permission') {
            permissionForm.setFieldsValue({
                category: item.category,
                note: item.note,
                date: dayjs(item.date),
                start_time: dayjs(item.start_time, 'HH:mm:ss'),
                end_time: dayjs(item.end_time, 'HH:mm:ss'),
            });
            setIsPermissionModalOpen(true);
        } else if (type === 'bonus') {
            bonusForm.setFieldsValue({
                user_id: item.user_id,
                points: item.points,
                reason: item.reason,
                date: dayjs(item.date)
            });
            setIsBonusModalOpen(true);
        } else {
            violationForm.setFieldsValue({
                user_id: item.user_id,
                reason: item.reason,
                date: dayjs(item.date)
            });
            setIsViolationModalOpen(true);
        }
    };

    return (
        <div className="p-6">
            <Card className="shadow-md border-none rounded-2xl overflow-hidden">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-xl bg-linear-to-br from-[#667eea] to-[#764ba2] flex items-center justify-center text-white shadow-lg">
                            <CalendarOutlined className="text-2xl" />
                        </div>
                        <div>
                            <Title level={3} className="!m-0">Hoạt Động & Chấm Công</Title>
                            <Text type="secondary">Quản lý xin phép, điểm cộng và vi phạm cá nhân</Text>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <Button
                            type="primary"
                            icon={<PlusOutlined />}
                            className="bg-green-500 hover:bg-green-600 border-none"
                            onClick={() => openAddModal('bonus')}
                        >
                            Thêm Điểm Cộng
                        </Button>
                        <Button
                            type="primary"
                            icon={<WarningOutlined />}
                            className="bg-red-500 hover:bg-red-600 border-none"
                            onClick={() => openAddModal('violation')}
                        >
                            Thêm Vi Phạm
                        </Button>
                        <Button
                            icon={<FileTextOutlined />}
                            onClick={() => openAddModal('permission')}
                        >
                            Xin Phép
                        </Button>
                    </div>
                </div>

                <div className="bg-white p-4 rounded-xl border border-gray-100">
                    <Calendar
                        onSelect={onSelect}
                        cellRender={dateCellRender}
                        fullscreen={true}
                        className="custom-calendar"
                    />
                </div>
            </Card>

            <Drawer
                title={
                    <div className="flex flex-col">
                        <Text strong className="text-lg">Chi tiết ngày {selectedDate.format('DD/MM/YYYY')}</Text>
                        <Text type="secondary" className="text-xs">Danh sách các hoạt động đã ghi nhận</Text>
                    </div>
                }
                placement="right"
                onClose={() => setDrawerVisible(false)}
                open={drawerVisible}
                size={450}
                className="activity-drawer"
            >
                {loading ? (
                    <div className="h-full flex items-center justify-center">
                        <Spin size="large" tip="Đang tải dữ liệu..." />
                    </div>
                ) : (
                    <div className="flex flex-col gap-8 pb-10">
                        {/* Permission Requests */}
                        <section>
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-2">
                                    <FileTextOutlined className="text-blue-500" />
                                    <Text strong className="uppercase tracking-wider text-sm">Đơn xin phép</Text>
                                    <Badge count={dailyData?.permission_requests.length} color="#3b82f6" offset={[2, 0]} />
                                </div>
                                {/* Removed Add button from here as per instruction */}
                            </div>

                            {dailyData?.permission_requests.length ? (
                                <List
                                    dataSource={dailyData.permission_requests}
                                    renderItem={(item) => (
                                        <Card size="small" className="mb-3 border-l-4 border-l-blue-400 bg-blue-50/20 hover:shadow-sm transition-shadow">
                                            <div className="flex justify-between items-start mb-2">
                                                <Tag color="blue">{item.category.toUpperCase()}</Tag>
                                                <div className="flex gap-2">
                                                    <Tooltip title="Edit">
                                                        <EditOutlined className="text-gray-400 hover:text-blue-600 cursor-pointer" onClick={() => openEditModal('permission', item)} />
                                                    </Tooltip>
                                                    <Popconfirm title="Delete this request?" onConfirm={() => handleDeletePermission(item.id)}>
                                                        <DeleteOutlined className="text-gray-400 hover:text-red-500 cursor-pointer" />
                                                    </Popconfirm>
                                                </div>
                                            </div>
                                            <div className="flex items-center text-gray-500 text-xs mb-2">
                                                <ClockCircleOutlined className="mr-1" />
                                                {item.start_time.substring(0, 5)} - {item.end_time.substring(0, 5)}
                                            </div>
                                            <Text className="block text-sm text-gray-700">{item.note}</Text>
                                            <div className="mt-2 pt-2 border-t border-blue-100 flex justify-between items-center text-[10px] text-gray-400">
                                                <span>Tạo bởi: #{item.created_by || 'System'}</span>
                                                <span>{dayjs(item.created_at).format('DD/MM HH:mm')}</span>
                                            </div>
                                            {item.updated_at !== item.created_at && (
                                                <div className="flex justify-between items-center text-[10px] text-gray-400 italic">
                                                    <span>Sửa bởi: #{item.updated_by || 'System'}</span>
                                                    <span>{dayjs(item.updated_at).format('DD/MM HH:mm')}</span>
                                                </div>
                                            )}
                                        </Card>
                                    )}
                                />
                            ) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={<span className="text-xs text-gray-400">Không có đơn xin phép</span>} />}
                        </section>

                        <Divider className="!m-0" />

                        {/* Bonus Points */}
                        <section>
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-2">
                                    <PlusCircleOutlined className="text-green-500" />
                                    <Text strong className="uppercase tracking-wider text-sm">Điểm cộng</Text>
                                    <Badge count={dailyData?.bonus_points.length} color="#10b981" offset={[2, 0]} />
                                </div>
                                {/* Removed Add button from here as per instruction */}
                            </div>

                            {dailyData?.bonus_points.length ? (
                                <List
                                    dataSource={dailyData.bonus_points}
                                    renderItem={(item) => (
                                        <Card size="small" className="mb-3 border-l-4 border-l-green-400 bg-green-50/20 hover:shadow-sm transition-shadow">
                                            <div className="flex justify-between items-center mb-1">
                                                <div className="flex items-center gap-2">
                                                    <Text strong className="text-green-700">+{item.points} Điểm</Text>
                                                    <CheckCircleOutlined className="text-green-500 text-xs" />
                                                </div>
                                                <div className="flex gap-2">
                                                    <Tooltip title="Edit">
                                                        <EditOutlined className="text-gray-400 hover:text-green-600 cursor-pointer" onClick={() => openEditModal('bonus', item)} />
                                                    </Tooltip>
                                                    <Popconfirm title="Delete this bonus?" onConfirm={() => handleDeleteBonus(item.id)}>
                                                        <DeleteOutlined className="text-gray-400 hover:text-red-500 cursor-pointer" />
                                                    </Popconfirm>
                                                </div>
                                            </div>
                                            <Text className="block text-sm text-gray-700">{item.reason}</Text>
                                        </Card>
                                    )}
                                />
                            ) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={<span className="text-xs text-gray-400">Chưa có điểm cộng</span>} />}
                        </section>

                        <Divider className="!m-0" />

                        {/* Violations */}
                        <section>
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-2">
                                    <WarningOutlined className="text-red-500" />
                                    <Text strong className="uppercase tracking-wider text-sm">Vi phạm</Text>
                                    <Badge count={dailyData?.violations.length} color="#ef4444" offset={[2, 0]} />
                                </div>
                                {/* Removed Add button from here as per instruction */}
                            </div>

                            {dailyData?.violations.length ? (
                                <List
                                    dataSource={dailyData.violations}
                                    renderItem={(item) => (
                                        <Card size="small" className="mb-3 border-l-4 border-l-red-400 bg-red-50/20 hover:shadow-sm transition-shadow">
                                            <div className="flex justify-between items-center mb-1">
                                                <div className="flex items-center gap-2">
                                                    <Text strong className="text-red-700">Vi phạm</Text>
                                                    <WarningOutlined className="text-red-500 text-xs" />
                                                </div>
                                                <div className="flex gap-2">
                                                    <Tooltip title="Edit">
                                                        <EditOutlined className="text-gray-400 hover:text-red-600 cursor-pointer" onClick={() => openEditModal('violation', item)} />
                                                    </Tooltip>
                                                    <Popconfirm title="Delete this violation?" onConfirm={() => handleDeleteViolation(item.id)}>
                                                        <DeleteOutlined className="text-gray-400 hover:text-red-500 cursor-pointer" />
                                                    </Popconfirm>
                                                </div>
                                            </div>
                                            <Text className="block text-sm text-gray-700">{item.reason}</Text>
                                        </Card>
                                    )}
                                />
                            ) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={<span className="text-xs text-gray-400">Tuyệt vời! Không có vi phạm</span>} />}
                        </section>
                    </div>
                )}
            </Drawer>

            {/* Modals */}
            <Modal
                title={editingItem ? "Edit Permission Request" : "New Permission Request"}
                open={isPermissionModalOpen}
                onCancel={() => setIsPermissionModalOpen(false)}
                onOk={permissionForm.submit}
            >
                <Form form={permissionForm} layout="vertical" onFinish={handlePermissionSubmit}>
                    <Form.Item name="category" label="Loại" rules={[{ required: true }]}>
                        <Select>
                            <Option value="vắng sinh hoạt">Vắng sinh hoạt</Option>
                            <Option value="tạm hoãn bài tập">Tạm hoãn bài tập</Option>
                            <Option value="đi trễ sinh hoạt">Đi trễ sinh hoạt</Option>
                            <Option value="khác">Khác</Option>
                        </Select>
                    </Form.Item>
                    <div className="grid grid-cols-1 gap-4">
                        <Form.Item name="date" label="Ngày xin phép" rules={[{ required: true, message: 'Vui lòng chọn ngày!' }]}>
                            <DatePicker format="DD/MM/YYYY" className="w-full" />
                        </Form.Item>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <Form.Item name="start_time" label="Từ giờ" rules={[{ required: true, message: 'Vui lòng chọn giờ bắt đầu!' }]}>
                            <TimePicker format="HH:mm" className="w-full" />
                        </Form.Item>
                        <Form.Item name="end_time" label="Đến giờ" rules={[{ required: true, message: 'Vui lòng chọn giờ kết thúc!' }]}>
                            <TimePicker format="HH:mm" className="w-full" />
                        </Form.Item>
                    </div>
                    <Form.Item name="note" label="Lý do / Ghi chú" rules={[{ required: true }]}>
                        <TextArea rows={3} />
                    </Form.Item>
                </Form>
            </Modal>

            <Modal
                title={editingItem ? "Edit Bonus Point" : "Add Bonus Point"}
                open={isBonusModalOpen}
                onCancel={() => setIsBonusModalOpen(false)}
                onOk={bonusForm.submit}
            >
                <Form form={bonusForm} layout="vertical" onFinish={handleBonusSubmit}>
                    <Form.Item name="user_id" label="Thành viên" rules={[{ required: true, message: 'Vui lòng chọn thành viên!' }]}>
                        <Select
                            showSearch
                            placeholder="Chọn thành viên"
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
                    <div className="grid grid-cols-2 gap-4">
                        <Form.Item name="date" label="Ngày & Giờ" rules={[{ required: true, message: 'Vui lòng chọn thời gian!' }]}>
                            <DatePicker showTime format="DD/MM/YYYY HH:mm" className="w-full" />
                        </Form.Item>
                        <Form.Item name="points" label="Điểm số" rules={[{ required: true, message: 'Vui lòng nhập điểm số!' }]}>
                            <InputNumber min={1} max={100} className="w-full" />
                        </Form.Item>
                    </div>
                    <Form.Item name="reason" label="Lý do" rules={[{ required: true, message: 'Vui lòng nhập lý do!' }]}>
                        <TextArea rows={3} />
                    </Form.Item>
                </Form>
            </Modal>

            <Modal
                title={editingItem ? "Edit Violation" : "Record Violation"}
                open={isViolationModalOpen}
                onCancel={() => setIsViolationModalOpen(false)}
                onOk={violationForm.submit}
            >
                <Form form={violationForm} layout="vertical" onFinish={handleViolationSubmit}>
                    <Form.Item name="user_id" label="Thành viên" rules={[{ required: true, message: 'Vui lòng chọn thành viên!' }]}>
                        <Select
                            showSearch
                            placeholder="Chọn thành viên"
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
                    <Form.Item name="date" label="Ngày & Giờ" rules={[{ required: true, message: 'Vui lòng chọn thời gian!' }]}>
                        <DatePicker showTime format="DD/MM/YYYY HH:mm" className="w-full" />
                    </Form.Item>
                    <Form.Item name="reason" label="Lý do vi phạm" rules={[{ required: true, message: 'Vui lòng nhập lý do vi phạm!' }]}>
                        <TextArea rows={3} />
                    </Form.Item>
                </Form>
            </Modal>

            <style>{`
                .custom-calendar .ant-picker-calendar-header {
                    padding-bottom: 20px;
                }
                .custom-calendar .ant-picker-cell-selected .ant-picker-calendar-date {
                    background: rgba(102, 126, 234, 0.1) !important;
                    border-top: 2px solid #667eea !important;
                }
                .activity-drawer .ant-drawer-header {
                    background: #f8fafc;
                    border-bottom: 1px solid #f1f5f9;
                }
            `}</style>
        </div>
    );
};

export default ActivityCalendarPage;
