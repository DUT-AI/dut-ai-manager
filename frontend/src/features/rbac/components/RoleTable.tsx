import { Button, Popconfirm, Space, Table, Tag } from 'antd';
import {
    DeleteOutlined,
    EditOutlined,
    KeyOutlined,
    SafetyCertificateOutlined,
} from '@ant-design/icons';
import type { RoleResponse } from '../types/rbac.types';

interface RoleTableProps {
    roles: RoleResponse[];
    isLoading: boolean;
    canUpdateRole: boolean;
    canDeleteRole: boolean;
    onOpenPerms: (role: RoleResponse) => void;
    onOpenApiKeys: (role: RoleResponse) => void;
    onEdit: (role: RoleResponse) => void;
    onDelete: (id: number) => void;
}

export const RoleTable = ({
    roles,
    isLoading,
    canUpdateRole,
    canDeleteRole,
    onOpenPerms,
    onOpenApiKeys,
    onEdit,
    onDelete,
}: RoleTableProps) => {
    const columns = [
        {
            title: 'Role Name',
            dataIndex: 'name',
            key: 'name',
            render: (name: string) => (
                <Tag
                    color={name === 'admin' ? 'volcano' : name === 'leader' ? 'blue' : 'green'}
                    className="uppercase font-bold"
                >
                    {name}
                </Tag>
            ),
        },
        {
            title: 'Description',
            dataIndex: 'description',
            key: 'description',
            render: (desc: string | null) => desc || 'No description provided.',
        },
        {
            title: 'Actions',
            key: 'actions',
            width: 280,
            render: (_: unknown, record: RoleResponse) => (
                <Space>
                    <Button
                        icon={<KeyOutlined />}
                        onClick={() => onOpenPerms(record)}
                        disabled={!canUpdateRole}
                    >
                        Manage Perms
                    </Button>
                    <Button
                        icon={<SafetyCertificateOutlined />}
                        onClick={() => onOpenApiKeys(record)}
                        disabled={!canUpdateRole}
                    >
                        API Keys
                    </Button>
                    <Button
                        icon={<EditOutlined />}
                        onClick={() => onEdit(record)}
                        disabled={!canUpdateRole}
                    />
                    <Popconfirm
                        title="Are you sure to delete this role?"
                        onConfirm={() => onDelete(record.id)}
                        disabled={!canDeleteRole}
                        okText="Delete"
                        cancelText="Cancel"
                    >
                        <Button icon={<DeleteOutlined />} danger disabled={!canDeleteRole} />
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    return (
        <Table
            columns={columns}
            dataSource={roles}
            rowKey="id"
            loading={isLoading}
            pagination={false}
            className="border border-gray-100 rounded-lg"
        />
    );
};
