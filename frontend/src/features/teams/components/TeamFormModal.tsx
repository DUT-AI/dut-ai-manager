import { Modal, Form, Input, Select, type FormInstance } from 'antd';
import type { TeamResponse } from '../types/team.types';
import type { UserResponse } from '@/features/users/types/user.types';

const { Option } = Select;

interface TeamFormModalProps {
    isOpen: boolean;
    onCancel: () => void;
    onFinish: (values: Record<string, unknown>) => void;
    editingItem: TeamResponse | null;
    loading: boolean;
    users: UserResponse[];
    form: FormInstance;
    isMobile?: boolean;
}

export const TeamFormModal = ({
    isOpen,
    onCancel,
    onFinish,
    editingItem,
    loading,
    users,
    form,
    isMobile
}: TeamFormModalProps) => {
    return (
        <Modal
            title={editingItem ? 'Chỉnh sửa Nhóm' : 'Tạo Nhóm mới'}
            open={isOpen}
            onCancel={onCancel}
            onOk={() => form.submit()}
            centered
            confirmLoading={loading}
            destroyOnClose
            okText={editingItem ? 'Lưu thay đổi' : 'Tạo mới'}
            cancelText="Hủy"
            width={isMobile ? '100%' : 520}
        >
            <Form form={form} layout="vertical" onFinish={onFinish} className="mt-4">
                <Form.Item
                    name="team_name"
                    label="Tên nhóm"
                    rules={[{ required: true, message: 'Vui lòng nhập tên nhóm' }]}
                >
                    <Input placeholder="Ví dụ: Đội AI, Đội Backend..." />
                </Form.Item>

                <Form.Item
                    name="member_ids"
                    label="Thành viên"
                >
                    <Select
                        mode="multiple"
                        allowClear
                        showSearch
                        style={{ width: '100%' }}
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
            </Form>
        </Modal>
    );
};
