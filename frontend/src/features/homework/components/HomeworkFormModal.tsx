import { useState, useEffect, useMemo, useCallback } from 'react';
import { Modal, Form, Input, DatePicker, Select, message, Divider, Button, Space, Badge, Tag, Typography } from 'antd';
import { TeamOutlined, UserOutlined, CheckOutlined, ClearOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { Homework } from '@/features/homework/types/homework.types';
import type { UserResponse } from '@/features/users/types/user.types';
import type { TeamResponse } from '@/features/teams/types/team.types';
import { homeworkService } from '@/features/homework/services/homework.service';

const { Text } = Typography;

interface Props {
    open: boolean;
    editingItem: Homework | null;
    users: UserResponse[];
    teams: TeamResponse[];
    onSuccess: () => void;
    onCancel: () => void;
}

export const HomeworkFormModal = ({
    open,
    editingItem,
    users,
    teams,
    onSuccess,
    onCancel
}: Props) => {
    const [form] = Form.useForm();
    const [loading, setLoading] = useState(false);
    const [selectedTeamIds, setSelectedTeamIds] = useState<number[]>([]);
    const [selectedAssigneeIds, setSelectedAssigneeIds] = useState<number[]>([]);
    const isEditing = !!editingItem;

    // Helper map: teamId -> array of member user_ids
    const teamMemberMap = useMemo(() => {
        const map = new Map<number, number[]>();
        teams.forEach(t => {
            const memberIds = (t.members || []).map(m => m.user_id);
            map.set(t.id, memberIds);
        });
        return map;
    }, [teams]);

    // Compute which teams have ALL members present in a given user list
    const detectMatchingTeams = useCallback((assigneeIds: number[]) => {
        const idSet = new Set(assigneeIds);
        const matched: number[] = [];
        teams.forEach(t => {
            const memberIds = (t.members || []).map(m => m.user_id);
            if (memberIds.length > 0 && memberIds.every(uid => idSet.has(uid))) {
                matched.push(t.id);
            }
        });
        return matched;
    }, [teams]);

    useEffect(() => {
        if (open) {
            if (editingItem) {
                const initialAssignees = editingItem.assignee_ids || [];
                const matchedTeams = detectMatchingTeams(initialAssignees);
                setSelectedTeamIds(matchedTeams);
                setSelectedAssigneeIds(initialAssignees);

                form.setFieldsValue({
                    title: editingItem.title,
                    deadline: dayjs(editingItem.deadline),
                    link: editingItem.link || '',
                    slug: editingItem.slug || '',
                    team_ids: matchedTeams,
                    assignee_ids: initialAssignees,
                });
            } else {
                setSelectedTeamIds([]);
                setSelectedAssigneeIds([]);
                form.resetFields();
            }
        }
    }, [open, editingItem, detectMatchingTeams, form]);

    // Handle Team Selection Change (Resolves team members into assignee_ids)
    const handleTeamChange = (newTeamIds: number[]) => {
        const currentAssignees = form.getFieldValue('assignee_ids') || [];
        const currentAssigneeSet = new Set<number>(currentAssignees);

        // Teams that were newly selected
        const newlyAdded = newTeamIds.filter(id => !selectedTeamIds.includes(id));
        newlyAdded.forEach(tId => {
            const memberIds = teamMemberMap.get(tId) || [];
            memberIds.forEach(uid => currentAssigneeSet.add(uid));
        });

        // Teams that were deselected
        const newlyRemoved = selectedTeamIds.filter(id => !newTeamIds.includes(id));
        newlyRemoved.forEach(tId => {
            const memberIds = teamMemberMap.get(tId) || [];
            memberIds.forEach(uid => {
                // Only remove if this user is NOT in another currently selected team
                const belongsToOtherSelectedTeam = newTeamIds.some(otherTId => {
                    const otherMembers = teamMemberMap.get(otherTId) || [];
                    return otherMembers.includes(uid);
                });
                if (!belongsToOtherSelectedTeam) {
                    currentAssigneeSet.delete(uid);
                }
            });
        });

        const finalAssignees = Array.from(currentAssigneeSet);
        setSelectedTeamIds(newTeamIds);
        setSelectedAssigneeIds(finalAssignees);

        form.setFieldsValue({
            team_ids: newTeamIds,
            assignee_ids: finalAssignees,
        });
    };

    // Handle Direct Assignee Selection Change
    const handleAssigneeChange = (newAssignees: number[]) => {
        setSelectedAssigneeIds(newAssignees);
        // Automatically re-evaluate matching teams based on updated assignees
        const matchedTeams = detectMatchingTeams(newAssignees);
        setSelectedTeamIds(matchedTeams);
        form.setFieldsValue({
            team_ids: matchedTeams,
            assignee_ids: newAssignees,
        });
    };

    // Quick Action: Select All Users
    const handleSelectAll = () => {
        const allUserIds = users.map(u => u.id).filter((id): id is number => id !== undefined);
        const allTeamIds = teams.map(t => t.id);
        setSelectedTeamIds(allTeamIds);
        setSelectedAssigneeIds(allUserIds);
        form.setFieldsValue({
            team_ids: allTeamIds,
            assignee_ids: allUserIds,
        });
    };

    // Quick Action: Clear All
    const handleClearAll = () => {
        setSelectedTeamIds([]);
        setSelectedAssigneeIds([]);
        form.setFieldsValue({
            team_ids: [],
            assignee_ids: [],
        });
    };

    const handleFinish = async (values: any) => {
        setLoading(true);
        try {
            const payload = {
                title: values.title.trim(),
                deadline: values.deadline.format('YYYY-MM-DDTHH:mm:ss'),
                link: values.link?.trim() || '',
                slug: values.slug?.trim() || null,
                assignee_ids: values.assignee_ids || [],
            };

            if (isEditing) {
                await homeworkService.update(editingItem!.id, payload);
                message.success('Cập nhật bài tập thành công');
            } else {
                await homeworkService.create(payload);
                message.success('Tạo bài tập thành công');
            }
            onSuccess();
        } catch (error: any) {
            message.error(error?.response?.data?.detail || error?.message || 'Thao tác thất bại');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Modal
            title={
                <div className="flex items-center gap-2">
                    <span className="font-semibold text-lg">
                        {isEditing ? 'Chỉnh sửa bài tập' : 'Tạo bài tập mới'}
                    </span>
                </div>
            }
            open={open}
            onCancel={onCancel}
            onOk={form.submit}
            confirmLoading={loading}
            destroyOnHidden
            width={640}
        >
            <Form form={form} layout="vertical" onFinish={handleFinish} className="mt-3">
                <Form.Item
                    name="title"
                    label={<span className="font-medium">Tiêu đề bài tập</span>}
                    rules={[{ required: true, message: 'Vui lòng nhập tiêu đề bài tập' }]}
                >
                    <Input placeholder="Ví dụ: Lesson 1: Python Basics..." size="large" />
                </Form.Item>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Form.Item
                        name="deadline"
                        label={<span className="font-medium">Hạn nộp</span>}
                        rules={[
                            { required: true, message: 'Vui lòng chọn hạn nộp' },
                            {
                                validator: (_, value) => {
                                    if (value && !isEditing && value.isBefore(dayjs())) {
                                        return Promise.reject(new Error('Hạn nộp không được ở trong quá khứ!'));
                                    }
                                    return Promise.resolve();
                                }
                            }
                        ]}
                    >
                        <DatePicker
                            showTime
                            className="w-full"
                            format="DD/MM/YYYY HH:mm"
                            placeholder="Chọn ngày và giờ..."
                            disabledDate={(current) => !isEditing && current && current.isBefore(dayjs().startOf('day'))}
                        />
                    </Form.Item>

                    <Form.Item
                        name="slug"
                        label={<span className="font-medium">Slug bài tập (Quiz API)</span>}
                        extra={
                            <span className="text-xs text-gray-500">
                                Hệ thống tự động trích xuất từ link. Nếu link không có slug chuẩn, vui lòng nhập slug thủ công.
                            </span>
                        }
                    >
                        <Input placeholder="Ví dụ: python-basics" allowClear />
                    </Form.Item>
                </div>

                <Form.Item
                    name="link"
                    label={<span className="font-medium">Đường dẫn bài tập / Quiz URL</span>}
                    rules={[{ required: true, message: 'Vui lòng nhập link bài tập' }]}
                >
                    <Input
                        placeholder="https://quiz.dutai.site/homeworks/..."
                        onChange={(e) => {
                            const val = e.target.value;
                            const currentSlug = form.getFieldValue('slug');
                            if (!currentSlug && val) {
                                const match = val.match(/\/(?:homeworks|game|lessons)\/([^/?#]+)/);
                                if (match) {
                                    form.setFieldsValue({ slug: match[1] });
                                } else if (val.startsWith('http://') || val.startsWith('https://')) {
                                    const parts = val.replace(/\/+$/, '').split('/');
                                    const candidate = parts[parts.length - 1]?.split('?')[0]?.split('#')[0];
                                    if (candidate && candidate.length > 1 && !candidate.includes(' ')) {
                                        form.setFieldsValue({ slug: candidate });
                                    }
                                }
                            }
                        }}
                    />
                </Form.Item>

                <Divider className="!my-4">
                    <div className="flex items-center gap-2">
                        <span className="font-medium text-sm text-indigo-700">Phân công giao bài</span>
                        <Badge
                            count={selectedAssigneeIds.length}
                            overflowCount={999}
                            style={{ backgroundColor: selectedAssigneeIds.length > 0 ? '#4f46e5' : '#9ca3af' }}
                        />
                    </div>
                </Divider>

                <div className="bg-slate-50/80 p-3.5 rounded-xl border border-slate-200/80 mb-4">
                    <div className="flex items-center justify-between mb-2">
                        <Text className="text-xs font-semibold text-gray-600 uppercase tracking-wider">
                            Giao nhanh theo Team
                        </Text>
                        <Space size="small">
                            <Button
                                type="link"
                                size="small"
                                icon={<CheckOutlined />}
                                onClick={handleSelectAll}
                                className="!p-0 !text-xs !text-indigo-600 font-medium"
                            >
                                Chọn tất cả ({users.length})
                            </Button>
                            <span className="text-gray-300">|</span>
                            <Button
                                type="link"
                                size="small"
                                danger
                                icon={<ClearOutlined />}
                                onClick={handleClearAll}
                                className="!p-0 !text-xs font-medium"
                            >
                                Xóa tất cả
                            </Button>
                        </Space>
                    </div>

                    <Form.Item name="team_ids" className="!mb-2">
                        <Select
                            mode="multiple"
                            placeholder="Chọn một hoặc nhiều Team để tự động thêm tất cả thành viên..."
                            allowClear
                            value={selectedTeamIds}
                            onChange={handleTeamChange}
                            filterOption={(input: string, option: any) =>
                                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                            }
                            options={teams.map(t => ({
                                label: `${t.team_name} (${t.member_count} thành viên)`,
                                value: t.id
                            }))}
                            tagRender={({ label, closable, onClose }) => (
                                <Tag
                                    color="indigo"
                                    closable={closable}
                                    onClose={onClose}
                                    className="flex items-center gap-1 font-medium my-0.5"
                                >
                                    <TeamOutlined /> {label}
                                </Tag>
                            )}
                        />
                    </Form.Item>
                    <p className="text-xs text-gray-500 m-0">
                        💡 Khi chọn Team, toàn bộ thành viên trong nhóm sẽ được tự động phân giải và lưu trực tiếp vào danh sách người làm bài.
                    </p>
                </div>

                <Form.Item
                    name="assignee_ids"
                    label={
                        <div className="flex items-center justify-between w-full">
                            <span className="flex items-center gap-2 font-medium">
                                <UserOutlined /> Danh sách thành viên được giao bài
                            </span>
                            <span className="text-xs text-indigo-600 font-normal">
                                {selectedAssigneeIds.length} người được chọn
                            </span>
                        </div>
                    }
                    rules={[
                        {
                            validator: (_, value) => {
                                if (!value || value.length === 0) {
                                    return Promise.reject(new Error('Vui lòng chọn ít nhất 1 thành viên hoặc 1 team'));
                                }
                                return Promise.resolve();
                            }
                        }
                    ]}
                >
                    <Select
                        mode="multiple"
                        placeholder="Tìm và chọn các thành viên cụ thể..."
                        allowClear
                        value={selectedAssigneeIds}
                        onChange={handleAssigneeChange}
                        filterOption={(input: string, option: any) =>
                            (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                        }
                        options={users.map(u => ({
                            label: `${u.name} (${u.email})`,
                            value: u.id
                        }))}
                        maxTagCount="responsive"
                    />
                </Form.Item>
            </Form>
        </Modal>
    );
};
