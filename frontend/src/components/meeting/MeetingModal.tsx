import { useEffect, useState } from 'react';
import { Modal, Form, Select, DatePicker, Input, message } from 'antd';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';
import type { UserResponse } from '@/types/user.types';
import { teamService } from '@/services/api/team.service';
import type { TeamResponse } from '@/types/team.types';

const { Option } = Select;
const { TextArea } = Input;
const { RangePicker } = DatePicker;

import type { MeetingResponse } from '@/types/meeting.types';

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

    useEffect(() => {
        if (open) {
            if (editingItem) {
                form.setFieldsValue({
                    title: editingItem.title,
                    content: editingItem.content,
                    time_range: [dayjs(editingItem.start_time), dayjs(editingItem.end_time)],
                    // For editing, we don't know the team_ids/user_ids from MeetingResponse easily 
                    // unless we store them or the backend returns them. 
                    // Current MeetingResponse only has participants.
                    // We can pre-fill user_ids from participants.
                    user_ids: editingItem.participants.map(p => p.user_id)
                });
            } else {
                form.resetFields();
                // Default start time to initialDate at 19:00, end time at 21:00 (for example)
                const start = initialDate.hour(19).minute(0).second(0);
                const end = initialDate.hour(21).minute(0).second(0);
                form.setFieldsValue({
                    time_range: [start, end]
                });
            }
            fetchTeams();
        }
    }, [open, editingItem, initialDate, form]);

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

    const handleFinish = (values: any) => {
        const [start, end] = values.time_range;
        const formattedValues = {
            title: values.title,
            content: values.content,
            start_time: start.toISOString(),
            end_time: end.toISOString(),
            team_ids: values.team_ids || [],
            user_ids: values.user_ids || []
        };

        if (formattedValues.team_ids.length === 0 && formattedValues.user_ids.length === 0) {
            message.warning('Vui lòng chọn ít nhất một team hoặc thành viên!');
            return;
        }

        onSubmit(formattedValues);
    };

    return (
        <Modal
            title={editingItem ? "Chỉnh sửa buổi sinh hoạt" : "Tạo buổi sinh hoạt / Meeting"}
            open={open}
            onCancel={onCancel}
            onOk={form.submit}
            destroyOnClose
            width={600}
        >
            <Form form={form} layout="vertical" onFinish={handleFinish}>
                <Form.Item name="title" label="Tiêu đề" rules={[{ required: true, message: 'Vui lòng nhập tiêu đề!' }]}>
                    <Input placeholder="Ví dụ: Sinh hoạt định kỳ tuần 1" />
                </Form.Item>

                <Form.Item name="time_range" label="Thời gian diễn ra" rules={[{ required: true, message: 'Vui lòng chọn thời gian!' }]}>
                    <RangePicker showTime format="DD/MM/YYYY HH:mm" className="w-full" />
                </Form.Item>

                <div className="grid grid-cols-2 gap-4">
                    <Form.Item name="team_ids" label="Chọn theo Team">
                        <Select
                            mode="multiple"
                            placeholder="Chọn teams"
                            loading={loadingTeams}
                            allowClear
                        >
                            {teams.map(t => (
                                <Option key={t.id} value={t.id}>{t.name}</Option>
                            ))}
                        </Select>
                    </Form.Item>
                    <Form.Item name="user_ids" label="Chọn theo Thành viên">
                        <Select
                            mode="multiple"
                            placeholder="Chọn thành viên"
                            showSearch
                            optionFilterProp="children"
                            allowClear
                        >
                            {users.map(u => (
                                <Option key={u.id} value={u.id}>{u.name}</Option>
                            ))}
                        </Select>
                    </Form.Item>
                </div>

                <Form.Item name="content" label="Nội dung / Ghi chú">
                    <TextArea rows={3} placeholder="Mô tả chi tiết buổi sinh hoạt..." />
                </Form.Item>
            </Form>
        </Modal>
    );
};
