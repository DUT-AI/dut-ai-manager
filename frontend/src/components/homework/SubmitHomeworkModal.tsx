import { useEffect, useState } from 'react';
import { Modal, Form, Input, Card, Statistic, Typography, message } from 'antd';
import { LinkOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { Homework, HomeworkSubmission } from '@/types/homework.types';
import { homeworkService } from '@/services/api/homework.service';

const { Text } = Typography;

interface Props {
    open: boolean;
    homework: Homework | null;
    onSuccess: () => void;
    onCancel: () => void;
}

export const SubmitHomeworkModal = ({ open, homework, onSuccess, onCancel }: Props) => {
    const [form] = Form.useForm();
    const [mySubmission, setMySubmission] = useState<HomeworkSubmission | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (open && homework) {
            form.resetFields();
            setMySubmission(null);
            fetchMySubmission();
        }
    }, [open, homework]);

    const fetchMySubmission = async () => {
        if (!homework) return;
        setLoading(true);
        try {
            const submission = await homeworkService.getMySubmission(homework.id);
            if (submission) {
                setMySubmission(submission);
                form.setFieldsValue({ link: submission.link });
            }
        } catch (error: any) {
            // Ignore 404 - user hasn't submitted yet
        } finally {
            setLoading(false);
        }
    };

    const handleFinish = async (values: any) => {
        if (!homework) return;
        try {
            await homeworkService.submit(homework.id, { link: values.link });
            message.success('Nộp bài thành công');
            onSuccess();
        } catch (error: any) {
            message.error(error?.message || 'Nộp bài thất bại');
        }
    };

    return (
        <Modal
            title={`Nộp bài: ${homework?.title}`}
            open={open}
            onCancel={onCancel}
            onOk={form.submit}
            okText="Nộp bài"
            confirmLoading={loading}
            destroyOnClose
        >
            {homework && (
                <div className="mb-4">
                    <div className="bg-gray-50 p-3 rounded mb-4">
                        <Text strong>Đề bài:</Text>
                        <div className="whitespace-pre-wrap mt-1 text-gray-700">
                            {homework.description}
                        </div>
                        <div className="mt-2 text-xs text-red-500">
                            Deadline: {dayjs(homework.deadline).format('DD/MM/YYYY HH:mm')}
                        </div>
                    </div>

                    {mySubmission && (
                        <Card size="small" className="mb-4 border-blue-200 bg-blue-50">
                            <Statistic
                                title="Trạng thái hiện tại"
                                value={mySubmission.status}
                                valueStyle={{ fontSize: 16, color: '#1890ff' }}
                            />
                            <Text type="secondary" style={{ fontSize: 12 }}>
                                Cập nhật lần cuối: {dayjs(mySubmission.updated_at).format('DD/MM HH:mm')}
                            </Text>
                        </Card>
                    )}
                </div>
            )}

            <Form form={form} layout="vertical" onFinish={handleFinish}>
                <Form.Item
                    name="link"
                    label="Link bài làm (Github, Drive...)"
                    rules={[
                        { required: true, message: 'Vui lòng nhập link bài làm' },
                        { type: 'url', message: 'Link không hợp lệ! Vui lòng nhập đúng định dạng URL (vd: https://...)' }
                    ]}
                >
                    <Input prefix={<LinkOutlined />} placeholder="https://..." />
                </Form.Item>
            </Form>
        </Modal>
    );
};
