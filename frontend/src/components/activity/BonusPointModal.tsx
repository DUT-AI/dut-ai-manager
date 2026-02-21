import { Modal, Form, Select, DatePicker, InputNumber, Input } from 'antd';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';
import type { BonusPointResponse } from '@/types/activity.types';
import type { UserResponse } from '@/types/user.types';

const { Option } = Select;
const { TextArea } = Input;

interface Props {
    open: boolean;
    editingItem: BonusPointResponse | null;
    initialDate: Dayjs;
    users: UserResponse[];
    onSubmit: (values: any) => void;
    onCancel: () => void;
}

export const BonusPointModal = ({ open, editingItem, initialDate, users, onSubmit, onCancel }: Props) => {
    const [form] = Form.useForm();

    const initialValues = editingItem ? {
        user_id: editingItem.user_id,
        points: editingItem.points,
        reason: editingItem.reason,
        date: dayjs(editingItem.date),
    } : { date: initialDate };

    const handleFinish = (values: any) => {
        if (editingItem) {
            const formattedValues = {
                ...values,
                date: values.date.toISOString()
            };
            onSubmit(formattedValues);
        } else {
            const formattedValues = {
                user_ids: values.user_ids,
                points: values.points,
                reason: values.reason,
                date: values.date.toISOString()
            };
            onSubmit(formattedValues);
        }
    };

    return (
        <Modal
            title={editingItem ? "Sửa điểm cộng" : "Thêm điểm cộng"}
            open={open}
            onCancel={onCancel}
            onOk={form.submit}
            destroyOnClose
        >
            <Form form={form} initialValues={initialValues} layout="vertical" onFinish={handleFinish}>
                {editingItem ? (
                    <Form.Item name="user_id" label="Thành viên" rules={[{ required: true, message: 'Vui lòng chọn thành viên!' }]}>
                        <Select
                            disabled
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
                ) : (
                    <Form.Item name="user_ids" label="Thành viên" rules={[{ required: true, message: 'Vui lòng chọn thành viên!' }]}>
                        <Select
                            mode="multiple"
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
                )}
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
    );
};
