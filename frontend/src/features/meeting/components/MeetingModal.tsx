import { useCallback, useEffect, useMemo, useState } from 'react';
import { Modal, Form, Select, DatePicker, Input, message, Switch, Button, Space, Typography, Tag, Divider, Badge } from 'antd';
import { TeamOutlined, UserOutlined, CheckOutlined, ClearOutlined, CrownOutlined } from '@ant-design/icons';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';
import { useUserOptions } from '@/features/users/hooks/useUsers';
import { teamService } from '@/features/teams/services/team.service';
import type { TeamResponse } from '@/features/teams/types/team.types';
import type { MeetingResponse, MeetingDetailResponse } from '@/features/meeting/types/meeting.types';

const { TextArea } = Input;
const { RangePicker } = DatePicker;
const { Text } = Typography;

interface Props {
    open: boolean;
    editingItem?: MeetingResponse | MeetingDetailResponse | null;
    initialDate?: Dayjs;
    confirmLoading?: boolean;
    onSubmit: (values: any) => void;
    onCancel: () => void;
}

export const MeetingModal = ({ open, editingItem, initialDate, confirmLoading, onSubmit, onCancel }: Props) => {
    const [form] = Form.useForm();
    const [teams, setTeams] = useState<TeamResponse[]>([]);
    const [loadingTeams, setLoadingTeams] = useState(false);
    const [selectedTeamIds, setSelectedTeamIds] = useState<number[]>([]);
    const [selectedTrainerIds, setSelectedTrainerIds] = useState<number[]>([]);
    const [selectedTraineeIds, setSelectedTraineeIds] = useState<number[]>([]);

    const { data: userOptions = [] } = useUserOptions();

    const userSelectOptions = useMemo(() => {
        return userOptions.map(u => ({
            label: u.email ? `${u.name} (${u.email})` : u.name,
            value: u.id,
        }));
    }, [userOptions]);

    const filterUserOption = (input: string, option?: { label?: string; value?: number }) => {
        if (!input || !option?.label) return true;
        const cleanInput = input.trim().toLowerCase();
        const cleanLabel = option.label.toLowerCase();

        // 1. Khớp chuỗi trực tiếp
        if (cleanLabel.includes(cleanInput)) return true;

        // 2. Khớp không dấu (hỗ trợ tiếng Việt không dấu hoặc gõ sai dấu)
        const normInput = cleanInput.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
        const normLabel = cleanLabel.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
        return normLabel.includes(normInput);
    };

    const initialDateKey = initialDate ? initialDate.format('YYYY-MM-DD') : '';

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
        if (!open) return;

        if (editingItem) {
            const detailItem = editingItem as Partial<MeetingDetailResponse>;
            const trainers = (detailItem.trainers || []).map((p: any) => p.user_id ?? p.id);
            const trainees = (detailItem.trainees || []).map((p: any) => p.user_id ?? p.id);

            const matchedTeams = detectMatchingTeams(trainees);
            setSelectedTeamIds(matchedTeams);
            setSelectedTrainerIds(trainers);
            setSelectedTraineeIds(trainees);

            form.setFieldsValue({
                title: editingItem.title,
                content: editingItem.content,
                require_check_in: editingItem.require_check_in,
                enable_evaluation: editingItem.enable_evaluation ?? false,
                time_range: [dayjs(editingItem.start_time), dayjs(editingItem.end_time)],
                trainer_ids: trainers,
                team_ids: matchedTeams,
                trainee_ids: trainees,
            });
        } else {
            const baseDate = initialDate || dayjs();
            setSelectedTeamIds([]);
            setSelectedTrainerIds([]);
            setSelectedTraineeIds([]);
            form.setFieldsValue({
                title: '',
                content: '',
                time_range: [
                    baseDate.hour(19).minute(0).second(0),
                    baseDate.hour(21).minute(0).second(0),
                ],
                require_check_in: true,
                enable_evaluation: false,
                trainer_ids: [],
                team_ids: [],
                trainee_ids: [],
            });
        }
    }, [open, editingItem?.id, initialDateKey, detectMatchingTeams, form]);

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

    // Handle Trainer Selection Change
    const handleTrainerChange = (newTrainerIds: number[]) => {
        setSelectedTrainerIds(newTrainerIds);
        // Tự động loại bỏ khỏi trainee_ids nếu đã chọn làm trainer
        const currentTrainees = form.getFieldValue('trainee_ids') || [];
        const filteredTrainees = currentTrainees.filter((id: number) => !newTrainerIds.includes(id));
        if (filteredTrainees.length !== currentTrainees.length) {
            setSelectedTraineeIds(filteredTrainees);
            form.setFieldsValue({ trainee_ids: filteredTrainees });
        }
        form.setFieldsValue({ trainer_ids: newTrainerIds });
    };

    // Handle Team Selection Change (Resolves team members into trainee_ids)
    const handleTeamChange = (newTeamIds: number[]) => {
        const currentTraineeIds = form.getFieldValue('trainee_ids') || [];
        const currentTraineeSet = new Set<number>(currentTraineeIds);

        // Teams that were newly selected
        const newlyAdded = newTeamIds.filter(id => !selectedTeamIds.includes(id));
        newlyAdded.forEach(tId => {
            const memberIds = teamMemberMap.get(tId) || [];
            memberIds.forEach(uid => {
                if (!selectedTrainerIds.includes(uid)) {
                    currentTraineeSet.add(uid);
                }
            });
        });

        // Teams that were deselected
        const newlyRemoved = selectedTeamIds.filter(id => !newTeamIds.includes(id));
        newlyRemoved.forEach(tId => {
            const memberIds = teamMemberMap.get(tId) || [];
            memberIds.forEach(uid => {
                const belongsToOtherSelectedTeam = newTeamIds.some(otherTId => {
                    const otherMembers = teamMemberMap.get(otherTId) || [];
                    return otherMembers.includes(uid);
                });
                if (!belongsToOtherSelectedTeam) {
                    currentTraineeSet.delete(uid);
                }
            });
        });

        const finalTrainees = Array.from(currentTraineeSet);
        setSelectedTeamIds(newTeamIds);
        setSelectedTraineeIds(finalTrainees);

        form.setFieldsValue({
            team_ids: newTeamIds,
            trainee_ids: finalTrainees,
        });
    };

    // Handle Direct Trainee Selection Change
    const handleTraineeChange = (newTraineeIds: number[]) => {
        // Lọc bỏ trainer nếu người dùng chọn trùng
        const cleanTrainees = newTraineeIds.filter(id => !selectedTrainerIds.includes(id));
        setSelectedTraineeIds(cleanTrainees);
        const matchedTeams = detectMatchingTeams(cleanTrainees);
        setSelectedTeamIds(matchedTeams);
        form.setFieldsValue({
            team_ids: matchedTeams,
            trainee_ids: cleanTrainees,
        });
    };

    // Quick Action: Select All Trainees
    const handleSelectAllTrainees = () => {
        const allUserIds = userOptions.map(u => u.id).filter(id => !selectedTrainerIds.includes(id));
        const allTeamIds = teams.map(t => t.id);
        setSelectedTeamIds(allTeamIds);
        setSelectedTraineeIds(allUserIds);
        form.setFieldsValue({
            team_ids: allTeamIds,
            trainee_ids: allUserIds,
        });
    };

    // Quick Action: Clear Trainees
    const handleClearTrainees = () => {
        setSelectedTeamIds([]);
        setSelectedTraineeIds([]);
        form.setFieldsValue({
            team_ids: [],
            trainee_ids: [],
        });
    };

    const handleFinish = (values: any) => {
        const [start, end] = values.time_range;
        const trainerIds = values.trainer_ids || [];
        const traineeIds = values.trainee_ids || [];

        if (trainerIds.length === 0 && traineeIds.length === 0) {
            message.warning('Vui lòng chọn ít nhất một người tham gia (Trainer hoặc Trainee)!');
            return;
        }

        const formattedValues = {
            title: values.title.trim(),
            content: values.content?.trim() || '',
            start_time: start.toISOString(),
            end_time: end.toISOString(),
            require_check_in: values.require_check_in ?? true,
            enable_evaluation: values.enable_evaluation ?? false,
            trainer_ids: trainerIds,
            trainee_ids: traineeIds,
        };

        onSubmit(formattedValues);
    };

    const totalParticipants = selectedTrainerIds.length + selectedTraineeIds.length;

    return (
        <Modal
            title={editingItem ? "Chỉnh sửa buổi sinh hoạt" : "Tạo buổi sinh hoạt / Meeting"}
            open={open}
            onCancel={onCancel}
            onOk={form.submit}
            confirmLoading={confirmLoading}
            destroyOnClose
            width={680}
        >
            <Form form={form} layout="vertical" onFinish={handleFinish} className="mt-3">
                <Form.Item name="title" label={<span className="font-medium">Tiêu đề</span>} rules={[{ required: true, message: 'Vui lòng nhập tiêu đề!' }]}>
                    <Input placeholder="Ví dụ: Sinh hoạt định kỳ tuần 1" size="large" />
                </Form.Item>

                <Form.Item name="time_range" label={<span className="font-medium">Thời gian diễn ra</span>} rules={[{ required: true, message: 'Vui lòng chọn thời gian!' }]}>
                    <RangePicker showTime format="DD/MM/YYYY HH:mm" className="w-full" />
                </Form.Item>

                <Divider className="!my-4">
                    <div className="flex items-center gap-2">
                        <span className="font-medium text-sm text-indigo-700">Phân công & Thành viên</span>
                        <Badge
                            count={totalParticipants}
                            overflowCount={999}
                            style={{ backgroundColor: totalParticipants > 0 ? '#4f46e5' : '#9ca3af' }}
                        />
                    </div>
                </Divider>

                {/* 1. Ô CHỌN TRAINER(S) PHỤ TRÁCH */}
                <div className="bg-amber-50/60 p-3.5 rounded-xl border border-amber-200/80 mb-4">
                    <Form.Item
                        name="trainer_ids"
                        className="!mb-1"
                        label={
                            <div className="flex items-center justify-between w-full">
                                <span className="flex items-center gap-2 font-medium text-amber-900">
                                    <CrownOutlined className="text-amber-500" /> Giảng viên / Người phụ trách (Trainers)
                                </span>
                                <span className="text-xs text-amber-700 font-medium">
                                    {selectedTrainerIds.length} Trainer
                                </span>
                            </div>
                        }
                    >
                        <Select
                            mode="multiple"
                            placeholder="Chọn một hoặc nhiều Giảng viên/Mentor phụ trách (hoặc để trống nếu tự học)..."
                            showSearch
                            allowClear
                            value={selectedTrainerIds}
                            onChange={handleTrainerChange}
                            filterOption={filterUserOption}
                            options={userSelectOptions}
                            maxTagCount="responsive"
                            tagRender={({ label, closable, onClose }) => (
                                <Tag
                                    color="gold"
                                    closable={closable}
                                    onClose={onClose}
                                    className="flex items-center gap-1 font-semibold my-0.5 text-amber-900 border-amber-300"
                                >
                                    <CrownOutlined className="text-amber-600" /> {label}
                                </Tag>
                            )}
                        />
                    </Form.Item>
                    <p className="text-xs text-amber-800/80 m-0">
                        ⭐ Trainer có toàn quyền điểm danh, quản lý và nộp đánh giá tổng thể. Để trống đối với buổi sinh hoạt / tự học nhóm tự quản.
                    </p>
                </div>

                {/* 2. KHU VỰC CHỌN TRAINEES THAM GIA */}
                <div className="bg-slate-50/80 p-3.5 rounded-xl border border-slate-200/80 mb-4">
                    <div className="flex items-center justify-between mb-2">
                        <Text className="text-xs font-semibold text-gray-600 uppercase tracking-wider">
                            Chọn nhanh Học viên theo Team
                        </Text>
                        <Space size="small">
                            <Button
                                type="link"
                                size="small"
                                icon={<CheckOutlined />}
                                onClick={handleSelectAllTrainees}
                                className="!p-0 !text-xs !text-indigo-600 font-medium"
                            >
                                Chọn tất cả ({userOptions.length - selectedTrainerIds.length})
                            </Button>
                            <span className="text-gray-300">|</span>
                            <Button
                                type="link"
                                size="small"
                                danger
                                icon={<ClearOutlined />}
                                onClick={handleClearTrainees}
                                className="!p-0 !text-xs font-medium"
                            >
                                Xóa tất cả
                            </Button>
                        </Space>
                    </div>

                    <Form.Item name="team_ids" className="!mb-2">
                        <Select
                            mode="multiple"
                            placeholder="Chọn một hoặc nhiều Team để tự động thêm tất cả thành viên vào học viên..."
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

                    <Form.Item
                        name="trainee_ids"
                        className="!mb-0"
                        label={
                            <div className="flex items-center justify-between w-full">
                                <span className="flex items-center gap-2 font-medium text-blue-900">
                                    <UserOutlined /> Danh sách Học viên (Trainees)
                                </span>
                                <span className="text-xs text-blue-600 font-normal">
                                    {selectedTraineeIds.length} học viên
                                </span>
                            </div>
                        }
                    >
                        <Select
                            mode="multiple"
                            placeholder="Tìm và chọn các học viên cụ thể..."
                            showSearch
                            allowClear
                            value={selectedTraineeIds}
                            onChange={handleTraineeChange}
                            filterOption={filterUserOption}
                            options={userSelectOptions.filter(opt => !selectedTrainerIds.includes(opt.value))}
                            maxTagCount="responsive"
                            tagRender={({ label, closable, onClose }) => (
                                <Tag
                                    color="blue"
                                    closable={closable}
                                    onClose={onClose}
                                    className="flex items-center gap-1 my-0.5"
                                >
                                    <UserOutlined /> {label}
                                </Tag>
                            )}
                        />
                    </Form.Item>
                </div>

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
