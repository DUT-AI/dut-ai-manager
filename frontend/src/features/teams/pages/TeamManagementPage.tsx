import { useState, useMemo } from 'react';
import {
    Button,
    Card,
    Space,
    Form,
    Input,
    message,
    Typography,
    Grid,
    Tag
} from 'antd';
import {
    PlusOutlined,
    TeamOutlined,
    SearchOutlined
} from '@ant-design/icons';
import { useTeams, useCreateTeam, useUpdateTeam, useDeleteTeam } from '../hooks/useTeams';
import { useUsers } from '@/features/users';
import { useAuth } from '@/features/auth';
import type { TeamResponse, TeamCreate } from '@/features/teams/types/team.types';
import { motion, type Variants } from 'motion/react';
import { TeamTable, TeamMobileList, TeamFormModal } from '../components';

const { Title, Text } = Typography;

const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.1
        }
    }
};

const itemVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
        opacity: 1,
        y: 0,
        transition: { duration: 0.4, ease: "easeOut" }
    }
};

const TeamManagementPage = () => {
    useAuth();
    const screens = Grid.useBreakpoint();
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingItem, setEditingItem] = useState<TeamResponse | null>(null);
    const [form] = Form.useForm();

    // TanStack Query hooks
    const { data, isLoading } = useTeams();
    const teams = data || [];
    const { data: users = [] } = useUsers();
    const createTeam = useCreateTeam();
    const updateTeam = useUpdateTeam();
    const deleteTeam = useDeleteTeam();

    const [searchKeyword, setSearchKeyword] = useState('');

    const filteredTeams = useMemo(() => {
        if (!searchKeyword.trim()) return teams;
        const lower = searchKeyword.toLowerCase().trim();
        return teams.filter(t => t.team_name.toLowerCase().includes(lower));
    }, [teams, searchKeyword]);

    const handleCreateOrUpdate = async (values: Record<string, unknown>) => {
        try {
            const payload: TeamCreate = {
                team_name: String(values.team_name || ''),
                member_ids: values.member_ids as number[] | undefined
            };

            if (editingItem) {
                await updateTeam.mutateAsync({ id: editingItem.id, data: payload });
                message.success('Cập nhật nhóm thành công');
            } else {
                await createTeam.mutateAsync(payload);
                message.success('Tạo nhóm mới thành công');
            }
            setIsModalOpen(false);
            form.resetFields();
        } catch (error: unknown) {
            const err = error as { response?: { data?: { message?: string } } };
            message.error(err?.response?.data?.message || 'Thao tác thất bại');
        }
    };

    const handleDelete = async (id: number) => {
        try {
            await deleteTeam.mutateAsync(id);
            message.success('Xóa nhóm thành công');
        } catch (error: unknown) {
            const err = error as { response?: { data?: { message?: string } } };
            message.error(err?.response?.data?.message || 'Xóa thất bại');
        }
    };

    const handleEdit = (item: TeamResponse) => {
        setEditingItem(item);
        form.setFieldsValue({
            team_name: item.team_name,
            member_ids: item.members.map(m => m.user_id)
        });
        setIsModalOpen(true);
    };

    return (
        <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="p-4 md:p-6"
        >
            <Card className={!screens.md ? "bg-transparent shadow-none border-none" : "shadow-sm border-gray-100 rounded-xl overflow-hidden"} styles={{ body: { padding: !screens.md ? 0 : undefined } }}>
                <motion.div variants={itemVariants} className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6 px-3 md:px-0">
                    <Space size="middle">
                        <div className="hidden md:flex w-12 h-12 rounded-xl bg-indigo-50 items-center justify-center text-indigo-500">
                            <TeamOutlined className="text-2xl" />
                        </div>
                        <div>
                            <div className="flex items-center gap-2">
                                <Title level={3} className="!mb-0 text-xl md:text-2xl text-indigo-600">Quản lý Nhóm</Title>
                                <Tag color="blue" className="font-semibold">{teams.length} nhóm</Tag>
                            </div>
                            <Text type="secondary" className="text-xs md:text-sm">Tổ chức thành viên vào các nhóm chức năng</Text>
                        </div>
                    </Space>
                    <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 w-full md:w-auto">
                        <Input
                            placeholder="Tìm kiếm nhóm..."
                            prefix={<SearchOutlined className="text-gray-400" />}
                            value={searchKeyword}
                            onChange={(e) => setSearchKeyword(e.target.value)}
                            allowClear
                            className="w-full sm:w-60"
                        />
                        <Button
                            type="primary"
                            icon={<PlusOutlined />}
                            onClick={() => {
                                setEditingItem(null);
                                form.resetFields();
                                setIsModalOpen(true);
                            }}
                            className="w-full sm:w-auto bg-linear-to-r from-indigo-500 to-purple-600 border-none shadow-md h-10 px-6 font-semibold"
                        >
                            Tạo Nhóm mới
                        </Button>
                    </div>
                </motion.div>

                {!screens.md ? (
                    <motion.div variants={itemVariants}>
                        <TeamMobileList
                            teams={filteredTeams}
                            isLoading={isLoading}
                            onEdit={handleEdit}
                            onDelete={handleDelete}
                        />
                    </motion.div>
                ) : (
                    <motion.div variants={itemVariants}>
                        <TeamTable
                            teams={filteredTeams}
                            isLoading={isLoading}
                            onEdit={handleEdit}
                            onDelete={handleDelete}
                        />
                    </motion.div>
                )}
            </Card>

            <TeamFormModal
                isOpen={isModalOpen}
                onCancel={() => setIsModalOpen(false)}
                onFinish={handleCreateOrUpdate}
                editingItem={editingItem}
                loading={createTeam.isPending || updateTeam.isPending}
                users={users}
                form={form}
                isMobile={!screens.md}
            />
        </motion.div>
    );
};

export default TeamManagementPage;
