import { useCallback, useEffect, useMemo, useState } from 'react';
import { Modal, Form, Select, DatePicker, Input, message, Switch, Button, Space, Typography, Tag, Divider, Badge } from 'antd';
import { TeamOutlined, UserOutlined, CheckOutlined, ClearOutlined } from '@ant-design/icons';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';
import type { UserResponse } from '@/features/users/types/user.types';
import { teamService } from '@/features/teams/services/team.service';
import type { TeamResponse } from '@/features/teams/types/team.types';
import type { MeetingResponse } from '@/features/meeting/types/meeting.types';

const { TextArea } = Input;
const { RangePicker } = DatePicker;
const { Text } = Typography;

interface Props {
    open: boolean;
    editingItem?: MeetingResponse | null;
    initialDate: Dayjs;
    users: UserResponse[];
    onSubmit: (values: any) => void;
    onCancel: () => void;
}

export const MeetingModal = ({ open, editingItem, initialDate, users, onSubmit, onCancel }: Props) => {
    const [form] = Form.useForm();
    const [teams, setTeams] = useState<TeamResponse[]>([]);
    const [loadingTeams, setLoadingTeams] = useState(false);
    const [selectedTeamIds, setSelectedTeamIds] = useState<number[]>([]);
    const [selectedUserIds, setSelectedUserIds] = useState<number[]>([]);

    const initialValues = editingItem ? {
        title: editingItem.title,
        content: editingItem.content,
        require_check_in: editingItem.require_check_in,
        enable_evaluation: editingItem.enable_evaluation ?? false,
        time_range: [dayjs(editingItem.start_time), dayjs(editingItem.end_time)],
        user_ids: editingItem.participants.map(p => p.user_id),
    } : {
        time_range: [
            initialDate.hour(19).minute(0).second(0),
            initialDate.hour(21).minute(0).second(0),
        ],
        require_check_in: true,
        enable_evaluation: false,
    };

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
    const detectMatchingTeams = useCallback((userIds: number[]) => {
        const idSet = new Set(userIds);
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
        fetchTeams();
    }, []);

    useEffect(() => {
        if (open) {
            if (editingItem) {
                const initialUserIds = editingItem.participants.map(p => p.user_id);
                const matchedTeams = detectMatchingTeams(initialUserIds);
                setSelectedTeamIds(matchedTeams);
                setSelectedUserIds(initialUserIds);

                form.setFieldsValue({
                    title: editingItem.title,
                    content: editingItem.content,
                    require_check_in: editingItem.require_check_in,
                    enable_evaluation: editingItem.enable_evaluation ?? false,
                    time_range: [dayjs(editingItem.start_time), dayjs(editingItem.end_time)],
                    team_ids: matchedTeams,
                    user_ids: initialUserIds,
                });
            } else {
                setSelectedTeamIds([]);
                setSelectedUserIds([]);
                form.setFieldsValue({
                    title: '',
                    content: '',
                    time_range: [
                        initialDate.hour(19).minute(0).second(0),
                        initialDate.hour(21).minute(0).second(0),
                    ],
                    require_check_in: true,
                    enable_evaluation: false,
                    team_ids: [],
                    user_ids: [],
                });
            }
        }
    }, [open, editingItem, initialDate, detectMatchingTeams, form]);

    const fetchTeams = async () => {
        setLoadingTeams(true);
        try {
            const res = await teamService.getTeams();
            if (res.is_success) {
                setTeams(res.data || []);
            }
        } catch (error) {
            console.error('Failed to fetch teams', error);
        } finally {
            setLoadingTeams(false);
        }
    };

    // Handle Team Selection Change (Resolves team members into user_ids)
    const handleTeamChange = (newTeamIds: number[]) => {
        const currentUserIds = form.getFieldValue('user_ids') || [];
        const currentUserSet = new Set<number>(currentUserIds);

        // Teams that were newly selected
        const newlyAdded = newTeamIds.filter(id => !selectedTeamIds.includes(id));
        newlyAdded.forEach(tId => {
            const memberIds = teamMemberMap.get(tId) || [];
            memberIds.forEach(uid => currentUserSet.add(uid));
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
                    currentUserSet.delete(uid);
                }
            });
        });

        const finalUsers = Array.from(currentUserSet);
        setSelectedTeamIds(newTeamIds);
        setSelectedUserIds(finalUsers);

        form.setFieldsValue({
            team_ids: newTeamIds,
            user_ids: finalUsers,
        });
    };

    // Handle Direct User Selection Change
    const handleUserChange = (newUserIds: number[]) => {
        setSelectedUserIds(newUserIds);
        const matchedTeams = detectMatchingTeams(newUserIds);
        setSelectedTeamIds(matchedTeams);
        form.setFieldsValue({
            team_ids: matchedTeams,
            user_ids: newUserIds,
        });
    };

    // Quick Action: Select All Users
    const handleSelectAll = () => {
        const allUserIds = users.map(u => u.id).filter((id): id is number => id !== undefined);
        const allTeamIds = teams.map(t => t.id);
        setSelectedTeamIds(allTeamIds);
        setSelectedUserIds(allUserIds);
        form.setFieldsValue({
            team_ids: allTeamIds,
            user_ids: allUserIds,
        });
    };

    // Quick Action: Clear All
    const handleClearAll = () => {
        setSelectedTeamIds([]);
        setSelectedUserIds([]);
        form.setFieldsValue({
            team_ids: [],
            user_ids: [],
        });
    };

    const handleFinish = (values: any) => {
        const [start, end] = values.time_range;
        const finalUserIds = values.user_ids || [];

        if (finalUserIds.length === 0) {
            message.warning('Vui lòng chọn ít nhất một thành viên hoặc team tham gia!');
            return;
        }

        const formattedValues = {
            title: values.title.trim(),
            content: values.content?.trim() || '',
            start_time: start.format('YYYY-MM-DDTHH:mm:ss'),
            end_time: end.format('YYYY-MM-DDTHH:mm:ss'),
            require_check_in: values.require_check_in ?? true,
            enable_evaluation: values.enable_evaluation ?? false,
            user_ids: finalUserIds,
        };

        onSubmit(formattedValues);
    };

    return (
        <Modal
            title={editingItem ? "Chỉnh sửa buổi sinh hoạt" : "Tạo buổi sinh hoạt / Meeting"}
            open={open}
            onCancel={onCancel}
            onOk={form.submit}
            destroyOnClose
            width={640}
        >
            <Form form={form} initialValues={initialValues} layout="vertical" onFinish={handleFinish} className="mt-3">
                <Form.Item name="title" label={<span className="font-medium">Tiêu đề</span>} rules={[{ required: true, message: 'Vui lòng nhập tiêu đề!' }]}>
                    <Input placeholder="Ví dụ: Sinh hoạt định kỳ tuần 1" size="large" />
                </Form.Item>

                <Form.Item name="time_range" label={<span className="font-medium">Thời gian diễn ra</span>} rules={[{ required: true, message: 'Vui lòng chọn thời gian!' }]}>
                    <RangePicker showTime format="DD/MM/YYYY HH:mm" className="w-full" />
                </Form.Item>

                <Divider className="!my-4">
                    <div className="flex items-center gap-2">
                        <span className="font-medium text-sm text-indigo-700">Danh sách tham gia</span>
                        <Badge
                            count={selectedUserIds.length}
                            overflowCount={999}
                            style={{ backgroundColor: selectedUserIds.length > 0 ? '#4f46e5' : '#9ca3af' }}
                        />
                    </div>
                </Divider>

                <div className="bg-slate-50/80 p-3.5 rounded-xl border border-slate-200/80 mb-4">
                    <div className="flex items-center justify-between mb-2">
                        <Text className="text-xs font-semibold text-gray-600 uppercase tracking-wider">
                            Chọn nhanh theo Team
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
                            loading={loadingTeams}
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
                        💡 Khi chọn Team, toàn bộ thành viên trong nhóm sẽ được tự động phân giải và lưu trực tiếp vào danh sách người tham gia.
                    </p>
                </div>

                <Form.Item
                    name="user_ids"
                    label={
                        <div className="flex items-center justify-between w-full">
                            <span className="flex items-center gap-2 font-medium">
                                <UserOutlined /> Danh sách thành viên tham gia
                            </span>
                            <span className="text-xs text-indigo-600 font-normal">
                                {selectedUserIds.length} người được chọn
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
                        showSearch
                        allowClear
                        value={selectedUserIds}
                        onChange={handleUserChange}
                        filterOption={(input: string, option: any) =>
                            (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                        }
                        options={users.map(u => ({
                            label: u.email ? `${u.name} (${u.email})` : u.name,
                            value: u.id
                        }))}
                        maxTagCount="responsive"
                    />
                </Form.Item>

                <Form.Item name="content" label={<span className="font-medium">Nội dung / Ghi chú</span>}>
                    <TextArea rows={3} placeholder="Mô tả chi tiết buổi sinh hoạt..." />
                </Form.Item>

                <div className="grid grid-cols-2 gap-4">
                    <Form.Item name="require_check_in" label={<span className="font-medium">Kiểm tra checkin đúng giờ</span>} valuePropName="checked">
                        <Switch checkedChildren="Bật" unCheckedChildren="Tắt" />
                    </Form.Item>

                    <Form.Item name="enable_evaluation" label={<span className="font-medium">Đánh giá 2 chiều (Hạn 24h)</span>} valuePropName="checked">
                        <Switch checkedChildren="Bật" unCheckedChildren="Tắt" />
                    </Form.Item>
                </div>
            </Form>
        </Modal>
    );
};


