import { List, Card, Button, Popconfirm, Typography, Avatar, Tooltip } from 'antd';
import { EditOutlined, DeleteOutlined, TeamOutlined, UserOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { TeamResponse } from '../types/team.types';

const { Text } = Typography;

interface TeamMobileListProps {
    teams: TeamResponse[];
    isLoading: boolean;
    onEdit: (item: TeamResponse) => void;
    onDelete: (id: number) => void;
}

export const TeamMobileList = ({ teams, isLoading, onEdit, onDelete }: TeamMobileListProps) => (
    <div className="mt-4 px-3">
        <List
            dataSource={teams}
            loading={isLoading}
            split={false}
            renderItem={(record) => (
                <List.Item className="px-2 !mb-4 !border-0">
                    <Card
                        className="w-full shadow-sm border-gray-100 overflow-hidden"
                        styles={{ body: { padding: '16px' } }}
                        actions={[
                            <Button
                                key="edit"
                                type="text"
                                icon={<EditOutlined />}
                                onClick={() => onEdit(record)}
                            >
                                Sửa
                            </Button>,
                            <Popconfirm
                                key="delete"
                                title="Xóa nhóm này?"
                                description="Hành động này không thể hoàn tác"
                                onConfirm={() => onDelete(record.id)}
                                okText="Xóa"
                                cancelText="Hủy"
                            >
                                <Button type="text" danger icon={<DeleteOutlined />}>Xóa</Button>
                            </Popconfirm>
                        ]}
                    >
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-500 shrink-0">
                                <TeamOutlined className="text-xl" />
                            </div>
                            <div className="flex flex-col min-w-0 flex-1">
                                <Text strong className="text-base truncate">{record.team_name}</Text>
                                <Text type="secondary" className="text-xs">{record.member_count} thành viên</Text>
                            </div>
                        </div>

                        <div>
                            <Text type="secondary" className="block mb-2 text-xs uppercase font-bold tracking-wider">Thành viên</Text>
                            <Avatar.Group max={{ count: 6, style: { color: '#f56a00', backgroundColor: '#fde3cf' } }}>
                                {record.members.map(m => (
                                    <Tooltip title={m.user_name} key={m.user_id}>
                                        <Avatar src={m.user_avatar_url} icon={<UserOutlined />} />
                                    </Tooltip>
                                ))}
                            </Avatar.Group>
                        </div>

                        <div className="mt-4 pt-3 border-t border-gray-50 flex justify-between items-center text-gray-400 text-[10px]">
                            <span>Ngày tạo: {dayjs(record.created_at).format('DD/MM/YYYY')}</span>
                        </div>
                    </Card>
                </List.Item>
            )}
        />
    </div>
);
