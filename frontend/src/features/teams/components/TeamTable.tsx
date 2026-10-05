import { Table, Space, Button, Popconfirm, Typography, Tooltip, Avatar } from 'antd';
import { EditOutlined, DeleteOutlined, TeamOutlined, UserOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { TeamResponse } from '../types/team.types';

const { Text } = Typography;

interface TeamTableProps {
    teams: TeamResponse[];
    isLoading: boolean;
    onEdit: (item: TeamResponse) => void;
    onDelete: (id: number) => void;
}

export const TeamTable = ({ teams, isLoading, onEdit, onDelete }: TeamTableProps) => {
    const columns = [
        {
            title: 'Tên nhóm',
            dataIndex: 'team_name',
            key: 'team_name',
            render: (text: string) => (
                <Space>
                    <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-500">
                        <TeamOutlined />
                    </div>
                    <Text strong>{text}</Text>
                </Space>
            )
        },
        {
            title: 'Thành viên',
            key: 'members',
            render: (_: unknown, record: TeamResponse) => (
                <Space direction="vertical" size={4} className="max-w-[300px]">
                    <Avatar.Group max={{ count: 5, style: { color: '#f56a00', backgroundColor: '#fde3cf' } }} size="small">
                        {record.members.map(m => (
                            <Tooltip title={m.user_name} key={m.user_id}>
                                <Avatar src={m.user_avatar_url} icon={<UserOutlined />} />
                            </Tooltip>
                        ))}
                    </Avatar.Group>
                    <Text type="secondary" className="text-xs">{record.member_count} thành viên</Text>
                </Space>
            )
        },
        {
            title: 'Ngày tạo',
            dataIndex: 'created_at',
            key: 'created_at',
            render: (date: string) => dayjs(date).format('DD/MM/YYYY HH:mm')
        },
        {
            title: 'Thao tác',
            key: 'actions',
            render: (_: unknown, record: TeamResponse) => (
                <Space>
                    <Button
                        icon={<EditOutlined />}
                        onClick={() => onEdit(record)}
                    />
                    <Popconfirm
                        title="Xóa nhóm này?"
                        description="Hành động này không thể hoàn tác"
                        onConfirm={() => onDelete(record.id)}
                        okText="Xóa"
                        cancelText="Hủy"
                    >
                        <Button icon={<DeleteOutlined />} danger />
                    </Popconfirm>
                </Space>
            )
        }
    ];

    return (
        <Table
            columns={columns}
            dataSource={teams}
            rowKey="id"
            loading={isLoading}
            className="custom-table"
            pagination={{
                defaultPageSize: 20,
                pageSizeOptions: ['10', '20', '50', '100'],
                showSizeChanger: true,
                showTotal: (total, range) => `Hiển thị ${range[0]}-${range[1]} trên tổng số ${total} nhóm`,
            }}
        />
    );
};
