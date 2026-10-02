import React, { useEffect, useState } from 'react';
import { Modal, Rate, Typography, Spin, Alert, Card, Empty, Space } from 'antd';
import { TrophyOutlined, LockOutlined, MessageOutlined } from '@ant-design/icons';
import type { EvaluationResponse } from '../types/meeting.types';
import { meetingService } from '../services/meeting.service';

const { Text, Title, Paragraph } = Typography;

interface Props {
    open: boolean;
    meetingId: number;
    onClose: () => void;
}

export const MyEvaluationResultModal: React.FC<Props> = ({
    open,
    meetingId,
    onClose,
}) => {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<EvaluationResponse | null>(null);
    const [isLocked, setIsLocked] = useState(false);
    const [errorMsg, setErrorMsg] = useState<string | null>(null);

    useEffect(() => {
        if (!open || !meetingId) return;

        const fetchResult = async () => {
            setLoading(true);
            setErrorMsg(null);
            setIsLocked(false);
            try {
                const res = await meetingService.getMyEvaluationResult(meetingId);
                if (res.is_success && res.data) {
                    setResult(res.data);
                } else {
                    setResult(null);
                }
            } catch (err: any) {
                if (err.response?.status === 403) {
                    setIsLocked(true);
                } else if (err.response?.status === 404) {
                    setResult(null);
                } else {
                    setErrorMsg(err.response?.data?.detail || 'Không thể tải kết quả đánh giá.');
                }
            } finally {
                setLoading(false);
            }
        };

        fetchResult();
    }, [open, meetingId]);

    return (
        <Modal
            title={
                <Space>
                    <TrophyOutlined className="text-yellow-500" />
                    <span>Kết quả Đánh giá Cá nhân</span>
                </Space>
            }
            open={open}
            onCancel={onClose}
            footer={null}
            destroyOnClose
            width={540}
        >
            {loading ? (
                <div className="py-12 text-center">
                    <Spin tip="Đang tải kết quả..." />
                </div>
            ) : isLocked ? (
                <Alert
                    type="warning"
                    showIcon
                    icon={<LockOutlined />}
                    message="Kết quả bị khóa"
                    description="Bạn cần gửi đánh giá Trainer cho buổi học này trước khi có thể mở khóa xem nhận xét và điểm số của mình."
                    className="my-4"
                />
            ) : errorMsg ? (
                <Alert type="error" showIcon message={errorMsg} className="my-4" />
            ) : !result ? (
                <div className="py-8 text-center">
                    <Empty description="Trainer chưa gửi đánh giá cho bạn trong buổi học này." />
                </div>
            ) : (
                <div className="space-y-4 py-2">
                    <Card size="small" className="bg-blue-50/50 border-blue-100">
                        <div className="flex justify-between items-center">
                            <div>
                                <Text type="secondary" className="text-xs">ĐIỂM TRUNG BÌNH</Text>
                                <Title level={2} className="!m-0 text-blue-600">
                                    {result.average_score.toFixed(1)} <span className="text-sm text-gray-500">/ 5.0</span>
                                </Title>
                            </div>
                            <Rate disabled allowHalf value={result.average_score} />
                        </div>
                    </Card>

                    <div>
                        <Text strong className="block mb-2 text-sm text-gray-700">Chi tiết theo tiêu chí:</Text>
                        <div className="space-y-2.5">
                            {result.scores.map((score, idx) => (
                                <div key={idx} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg border border-gray-100">
                                    <div className="flex-1 pr-3">
                                        <Text className="block text-sm font-semibold text-gray-800">
                                            {score.criteria_name || score.criteria_code}
                                        </Text>
                                        {score.criteria_description && (
                                            <Text type="secondary" className="block text-xs mt-0.5 leading-relaxed text-gray-500">
                                                {score.criteria_description}
                                            </Text>
                                        )}
                                    </div>
                                    <div className="flex items-center gap-2 flex-shrink-0">
                                        <Rate disabled value={score.score} className="text-sm" />
                                        <Text strong className="text-xs w-6 text-right text-gray-700">{score.score}⭐</Text>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {result.feedback_text && (
                        <div className="mt-4 p-3 bg-amber-50/60 rounded-lg border border-amber-100">
                            <div className="flex items-center gap-1.5 mb-1 text-amber-800 font-semibold text-xs">
                                <MessageOutlined />
                                <span>Nhận xét từ Trainer:</span>
                            </div>
                            <Paragraph className="!mb-0 text-sm text-gray-700 italic">
                                "{result.feedback_text}"
                            </Paragraph>
                        </div>
                    )}
                </div>
            )}
        </Modal>
    );
};
