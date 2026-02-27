import { useEffect, useState } from 'react';
import { Modal, Form, Select, DatePicker, Input, message, Switch } from 'antd';
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

    const initialValues = editingItem ? {
        title: editingItem.title,
        content: editingItem.content,
        require_check_in: editingItem.require_check_in,
        time_range: [dayjs(editingItem.start_time), dayjs(editingItem.end_time)],
        user_ids: editingItem.participants.map(p => p.user_id),
    } : {
        time_range: [
            initialDate.hour(19).minute(0).second(0),
            initialDate.hour(21).minute(0).second(0),
        ],
        require_check_in: true,
    };

    useEffect(() => {
        fetchTeams();
    }, []);

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
            start_time: start.format('YYYY-MM-DDTHH:mm:ss'),
            end_time: end.format('YYYY-MM-DDTHH:mm:ss'),
            require_check_in: values.require_check_in ?? true,
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
            <Form form={form} initialValues={initialValues} layout="vertical" onFinish={handleFinish}>
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
                                <Option key={t.id} value={t.id}>{t.team_name}</Option>
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

                <Form.Item name="require_check_in" label="Kiểm tra checkin đúng giờ" valuePropName="checked">
                    <Switch checkedChildren="Bật" unCheckedChildren="Tắt" />
                </Form.Item>
            </Form>
        </Modal>
    );
};
