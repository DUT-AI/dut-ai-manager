import { Modal, Form, Select, TimePicker, Input } from 'antd';
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

    const initialValues = editingItem ? {
        category: editingItem.category,
        note: editingItem.note,
        start_time: editingItem.start_time ? dayjs(editingItem.start_time) : null,
    } : { start_time: initialDate };

    const handleFinish = (values: any) => {
        let finalStartTime = undefined;
        if (values.start_time) {
            // Since this modal creates from a specific date day, we maintain that date part
            const dateStr = initialDate.format('YYYY-MM-DD');
            const timeStr = values.start_time.format('HH:mm:ss');
            finalStartTime = `${dateStr}T${timeStr}`;
        }
        
        const formattedValues = {
            ...values,
            start_time: finalStartTime,
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
            <Form form={form} initialValues={initialValues} layout="vertical" onFinish={handleFinish}>
                <Form.Item name="category" label="Loại" rules={[{ required: true }]}>
                    <Select>
                        <Option value="ABSENT">Vắng sinh hoạt</Option>
                        <Option value="POSTPONE">Tạm hoãn bài tập</Option>
                        <Option value="LATE">Đi trễ sinh hoạt</Option>
                        <Option value="OTHER">Khác</Option>
                    </Select>
                </Form.Item>
                <div className="grid grid-cols-1 gap-4">
                    <Form.Item name="start_time" label="Thời gian / Hạn chót" rules={[{ required: true, message: 'Vui lòng chọn thời gian!' }]}>
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
