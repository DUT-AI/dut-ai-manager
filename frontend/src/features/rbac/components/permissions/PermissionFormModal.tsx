import React, { useEffect } from 'react';
import { Modal, Form, Select, DatePicker, TimePicker, Input, Grid, Tag } from 'antd';
import dayjs from 'dayjs';
import { useHomeworks } from '@/features/homework/hooks/useHomeworks';
import { useMeetings, useUpcomingMeetingsWithSeats } from '@/features/meeting';
import type { PermissionRequestResponse } from '@/features/activity/types/activity.types';

const { Option } = Select;
const { TextArea } = Input;

interface PermissionFormModalProps {
    isOpen: boolean;
    editingItem: PermissionRequestResponse | null;
    confirmLoading: boolean;
    onClose: () => void;
    onSubmit: (values: any) => Promise<void>;
}

export const PermissionFormModal: React.FC<PermissionFormModalProps> = ({
    isOpen,
    editingItem,
    confirmLoading,
    onClose,
    onSubmit,
}) => {
    const screens = Grid.useBreakpoint();
    const [form] = Form.useForm();

    // Chỉ kích hoạt query khi modal thực sự mở
    const { data: homeworksData } = useHomeworks({ enabled: isOpen });
    const homeworks = homeworksData || [];
    const { data: meetings = [] } = useMeetings({ enabled: isOpen });
    const { data: upcomingMeetings = [] } = useUpcomingMeetingsWithSeats(undefined, isOpen);

    useEffect(() => {
        if (isOpen) {
            if (editingItem) {
                form.setFieldsValue({
                    ...editingItem,
                    start_time: editingItem.start_time ? dayjs(editingItem.start_time) : null,
                });
            } else {
                form.resetFields();
                form.setFieldsValue({
                    date: dayjs(),
                    category: 'ABSENCE',
                });
            }
        }
    }, [isOpen, editingItem, form]);

    const handleOk = async () => {
        try {
            const values = await form.validateFields();

            if (values.category === 'CHANGE_MEETING') {
                if (values.old_meeting_id && values.old_meeting_id === values.meeting_id) {
                    form.setFields([
                        {
                            name: 'meeting_id',
                            errors: ['Không thể đổi sang cùng một buổi họp!'],
                        },
                    ]);
                    return;
                }
            }

            let finalStartTime: string | undefined = undefined;
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

            const formattedValues = {
                ...values,
                start_time: values.category === 'CHANGE_MEETING' ? undefined : finalStartTime,
                old_meeting_id: values.category === 'CHANGE_MEETING' ? (values.old_meeting_id ? Number(values.old_meeting_id) : undefined) : undefined,
                meeting_id: values.meeting_id ? Number(values.meeting_id) : undefined,
            };

            await onSubmit(formattedValues);
            form.resetFields();
        } catch {
            // Validation failed or onSubmit error
        }
    };

    return (
        <Modal
            title={editingItem ? 'Chỉnh sửa Đơn xin phép' : 'Tạo Đơn xin phép mới'}
            open={isOpen}
            onCancel={onClose}
            onOk={handleOk}
            centered
            confirmLoading={confirmLoading}
            destroyOnHidden
            okText={editingItem ? 'Lưu thay đổi' : 'Gửi đơn'}
            cancelText="Hủy"
            width={screens.md ? 500 : '100%'}
        >
            <Form form={form} layout="vertical" className="mt-6">
                <Form.Item name="category" label="Loại đơn" rules={[{ required: true }]}>
                    <Select onChange={() => form.setFieldsValue({ homework_id: undefined, meeting_id: undefined, old_meeting_id: undefined, start_time: undefined })}>
                        <Option value="ABSENCE">Vắng sinh hoạt</Option>
                        <Option value="LATE">Đi trễ sinh hoạt</Option>
                        <Option value="POSTPONE">Tạm hoãn bài tập</Option>
                        <Option value="CHANGE_MEETING">Đổi buổi sinh hoạt</Option>
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
                                <Form.Item
                                    name="homework_id"
                                    label="Bài tập"
                                    rules={[{ required: true, message: 'Vui lòng chọn bài tập!' }]}
                                >
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
                                <Form.Item
                                    name="meeting_id"
                                    label="Buổi sinh hoạt"
                                    rules={[{ required: true, message: 'Vui lòng chọn buổi sinh hoạt!' }]}
                                >
                                    <Select placeholder="Chọn buổi sinh hoạt">
                                        {(meetings || []).map((m: any) => (
                                            <Option key={m.id} value={m.id}>
                                                {m.title} ({dayjs(m.start_time).format('DD/MM/YYYY')})
                                            </Option>
                                        ))}
                                    </Select>
                                </Form.Item>
                            );
                        }
                        if (category === 'CHANGE_MEETING') {
                            return (
                                <>
                                    <Form.Item
                                        name="old_meeting_id"
                                        label="Buổi sinh hoạt hiện tại"
                                        tooltip="Chọn buổi sinh hoạt bạn đang tham gia, hoặc để trống nếu bạn chưa có lịch (đăng ký mới)"
                                    >
                                        <Select placeholder="Chọn buổi sinh hoạt hiện tại (để trống nếu đăng ký mới)" allowClear>
                                            {(meetings || []).map((m: any) => (
                                                <Option key={m.id} value={m.id}>
                                                    {m.title} ({dayjs(m.start_time).format('DD/MM/YYYY')})
                                                </Option>
                                            ))}
                                        </Select>
                                    </Form.Item>

                                    <Form.Item
                                        name="meeting_id"
                                        label="Buổi sinh hoạt đích (chuyển đến)"
                                        rules={[{ required: true, message: 'Vui lòng chọn buổi sinh hoạt đích!' }]}
                                    >
                                        <Select placeholder="Chọn buổi sinh hoạt sắp tới">
                                            {(upcomingMeetings || []).map((m: any) => (
                                                <Option key={m.id} value={m.id} disabled={m.is_full}>
                                                    <div className="flex items-center justify-between">
                                                        <span>{m.title} ({dayjs(m.start_time).format('DD/MM/YYYY HH:mm')})</span>
                                                        <Tag color={m.is_full ? 'error' : 'success'} className="ml-2 mr-0 font-medium text-xs">
                                                            {m.is_full ? 'Hết chỗ' : `Còn ${m.available_seats}/${m.max_seats} chỗ`}
                                                        </Tag>
                                                    </div>
                                                </Option>
                                            ))}
                                        </Select>
                                    </Form.Item>
                                </>
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
                        if (category === 'ABSENCE' || category === 'OTHER' || category === 'CHANGE_MEETING') return null;

                        if (category === 'POSTPONE') {
                            return (
                                <Form.Item
                                    name="start_time"
                                    label="Deadline mới (ngày và giờ)"
                                    rules={[
                                        { required: true, message: 'Vui lòng chọn deadline mới!' },
                                        ({ getFieldValue }) => ({
                                            validator(_, value) {
                                                const hwId = getFieldValue('homework_id');
                                                if (value && hwId) {
                                                    const homework = homeworks.find((h: any) => h.id === hwId);
                                                    if (homework) {
                                                        const deadline = dayjs(homework.deadline);
                                                        const diffDays = value.diff(deadline, 'day', true);
                                                        if (diffDays > 4) {
                                                            return Promise.reject(new Error('Thời gian hoãn không được quá 4 ngày!'));
                                                        }
                                                        if (diffDays < 0) {
                                                            return Promise.reject(new Error('Hạn mới phải sau deadline gốc!'));
                                                        }
                                                    }
                                                }
                                                return Promise.resolve();
                                            },
                                        }),
                                    ]}
                                >
                                    <DatePicker
                                        showTime
                                        format="DD/MM/YYYY HH:mm"
                                        className="w-full"
                                        placeholder="Chọn ngày và giờ"
                                    />
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

                <Form.Item
                    name="note"
                    label="Lý do/Ghi chú"
                    rules={[{ required: true, message: 'Vui lòng nhập lý do!' }]}
                >
                    <TextArea rows={4} placeholder="Mô tả chi tiết lý do..." />
                </Form.Item>
            </Form>
        </Modal>
    );
};
