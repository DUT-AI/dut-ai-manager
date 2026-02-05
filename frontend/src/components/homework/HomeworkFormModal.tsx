import { useEffect, useState } from 'react';
import { Modal, Form, Input, DatePicker, Select, message, Divider, Upload, Button } from 'antd';
import { TeamOutlined, UserOutlined, UploadOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { Homework } from '@/types/homework.types';
import type { UserResponse } from '@/types/user.types';
import type { TeamResponse } from '@/types/team.types';
import { homeworkService } from '@/services/api/homework.service';

const { TextArea } = Input;

interface Props {
    open: boolean;
    editingItem: Homework | null;
    users: UserResponse[];
    teams: TeamResponse[];
    currentAssignees?: number[];  // Current assignee IDs when editing
    onSuccess: () => void;
    onCancel: () => void;
}

export const HomeworkFormModal = ({
    open,
    editingItem,
    users,
    teams,
    currentAssignees = [],
    onSuccess,
    onCancel
}: Props) => {
    const [form] = Form.useForm();
    const [loading, setLoading] = useState(false);
    const isEditing = !!editingItem;

    const normFile = (e: any) => {
        if (Array.isArray(e)) {
            return e;
        }
        return e?.fileList;
    };

    useEffect(() => {
        if (open) {
            if (editingItem) {
                form.setFieldsValue({
                    title: editingItem.title,
                    description: editingItem.description,
                    deadline: dayjs(editingItem.deadline),
                    assignee_ids: currentAssignees,
                });
            } else {
                form.resetFields();
            }
        }
    }, [open, editingItem, form, currentAssignees]);

    const handleFinish = async (values: any) => {
        setLoading(true);
        try {
            const baseData = {
                title: values.title,
                description: values.description || '',
                deadline: values.deadline.format('YYYY-MM-DDTHH:mm:ss'),
            };

            if (isEditing) {
                await homeworkService.update(editingItem!.id, {
                    ...baseData,
                    assignee_ids: values.assignee_ids || [],
                    team_ids: values.team_ids || [],
                    file: values.file?.[0]?.originFileObj
                });
                message.success('Cập nhật bài tập thành công');
            } else {
                await homeworkService.create({
                    ...baseData,
                    assignee_ids: values.assignee_ids || [],
                    team_ids: values.team_ids || [],
                    file: values.file?.[0]?.originFileObj
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
            <Form form={form} layout="vertical" onFinish={handleFinish}>
                <Form.Item name="title" label="Tiêu đề" rules={[{ required: true, message: 'Vui lòng nhập tiêu đề' }]}>
                    <Input placeholder="Nhập tiêu đề bài tập..." />
                </Form.Item>

                <Form.Item name="deadline" label="Hạn nộp" rules={[{ required: true, message: 'Vui lòng chọn hạn nộp' }]}>
                    <DatePicker
                        showTime
                        className="w-full"
                        format="DD/MM/YYYY HH:mm"
                        placeholder="Chọn ngày và giờ..."
                    />
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
                        filterOption={(input: string, option: any) =>
                            (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                        }
                        options={users.map(u => ({ label: `${u.name} (${u.email})`, value: u.id }))}
                    />
                </Form.Item>

                <div className="text-xs text-gray-400 mb-4">
                    💡 {isEditing
                        ? 'Thêm người mới sẽ tự tạo bài nộp, xóa người cũ sẽ xóa bài nộp của họ'
                        : 'Có thể chọn cả team và thành viên cụ thể - hệ thống sẽ tự gộp lại'}
                </div>

                <Form.Item name="description" label="Mô tả / Đề bài">
                    <TextArea rows={4} placeholder="Nhập mô tả bài tập (hỗ trợ Markdown)..." />
                </Form.Item>

                <Form.Item
                    name="file"
                    label={isEditing ? "Thay thế tệp đính kèm (Tùy chọn)" : "Đính kèm tệp"}
                    valuePropName="fileList"
                    getValueFromEvent={normFile}
                    extra={isEditing ? "Tải lên file mới để thay thế file cũ. Chỉ chấp nhận 1 file nén (.zip, .rar, .gz), tối đa 10MB" : "Chỉ chấp nhận 1 file nén (.zip, .rar, .gz), tối đa 10MB"}
                >
                    <Upload
                        maxCount={1}
                        beforeUpload={(file) => {
                            const isLt10M = file.size / 1024 / 1024 < 10;
                            if (!isLt10M) {
                                message.error('File phải nhỏ hơn 10MB!');
                                return Upload.LIST_IGNORE;
                            }
                            return false;
                        }}
                        accept=".zip,.rar,.7z,.tar.gz,.gz"
                    >
                        <Button icon={<UploadOutlined />}>{isEditing ? "Chọn file thay thế" : "Chọn file đính kèm"}</Button>
                    </Upload>
                </Form.Item>
            </Form>
        </Modal>
    );
};
