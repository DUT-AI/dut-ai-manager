import React from 'react';
import { Timeline, Typography, Empty, Button, Card, Tag } from 'antd';
import { ExportOutlined, CheckCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { SubmissionHistoryItem } from '../types/homework.types';

const { Text } = Typography;

export interface MySubmissionTimelineProps {
    submissions: SubmissionHistoryItem[];
    type: 'CODING' | 'GAME';
    deadline: string;
    homeworkLink?: string | null;
}

export const MySubmissionTimeline: React.FC<MySubmissionTimelineProps> = ({
    submissions,
    type,
    deadline,
    homeworkLink
}) => {
    const isCoding = type === 'CODING';
    const deadlineObj = dayjs(deadline);

    if (submissions.length === 0) {
        return (
            <div className="py-6 flex flex-col items-center justify-center">
                <Empty
                    description={
                        <div className="text-center">
                            <Text type="secondary" className="block text-sm mb-1">
                                {isCoding
                                    ? 'Bạn chưa có lượt nộp bài tập coding nào'
                                    : 'Bạn chưa có lượt chơi game nào đạt 100%'}
                            </Text>
                            <Text type="secondary" className="text-xs">
                                Hãy vào hệ thống Quiz để hoàn thành bài tập và được ghi nhận tự động.
                            </Text>
                        </div>
                    }
                    imageStyle={{ height: 80 }}
                />
                {homeworkLink && (
                    <Button
                        type="primary"
                        href={homeworkLink}
                        target="_blank"
                        rel="noopener noreferrer"
                        icon={<ExportOutlined />}
                        className="mt-4 bg-indigo-600 hover:bg-indigo-700 h-9 font-medium"
                    >
                        {isCoding ? 'Nộp bài tập trên Quiz ngay' : 'Chơi Game trắc nghiệm ngay'}
                    </Button>
                )}
            </div>
        );
    }

    // Sắp xếp các lần nộp theo thời gian mới nhất lên đầu
    const sorted = [...submissions].sort(
        (a, b) => dayjs(b.submitted_at).valueOf() - dayjs(a.submitted_at).valueOf()
    );

    const latest = sorted[0];
    const isLatestLate = dayjs(latest.submitted_at).isAfter(deadlineObj);

    return (
        <div className="space-y-5">
            {/* Status Summary Card */}
            <div className="p-4 rounded-xl border border-emerald-100 bg-gradient-to-br from-emerald-50/70 via-teal-50/30 to-white shadow-2xs">
                <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-2.5">
                        <div className="w-10 h-10 rounded-lg bg-emerald-100 text-emerald-600 flex items-center justify-center text-lg shadow-2xs">
                            <CheckCircleOutlined />
                        </div>
                        <div>
                            <div className="flex items-center gap-2">
                                <span className="font-bold text-sm text-gray-900">
                                    {isCoding ? 'Đã nộp bài Coding' : 'Đã hoàn thành Game (100%)'}
                                </span>
                                {isLatestLate ? (
                                    <Tag color="error" className="m-0 text-xs font-medium">Nộp trễ</Tag>
                                ) : (
                                    <Tag color="success" className="m-0 text-xs font-medium">Đúng hạn</Tag>
                                )}
                            </div>
                            <Text type="secondary" className="text-xs block mt-0.5">
                                Gần nhất: {dayjs(latest.submitted_at).format('DD/MM/YYYY HH:mm:ss')} ({dayjs(latest.submitted_at).fromNow()})
                            </Text>
                        </div>
                    </div>
                    <Tag color="blue" className="m-0 font-semibold text-xs">
                        {sorted.length} lần nộp
                    </Tag>
                </div>
            </div>

            {/* Timeline Lịch sử */}
            <div>
                <div className="flex items-center justify-between mb-3">
                    <Text className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                        Chi tiết các lần nộp ({sorted.length})
                    </Text>
                    {homeworkLink && (
                        <Button
                            type="link"
                            href={homeworkLink}
                            target="_blank"
                            rel="noopener noreferrer"
                            icon={<ExportOutlined />}
                            size="small"
                            className="p-0 text-xs text-indigo-600 font-medium"
                        >
                            Làm lại trên Quiz
                        </Button>
                    )}
                </div>

                <Timeline
                    mode="left"
                    items={sorted.map((sub, idx) => {
                        const subTime = dayjs(sub.submitted_at);
                        const isLate = subTime.isAfter(deadlineObj);
                        const attemptNum = sorted.length - idx;

                        return {
                            color: isLate ? '#ef4444' : '#10b981',
                            label: (
                                <div className="text-right pr-2">
                                    <Text className="text-xs font-semibold block text-gray-700">
                                        {subTime.format('DD/MM/YYYY')}
                                    </Text>
                                    <Text type="secondary" className="text-[11px] block">
                                        {subTime.format('HH:mm:ss')}
                                    </Text>
                                </div>
                            ),
                            children: (
                                <Card
                                    size="small"
                                    className="!rounded-xl border-gray-100 shadow-2xs hover:shadow-xs transition-shadow mb-3 bg-white"
                                >
                                    <div className="flex items-center justify-between gap-2 flex-wrap mb-1.5">
                                        <div className="flex items-center gap-2">
                                            <span className="font-bold text-xs text-gray-800">
                                                Lần nộp #{attemptNum}
                                            </span>
                                            {isLate ? (
                                                <Tag color="error" className="m-0 text-[10px] font-semibold">
                                                    Quá hạn {subTime.from(deadlineObj, true)}
                                                </Tag>
                                            ) : (
                                                <Tag color="success" className="m-0 text-[10px] font-semibold">
                                                    Trước hạn {deadlineObj.from(subTime, true)}
                                                </Tag>
                                            )}
                                        </div>
                                        <Tag
                                            color={sub.source === 'WEBHOOK' ? 'cyan' : 'default'}
                                            className="m-0 text-[10px]"
                                        >
                                            {sub.source === 'WEBHOOK' ? 'Realtime' : 'Đồng bộ'}
                                        </Tag>
                                    </div>

                                    {/* Metadata Payload Details */}
                                    {sub.metadata && Object.keys(sub.metadata).length > 0 && (
                                        <div className="mt-2 text-xs bg-slate-50 dark:bg-zinc-800 p-2 rounded-lg border border-slate-100 dark:border-zinc-700 space-y-1">
                                            {sub.metadata.final_score !== undefined && (
                                                <div className="flex justify-between text-gray-600">
                                                    <span>Điểm số:</span>
                                                    <span className="font-semibold text-indigo-600">
                                                        {sub.metadata.final_score}
                                                    </span>
                                                </div>
                                            )}
                                            {sub.metadata.correct_count !== undefined && (
                                                <div className="flex justify-between text-gray-600">
                                                    <span>Số câu đúng:</span>
                                                    <span className="font-semibold text-emerald-600">
                                                        {sub.metadata.correct_count}/{sub.metadata.total_questions ?? sub.metadata.correct_count} (100%)
                                                    </span>
                                                </div>
                                            )}
                                            {sub.metadata.commit_sha && (
                                                <div className="flex justify-between text-gray-600">
                                                    <span>Commit:</span>
                                                    <code className="text-gray-800 bg-white px-1 rounded border">
                                                        {sub.metadata.commit_sha.slice(0, 8)}
                                                    </code>
                                                </div>
                                            )}
                                            {sub.metadata.original_filename && (
                                                <div className="flex justify-between text-gray-600 truncate">
                                                    <span>Tệp nộp:</span>
                                                    <span className="font-medium text-gray-800 truncate max-w-[200px]" title={sub.metadata.original_filename}>
                                                        {sub.metadata.original_filename}
                                                    </span>
                                                </div>
                                            )}
                                            {sub.metadata.max_score !== undefined && (
                                                <div className="flex justify-between text-gray-600">
                                                    <span>Điểm tối đa:</span>
                                                    <span className="font-semibold text-indigo-600">
                                                        {sub.metadata.max_score}
                                                    </span>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </Card>
                            ),
                        };
                    })}
                />
            </div>
        </div>
    );
};
