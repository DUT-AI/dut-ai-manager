import React from 'react';
import { Modal, Button, Typography, Spin, Empty, Timeline, Tag } from 'antd';
import { HistoryOutlined, CodeOutlined, PlayCircleOutlined, CheckOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { useHomeworkSubmissions } from '@/features/homework/hooks/useHomeworks';
import type { UserSubmissionInfo, SubmissionHistoryItem } from '@/features/homework/types/homework.types';

const { Text } = Typography;

export interface SubmissionHistoryModalProps {
    homeworkId: number | null;
    user: UserSubmissionInfo | null;
    open: boolean;
    onClose: () => void;
}

export const SubmissionHistoryModal: React.FC<SubmissionHistoryModalProps> = ({
    homeworkId,
    user,
    open,
    onClose
}) => {
    const { data: submissions = [], isLoading } = useHomeworkSubmissions(
        open && homeworkId ? homeworkId : null,
        open && user ? user.user_id : null
    );

    return (
        <Modal
            title={
                <div className="flex items-center gap-2.5 pb-1">
                    <div className="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 flex items-center justify-center text-indigo-600">
                        <HistoryOutlined className="text-base" />
                    </div>
                    <div>
                        <div className="font-semibold text-base leading-snug">
                            Lịch sử nộp bài
                        </div>
                        <Text type="secondary" className="text-xs font-normal">
                            Học viên: <span className="font-medium text-gray-800 dark:text-gray-200">{user?.name || `Học viên #${user?.user_id}`}</span> (ID: #{user?.user_id})
                        </Text>
                    </div>
                </div>
            }
            open={open}
            onCancel={onClose}
            footer={[
                <Button key="close" onClick={onClose} className="rounded-lg">
                    Đóng
                </Button>
            ]}
            width={560}
            centered
        >
            <div className="py-3 max-h-[62vh] overflow-y-auto pr-1">
                {isLoading ? (
                    <div className="flex flex-col items-center justify-center py-12 gap-2 text-gray-400">
                        <Spin />
                        <span className="text-xs">Đang tải lịch sử...</span>
                    </div>
                ) : submissions.length === 0 ? (
                    <Empty
                        image={Empty.PRESENTED_IMAGE_SIMPLE}
                        description="Chưa có dữ liệu lịch sử nộp bài được ghi nhận"
                    />
                ) : (
                    <div className="pt-2">
                        <Timeline
                            mode="left"
                            items={submissions.map((sub: SubmissionHistoryItem, idx: number) => {
                                const isCoding = sub.submission_type === 'CODING';
                                const details = sub.details || {};
                                return {
                                    color: isCoding ? '#4f46e5' : '#8b5cf6',
                                    label: (
                                        <div className="text-right pr-2">
                                            <div className="font-semibold text-xs text-gray-700 dark:text-gray-300">
                                                {dayjs(sub.submitted_at).format('HH:mm:ss')}
                                            </div>
                                            <div className="text-[11px] text-gray-400">
                                                {dayjs(sub.submitted_at).format('DD/MM/YYYY')}
                                            </div>
                                        </div>
                                    ),
                                    children: (
                                        <div className="bg-gray-50/80 dark:bg-zinc-800/80 p-3 rounded-xl border border-gray-100 dark:border-zinc-700/80 mb-3 shadow-xs hover:border-indigo-200 dark:hover:border-zinc-600 transition-colors">
                                            <div className="flex items-center justify-between gap-2 flex-wrap mb-1.5">
                                                <div className="flex items-center gap-1.5">
                                                    <Tag
                                                        icon={isCoding ? <CodeOutlined /> : <PlayCircleOutlined />}
                                                        color={isCoding ? 'blue' : 'purple'}
                                                        className="m-0 font-medium text-xs rounded-md"
                                                    >
                                                        {isCoding ? 'Coding' : 'Game Quiz'}
                                                    </Tag>
                                                    {sub.is_passed ? (
                                                        <Tag color="success" className="m-0 text-[11px] rounded-md font-medium">
                                                            <CheckOutlined /> Hoàn thành
                                                        </Tag>
                                                    ) : (
                                                        <Tag color="warning" className="m-0 text-[11px] rounded-md font-medium">
                                                            Chưa hoàn thành
                                                        </Tag>
                                                    )}
                                                </div>
                                                <span className="text-[11px] text-gray-400 font-mono">
                                                    #{idx + 1}
                                                </span>
                                            </div>

                                            {/* Details Breakdown */}
                                            {details && Object.keys(details).length > 0 && (
                                                <div className="mt-2 text-xs text-gray-600 dark:text-gray-300 bg-white dark:bg-zinc-900/90 p-2.5 rounded-lg border border-gray-100 dark:border-zinc-800 flex flex-col gap-1">
                                                    {details.attempt_number !== undefined && (
                                                        <div className="flex justify-between">
                                                            <span className="text-gray-400">Lần nộp:</span>
                                                            <span className="font-medium">Lần thứ {details.attempt_number}</span>
                                                        </div>
                                                    )}
                                                    {details.original_filename && (
                                                        <div className="flex justify-between gap-2">
                                                            <span className="text-gray-400">Tệp nộp:</span>
                                                            <span className="font-mono text-xs truncate max-w-[240px]">{details.original_filename}</span>
                                                        </div>
                                                    )}
                                                    {details.final_score !== undefined && (
                                                        <div className="flex justify-between">
                                                            <span className="text-gray-400">Điểm số:</span>
                                                            <span className="font-semibold text-emerald-600 dark:text-emerald-400">{details.final_score}</span>
                                                        </div>
                                                    )}
                                                    {details.correct_count !== undefined && details.total_questions !== undefined && (
                                                        <div className="flex justify-between">
                                                            <span className="text-gray-400">Đúng:</span>
                                                            <span className="font-medium">{details.correct_count}/{details.total_questions} câu</span>
                                                        </div>
                                                    )}
                                                    {details.source && (
                                                        <div className="flex justify-between">
                                                            <span className="text-gray-400">Nguồn ghi nhận:</span>
                                                            <span className="text-xs text-indigo-600 dark:text-indigo-400">
                                                                {details.source === 'manual_sync' ? 'Đồng bộ thủ công' : 'Quiz Webhook'}
                                                            </span>
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    ),
                                };
                            })}
                        />
                    </div>
                )}
            </div>
        </Modal>
    );
};
