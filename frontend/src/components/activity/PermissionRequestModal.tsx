import { useEffect } from 'react';
import { Modal, Form, Select, DatePicker, TimePicker, Input } from 'antd';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';
import type { PermissionRequestResponse } from '@/types/activity.types';

const { Option } = Select;
const { TextArea } = Input;

interface Props {
    open: boolean;
    editingItem: PermissionRequestResponse | null;
    initialDate: Dayjs;
    onSubmit: (values: any) => void;
    onCancel: () => void;
}

export const PermissionRequestModal = ({ open, editingItem, initialDate, onSubmit, onCancel }: Props) => {
    const [form] = Form.useForm();

    useEffect(() => {
        if (open) {
            if (editingItem) {
                form.setFieldsValue({
                    category: editingItem.category,
                    note: editingItem.note,
                    date: dayjs(editingItem.date),
                    start_time: dayjs(editingItem.start_time, 'HH:mm:ss'),
                    end_time: dayjs(editingItem.end_time, 'HH:mm:ss'),
                });
            } else {
                form.resetFields();
                form.setFieldValue('date', initialDate);
            }
        }
    }, [open, editingItem, initialDate, form]);

    const handleFinish = (values: any) => {
        const formattedValues = {
            ...values,
            date: values.date.format('YYYY-MM-DD'),
            start_time: values.start_time.format('HH:mm:ss'),
            end_time: values.end_time.format('HH:mm:ss'),
        };
        onSubmit(formattedValues);
    };

    return (
        <Modal
            title={editingItem ? "Sửa đơn xin phép" : "Tạo đơn xin phép"}
            open={open}
            onCancel={onCancel}
            onOk={form.submit}
            destroyOnClose
        >
            <Form form={form} layout="vertical" onFinish={handleFinish}>
                <Form.Item name="category" label="Loại" rules={[{ required: true }]}>
                    <Select>
                        <Option value="vắng sinh hoạt">Vắng sinh hoạt</Option>
                        <Option value="tạm hoãn bài tập">Tạm hoãn bài tập</Option>
                        <Option value="đi trễ sinh hoạt">Đi trễ sinh hoạt</Option>
                        <Option value="khác">Khác</Option>
                    </Select>
                </Form.Item>
                <Form.Item name="date" label="Ngày xin phép" rules={[{ required: true, message: 'Vui lòng chọn ngày!' }]}>
                    <DatePicker format="DD/MM/YYYY" className="w-full" />
                </Form.Item>
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
    );
};
