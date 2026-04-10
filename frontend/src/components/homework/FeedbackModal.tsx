import { Modal, Typography, Table, Space, Tag, Alert } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { useQuery } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import type { HomeworkSubmission, ScoreDetail } from '@/types/homework.types';
import { homeworkService } from '@/services/api/homework.service';

const { Text, Title, Paragraph } = Typography;

interface Props {
    open: boolean;
    submission: HomeworkSubmission | null;
    onClose: () => void;
}

export const FeedbackModal = ({ open, submission, onClose }: Props) => {
    // If feedback is still null, we poll the list every 5 seconds
    const { data: submissions } = useQuery({
        queryKey: ['homework-submissions', submission?.homework_id],
        queryFn: () => homeworkService.getSubmissions(submission?.homework_id!),
        enabled: open && !!submission && submission.feedback == null,
        refetchInterval: (query) => {
             // Stop polling if we finally got it
             const current = query.state.data?.find(s => s.id === submission?.id);
             return current?.feedback != null ? false : 5000;
        },
    });

    const activeSubmission = submissions?.find(s => s.id === submission?.id) || submission;
    const isLoading = open && activeSubmission && activeSubmission.feedback == null;

    const columns: ColumnsType<ScoreDetail> = [
        {
            title: 'Tiêu chí',
            dataIndex: 'criterion',
            key: 'criterion',
            width: '20%',
        },
        {
            title: 'Mô tả chi tiết',
            dataIndex: 'description',
            key: 'description',
        },
        {
            title: 'Điểm',
            dataIndex: 'weight',
            key: 'weight',
            width: '10%',
            align: 'center'
        },
        {
            title: 'Đạt',
            dataIndex: 'status',
            key: 'status',
            width: '10%',
            align: 'center',
            render: (status: boolean) => (
                 <Tag color={status ? 'success' : 'error'}>{status ? 'Pass' : 'Fail'}</Tag>
            )
        }
    ];

    return (
        <Modal
            title="Chi tiết Đánh giá & Chấm điểm"
            open={open}
            onCancel={onClose}
            footer={null}
            width={800}
            destroyOnClose
        >
            {isLoading ? (
                 <Alert
                    message="Hệ thống đang tự động đánh giá bài nộp. Vui lòng đợi trong giây lát..."
                    type="info"
                    showIcon
                    className="mb-4"
                 />
            ) : (
                <div style={{ wordBreak: 'break-word', marginTop: 16 }}>
                    {activeSubmission?.is_plagiarized && (
                         <Alert
                            message="Cảnh báo Đạo văn"
                            description={`Bài nộp có dấu hiệu đạo văn hoặc copy source. Tỉ lệ giống trên 80%.`}
                            type="error"
                            showIcon
                            className="mb-4"
                         />
                    )}

                    <Space style={{ marginBottom: 16 }}>
                        <Title level={4} style={{ margin: 0 }}>Điểm số:</Title>
                        <Tag color={activeSubmission?.is_pass ? 'success' : 'error'} style={{ fontSize: 16, padding: '4px 12px' }}>
                            {activeSubmission?.score != null ? activeSubmission.score : 'N/A'}/10
                        </Tag>
                    </Space>
                    
                    {activeSubmission?.score_details && Array.isArray(activeSubmission.score_details) && activeSubmission.score_details.length > 0 && (
                        <div style={{ marginBottom: 24 }}>
                             <Title level={5}>Chi tiết điểm</Title>
                             <Table<ScoreDetail>
                                 dataSource={activeSubmission.score_details}
                                 columns={columns}
                                 rowKey="criterion"
                                 pagination={false}
                                 size="small"
                                 bordered
                             />
                        </div>
                    )}
                    
                    {activeSubmission?.feedback && (
                         <div>
                             <Title level={5}>Nhận xét</Title>
                             <div className="bg-gray-50 p-4 rounded-md border border-gray-200 prose max-w-none">
                                 <ReactMarkdown>
                                      {activeSubmission.feedback}
                                 </ReactMarkdown>
                             </div>
                         </div>
                    )}
                </div>
            )}
        </Modal>
    );
};
