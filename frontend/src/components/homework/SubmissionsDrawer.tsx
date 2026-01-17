import { useState, useEffect } from 'react';
import { Drawer, Table, Select, Tag, Space, Typography, message } from 'antd';
import { LinkOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { Homework, HomeworkSubmission } from '@/types/homework.types';
import { HomeworkStatus } from '@/types/homework.types';
import { homeworkService } from '@/services/api/homework.service';
import type { ColumnsType } from 'antd/es/table';

const { Text } = Typography;
const { Option } = Select;

interface Props {
    open: boolean;
    homework: Homework | null;
    onClose: () => void;
}

export const SubmissionsDrawer = ({ open, homework, onClose }: Props) => {
    const [submissions, setSubmissions] = useState<HomeworkSubmission[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (open && homework) {
            fetchSubmissions();
        }
    }, [open, homework]);

    const fetchSubmissions = async () => {
        if (!homework) return;
        setLoading(true);
        try {
            const data = await homeworkService.getSubmissions(homework.id);
            setSubmissions(data || []);
        } catch (error: any) {
            message.error(error?.message || 'Không thể tải danh sách bài nộp');
        } finally {
            setLoading(false);
        }
    };

    const handleUpdateStatus = async (submissionId: number, status: HomeworkStatus) => {
        try {
            await homeworkService.updateStatus(submissionId, status);
            message.success('Cập nhật trạng thái thành công');
            setSubmissions(prev => prev.map(s => s.id === submissionId ? { ...s, status } : s));
        } catch (error: any) {
            message.error(error?.message || 'Cập nhật trạng thái thất bại');
        }
    };

    const renderStatusTag = (status: HomeworkStatus, isLate: boolean) => {
        let color = 'default';
        if (isLate) color = 'error';
        else if (status === HomeworkStatus.SUBMITTED) color = 'processing';
        else if (status === HomeworkStatus.LeaderChecked) color = 'warning';
        else if (status === HomeworkStatus.FINISHED) color = 'success';

        return (
            <Space>
                <Tag color={color}>{status}</Tag>
                {isLate && <Tag color="red">Nộp trễ</Tag>}
            </Space>
        );
    };

    const columns: ColumnsType<HomeworkSubmission> = [
        {
            title: 'Học viên',
            key: 'user',
            render: (record: HomeworkSubmission) => (
                <Text strong>{record.user_name || 'Unknown'}</Text>
            )
        },
        {
            title: 'Link',
            dataIndex: 'link',
            key: 'link',
            render: (link: string) => {
                let isValid = false;
                try {
                    new URL(link);
                    isValid = true;
                } catch {
                    isValid = false;
                }

                if (!isValid) {
                    return <Text type="secondary" italic>Link không hợp lệ</Text>;
                }
                return <a href={link} target="_blank" rel="noopener noreferrer"><LinkOutlined /> Mở link</a>;
            }
        },
        {
            title: 'Ngày nộp',
            dataIndex: 'updated_at',
            key: 'updated_at',
            render: (date: string) => dayjs(date).format('DD/MM HH:mm'),
        },
        {
            title: 'Trạng thái',
            key: 'status',
            render: (_: any, record: HomeworkSubmission) => renderStatusTag(record.status, record.is_late),
        },
        {
            title: 'Action',
            key: 'action',
            render: (_: any, record: HomeworkSubmission) => (
                <Select
                    defaultValue={record.status}
                    style={{ width: 160 }}
                    onChange={(val) => handleUpdateStatus(record.id, val)}
                    size="small"
                >
                    <Option value={HomeworkStatus.SUBMITTED}>Đã nộp</Option>
                    <Option value={HomeworkStatus.LeaderChecked}>Leader Check</Option>
                    <Option value={HomeworkStatus.FINISHED}>Finish</Option>
                </Select>
            )
        }
    ];

    return (
        <Drawer
            title={`Danh sách bài nộp: ${homework?.title}`}
            width={720}
            open={open}
            onClose={onClose}
        >
            <Table
                dataSource={submissions}
                columns={columns}
                rowKey="id"
                loading={loading}
            />
        </Drawer>
    );
};
