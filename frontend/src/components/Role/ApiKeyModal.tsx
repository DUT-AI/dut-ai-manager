import { useState } from 'react';
import {
    Modal,
    Button,
    Table,
    Form,
    Input,
    Space,
    Tag,
    Typography,
    Popconfirm,
    Alert,
    message
} from 'antd';
import { DeleteOutlined, PlusOutlined, KeyOutlined } from '@ant-design/icons';
import { useRoleApiKeys, useCreateApiKey, useRevokeApiKey } from '@/hooks/useApiKeys';
import type { RoleResponse } from '@/types/rbac.types';
import dayjs from 'dayjs';

const { Text, Paragraph } = Typography;

interface ApiKeyModalProps {
    role: RoleResponse | null;
    open: boolean;
    onClose: () => void;
}

const ApiKeyModal = ({ role, open, onClose }: ApiKeyModalProps) => {
    const [form] = Form.useForm();
    const [createdKey, setCreatedKey] = useState<string | null>(null);

    // Hooks
    const { data: apiKeys = [], isLoading } = useRoleApiKeys(role?.id || null);
    const createApiKeyMutation = useCreateApiKey();
    const revokeApiKeyMutation = useRevokeApiKey();

    const handleCreate = async (values: { name: string }) => {
        if (!role) return;

        try {
            const result = await createApiKeyMutation.mutateAsync({
                role_id: role.id,
                name: values.name
            });

            // Show secret key
            if (result.data?.secret_key) {
                setCreatedKey(result.data.secret_key);
                message.success('API Key created!');
                form.resetFields();
            }
        } catch (error) {
            // Error handled by hook
        }
    };

    const handleRevoke = async (id: number) => {
        try {
            await revokeApiKeyMutation.mutateAsync(id);
        } catch (error) {
            // Error handled by hook
        }
    };

    const columns = [
        {
            title: 'Name',
            dataIndex: 'name',
            key: 'name',
            render: (text: string) => <Text strong>{text}</Text>
        },
        {
            title: 'Prefix',
            dataIndex: 'prefix',
            key: 'prefix',
            render: (text: string) => <Tag>{text}</Tag>
        },
        {
            title: 'Created At',
            dataIndex: 'created_at',
            key: 'created_at',
            render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm')
        },
        {
            title: 'Action',
            key: 'action',
            render: (_: any, record: any) => (
                <Popconfirm
                    title="Revoke API Key"
                    description="Are you sure? This action cannot be undone and any system using this key will stop working."
                    onConfirm={() => handleRevoke(record.id)}
                    okText="Yes"
                    cancelText="No"
                >
                    <Button danger size="small" icon={<DeleteOutlined />}>Revoke</Button>
                </Popconfirm>
            )
        }
    ];

    const resetModal = () => {
        setCreatedKey(null);
        form.resetFields();
        onClose();
    };

    return (
        <Modal
            title={
                <Space>
                    <KeyOutlined />
                    <span>Manage API Keys - {role?.name}</span>
                </Space>
            }
            open={open}
            onCancel={resetModal}
            footer={null}
            width={700}
        >
            {/* Success Alert with Secret Key */}
            {createdKey && (
                <Alert
                    message="API Key Created Successfully"
                    description={
                        <div className="mt-2">
                            <Paragraph>
                                This is the only time the secret key will be shown. Please copy it now.
                            </Paragraph>
                            <div className="flex items-center gap-2 bg-gray-50 p-2 rounded border border-gray-200">
                                <Text code copyable className="text-base break-all flex-1">
                                    {createdKey}
                                </Text>
                            </div>
                            <div className="mt-2 text-right">
                                <Button size="small" onClick={() => setCreatedKey(null)}>
                                    I have copied it
                                </Button>
                            </div>
                        </div>
                    }
                    type="success"
                    showIcon
                    className="mb-4"
                />
            )}

            {/* Create Form */}
            <div className="bg-gray-50 p-4 rounded-lg mb-4 border border-gray-100">
                <Text strong className="mb-2 block">Create New API Key</Text>
                <Form layout="inline" form={form} onFinish={handleCreate}>
                    <Form.Item
                        name="name"
                        rules={[{ required: true, message: 'Please enter a name' }]}
                        className="flex-1 mb-0"
                    >
                        <Input placeholder="e.g. Mobile App, Backup Server" />
                    </Form.Item>
                    <Form.Item className="mb-0">
                        <Button
                            type="primary"
                            htmlType="submit"
                            icon={<PlusOutlined />}
                            loading={createApiKeyMutation.isPending}
                        >
                            Generate Key
                        </Button>
                    </Form.Item>
                </Form>
            </div>

            {/* List */}
            <Table
                dataSource={apiKeys || []}
                columns={columns}
                rowKey="id"
                pagination={false}
                loading={isLoading}
                size="small"
                locale={{ emptyText: 'No API Keys found for this role' }}
            />
        </Modal>
    );
};

export default ApiKeyModal;
