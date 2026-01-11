import { useEffect } from 'react';
import { Modal, Form, Select, DatePicker, Input } from 'antd';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';
import type { ViolationResponse } from '@/types/activity.types';
import type { UserResponse } from '@/types/user.types';

const { Option } = Select;
const { TextArea } = Input;

interface Props {
    open: boolean;
    editingItem: ViolationResponse | null;
    initialDate: Dayjs;
    users: UserResponse[];
    onSubmit: (values: any) => void;
    onCancel: () => void;
}

export const ViolationModal = ({ open, editingItem, initialDate, users, onSubmit, onCancel }: Props) => {
    const [form] = Form.useForm();

    useEffect(() => {
        if (open) {
            if (editingItem) {
                form.setFieldsValue({
                    user_id: editingItem.user_id,
                    reason: editingItem.reason,
                    date: dayjs(editingItem.date)
                });
            } else {
                form.resetFields();
                form.setFieldValue('date', initialDate);
            }
        }
    }, [open, editingItem, initialDate, form]);

    const handleFinish = (values: any) => {
        const formattedValues = {
            user_id: values.user_id,
            reason: values.reason,
            date: values.date.toISOString()
        };
        onSubmit(formattedValues);
    };

    return (
        <Modal
            title={editingItem ? "Sửa vi phạm" : "Ghi nhận vi phạm"}
            open={open}
            onCancel={onCancel}
            onOk={form.submit}
            destroyOnClose
        >
            <Form form={form} layout="vertical" onFinish={handleFinish}>
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
    );
};
