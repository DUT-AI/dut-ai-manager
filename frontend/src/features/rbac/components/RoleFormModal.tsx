import { useEffect } from 'react';
import { Form, Input, Modal } from 'antd';
import type { RoleResponse } from '../types/rbac.types';

interface RoleFormModalProps {
    open: boolean;
    editingRole: RoleResponse | null;
    isSubmitting: boolean;
    onCancel: () => void;
    onSubmit: (values: Record<string, unknown>) => Promise<void>;
}

export const RoleFormModal = ({
    open,
    editingRole,
    isSubmitting,
    onCancel,
    onSubmit,
}: RoleFormModalProps) => {
    const [form] = Form.useForm();

    useEffect(() => {
        if (open) {
            if (editingRole) {
                form.setFieldsValue(editingRole);
            } else {
                form.resetFields();
            }
        }
    }, [open, editingRole, form]);

    return (
        <Modal
            title={editingRole ? 'Edit Role' : 'Create Role'}
            open={open}
            onCancel={onCancel}
            onOk={() => form.submit()}
            confirmLoading={isSubmitting}
            destroyOnHidden
        >
            <Form form={form} layout="vertical" onFinish={onSubmit} className="mt-4">
                <Form.Item
                    name="name"
                    label="Role Name"
                    rules={[{ required: true, message: 'Please input role name!' }]}
                >
                    <Input placeholder="e.g. admin, leader, teammate" />
                </Form.Item>
                <Form.Item name="description" label="Description">
                    <Input.TextArea placeholder="Describe what this role is for" rows={3} />
                </Form.Item>
            </Form>
        </Modal>
    );
};
