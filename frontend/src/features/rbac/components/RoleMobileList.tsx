import { Button, Card, List, Popconfirm, Tag, Typography } from 'antd';
import {
    DeleteOutlined,
    EditOutlined,
    KeyOutlined,
    SafetyCertificateOutlined,
} from '@ant-design/icons';
import type { RoleResponse } from '../types/rbac.types';

const { Text } = Typography;

interface RoleMobileListProps {
    roles: RoleResponse[];
    isLoading: boolean;
    canUpdateRole: boolean;
    canDeleteRole: boolean;
    onOpenPerms: (role: RoleResponse) => void;
    onOpenApiKeys: (role: RoleResponse) => void;
    onEdit: (role: RoleResponse) => void;
    onDelete: (id: number) => void;
}

export const RoleMobileList = ({
    roles,
    isLoading,
    canUpdateRole,
    canDeleteRole,
    onOpenPerms,
    onOpenApiKeys,
    onEdit,
    onDelete,
}: RoleMobileListProps) => (
    <div className="mt-4 px-3">
        <List
            dataSource={roles}
            loading={isLoading}
            split={false}
            renderItem={(role) => (
                <List.Item className="px-2 !mb-4 !border-0">
                    <Card
                        className="w-full shadow-sm border-gray-100 overflow-hidden"
                        styles={{ body: { padding: '16px' } }}
                        actions={[
                            <Button
                                key="perms"
                                type="text"
                                icon={<KeyOutlined />}
                                onClick={() => onOpenPerms(role)}
                                disabled={!canUpdateRole}
                            >
                                Perms
                            </Button>,
                            <Button
                                key="api-keys"
                                type="text"
                                icon={<SafetyCertificateOutlined />}
                                onClick={() => onOpenApiKeys(role)}
                                disabled={!canUpdateRole}
                            >
                                API Keys
                            </Button>,
                            <Button
                                key="edit"
                                type="text"
                                icon={<EditOutlined />}
                                onClick={() => onEdit(role)}
                                disabled={!canUpdateRole}
                            >
                                Edit
                            </Button>,
                            <Popconfirm
                                key="delete"
                                title="Delete this role?"
                                onConfirm={() => onDelete(role.id)}
                                disabled={!canDeleteRole}
                                okText="Delete"
                                cancelText="Cancel"
                            >
                                <Button
                                    type="text"
                                    danger
                                    icon={<DeleteOutlined />}
                                    disabled={!canDeleteRole}
                                >
                                    Delete
                                </Button>
                            </Popconfirm>,
                        ]}
                    >
                        <div className="flex items-center justify-between mb-4">
                            <Tag
                                color={role.name === 'admin' ? 'volcano' : role.name === 'leader' ? 'blue' : 'green'}
                                className="uppercase font-bold m-0 text-base py-1 px-3"
                            >
                                {role.name}
                            </Tag>
                        </div>

                        <div>
                            <Text
                                type="secondary"
                                className="block mb-1 text-xs uppercase font-bold tracking-wider"
                            >
                                Description
                            </Text>
                            <Text>{role.description || 'No description provided.'}</Text>
                        </div>
                    </Card>
                </List.Item>
            )}
        />
    </div>
);
