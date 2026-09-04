import { useState, useEffect } from 'react';
import { Modal, Form, Input, DatePicker, Select, message, Divider } from 'antd';
import { TeamOutlined, UserOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { Homework } from '@/features/homework/types/homework.types';
import type { UserResponse } from '@/features/users/types/user.types';
import type { TeamResponse } from '@/features/teams/types/team.types';
import { homeworkService } from '@/features/homework/services/homework.service';

const EMPTY_ASSIGNEES: number[] = [];

interface Props {
    open: boolean;
    editingItem: Homework | null;
    users: UserResponse[];
    teams: TeamResponse[];
    currentAssignees?: number[];
    assigneesLoading?: boolean;
    onSuccess: () => void;
    onCancel: () => void;
}

export const HomeworkFormModal = ({
    open,
    editingItem,
    users,
    teams,
    currentAssignees = EMPTY_ASSIGNEES,
    assigneesLoading = false,
    onSuccess,
    onCancel
}: Props) => {
    const [form] = Form.useForm();
    const [loading, setLoading] = useState(false);
    const isEditing = !!editingItem;

    // Update assignee_ids when async loading completes
    useEffect(() => {
        if (isEditing && currentAssignees.length > 0) {
            form.setFieldsValue({ assignee_ids: currentAssignees });
        }
    }, [currentAssignees, isEditing, form]);

    const initialValues = editingItem ? {
        title: editingItem.title,
        deadline: dayjs(editingItem.deadline),
        link: editingItem.link,
        homework_slug: editingItem.homework_slug,
        game_slug: editingItem.game_slug,
        assignee_ids: currentAssignees,
    } : undefined;

    const handleFinish = async (values: any) => {
        setLoading(true);
        try {
            const baseData = {
                title: values.title,
                description: '',
                deadline: values.deadline.format('YYYY-MM-DDTHH:mm:ss'),
                link: values.link || '',
                homework_slug: values.homework_slug || null,
                game_slug: values.game_slug || null,
            };

            if (isEditing) {
                await homeworkService.update(editingItem!.id, {
                    ...baseData,
                    assignee_ids: values.assignee_ids || [],
                    team_ids: values.team_ids || [],
                });
                message.success('Cập nhật bài tập thành công');
            } else {
                await homeworkService.create({
                    ...baseData,
                    assignee_ids: values.assignee_ids || [],
                    team_ids: values.team_ids || [],
                });
                message.success('Tạo bài tập thành công');
            }
            onSuccess();
        } catch (error: any) {
            message.error(error?.message || 'Thao tác thất bại');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Modal
            title={isEditing ? 'Chỉnh sửa bài tập' : 'Tạo bài tập mới'}
            open={open}
            onCancel={onCancel}
            onOk={form.submit}
            confirmLoading={loading}
            destroyOnHidden
            width={600}
        >
            <Form form={form} initialValues={initialValues} layout="vertical" onFinish={handleFinish}>
                <Form.Item name="title" label="Tiêu đề" rules={[{ required: true, message: 'Vui lòng nhập tiêu đề' }]}>
                    <Input placeholder="Nhập tiêu đề bài tập..." />
                </Form.Item>

                <Form.Item 
                    name="deadline" 
                    label="Hạn nộp" 
                    rules={[
                        { required: true, message: 'Vui lòng chọn hạn nộp' },
                        {
                            validator: (_, value) => {
                                if (value && value.isBefore(dayjs())) {
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
                        disabledDate={(current) => current && current.isBefore(dayjs().startOf('day'))}
                    />
                </Form.Item>

                <Form.Item
                    name="link"
                    label="Link bài tập"
                    rules={[{ required: true, message: 'Vui lòng nhập link bài tập' }]}
                >
                    <Input placeholder="https://..." />
                </Form.Item>

                <Form.Item
                    name="homework_slug"
                    label="Slug của bài tập Coding (Tùy chọn)"
                >
                    <Input placeholder="Nhập slug bài tập coding..." />
                </Form.Item>

                <Form.Item
                    name="game_slug"
                    label="Slug của Game Quiz (Tùy chọn)"
                >
                    <Input placeholder="Nhập slug game..." />
                </Form.Item>



                <Divider className="!my-4">
                    {isEditing ? 'Chỉnh sửa người nộp bài' : 'Giao bài tập cho'}
                </Divider>

                <Form.Item
                    name="team_ids"
                    label={
                        <span className="flex items-center gap-2">
                            <TeamOutlined /> Chọn theo Team
                        </span>
                    }
                >
                    <Select
                        mode="multiple"
                        placeholder="Chọn team để giao bài cho tất cả thành viên..."
                        allowClear
                        filterOption={(input: string, option: any) =>
                            (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                        }
                        options={teams.map(t => ({
                            label: `${t.team_name} (${t.member_count} thành viên)`,
                            value: t.id
                        }))}
                    />
                </Form.Item>

                <Form.Item
                    name="assignee_ids"
                    label={
                        <span className="flex items-center gap-2">
                            <UserOutlined /> Hoặc chọn từng thành viên
                        </span>
                    }
                >
                    <Select
                        mode="multiple"
                        placeholder="Chọn thành viên cụ thể..."
                        allowClear
                        loading={assigneesLoading}
                        disabled={assigneesLoading}
                        filterOption={(input: string, option: any) =>
                            (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                        }
                        options={users.map(u => ({ label: `${u.name} (${u.email})`, value: u.id }))}
                    />
                </Form.Item>

                <div className="text-xs text-gray-400 mb-2">
                    💡 {isEditing
                        ? 'Thêm người mới sẽ tự tạo bài nộp, xóa người cũ sẽ xóa bài nộp của họ'
                        : 'Có thể chọn cả team và thành viên cụ thể - hệ thống sẽ tự gộp lại'}
                </div>
            </Form>
        </Modal>
    );
};
