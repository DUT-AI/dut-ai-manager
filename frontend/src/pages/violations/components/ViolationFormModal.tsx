import { Modal, Form, Select, DatePicker, Input } from 'antd';
import type { ViolationResponse } from '@/types/activity.types';
import type { UserResponse } from '@/types/user.types';

const { Option } = Select;
const { TextArea } = Input;

interface ViolationFormModalProps {
    isOpen: boolean;
    onCancel: () => void;
    onFinish: (values: any) => void;
    editingItem: ViolationResponse | null;
    loading: boolean;
    users: UserResponse[];
    form: any;
    isMobile?: boolean;
}

const ViolationFormModal = ({
    isOpen,
    onCancel,
    onFinish,
    editingItem,
    loading,
    users,
    form,
    isMobile
}: ViolationFormModalProps) => {
    return (
        <Modal
            title={editingItem ? 'Chỉnh sửa Vi phạm' : 'Ghi nhận Vi phạm mới'}
            open={isOpen}
            onCancel={onCancel}
            onOk={() => form.submit()}
            centered
            confirmLoading={loading}
            destroyOnClose
            okText={editingItem ? 'Lưu thay đổi' : 'Ghi nhận'}
            cancelText="Hủy"
            width={isMobile ? '100%' : 500}
        >
            <Form form={form} layout="vertical" onFinish={onFinish} className="mt-6">
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
    );
};

export default ViolationFormModal;
