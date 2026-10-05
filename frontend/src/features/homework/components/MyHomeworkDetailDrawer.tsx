import React from 'react';
import {
    Drawer,
    Tabs,
    Tag,
    Timeline,
    Typography,
    Empty,
    Spin,
    Button,
    Grid,
    Card,
    Alert,
} from 'antd';
import {
    CodeOutlined,
    TrophyOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined,
    ClockCircleOutlined,
    ExportOutlined,
    CalendarOutlined,
    ThunderboltOutlined,
    WarningOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/vi';

import { useHomework, useMyHomeworkSubmissions } from '../hooks/useHomeworks';
import type { SubmissionHistoryItem } from '../types/homework.types';

dayjs.extend(relativeTime);
dayjs.locale('vi');

const { Text, Title } = Typography;
const { useBreakpoint } = Grid;

interface MyHomeworkDetailDrawerProps {
    homeworkId: number | null;
    open: boolean;
    onClose: () => void;
}

const SubmissionTimeline: React.FC<{
    submissions: SubmissionHistoryItem[];
    type: 'CODING' | 'GAME';
    deadline: string;
    homeworkLink?: string | null;
}> = ({ submissions, type, deadline, homeworkLink }) => {
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

export const MyHomeworkDetailDrawer: React.FC<MyHomeworkDetailDrawerProps> = ({
    homeworkId,
    open,
    onClose,
}) => {
    const screens = useBreakpoint();

    const { data: homework, isLoading: isHwLoading } = useHomework(open ? homeworkId : null);
    const { data: submissions = [], isLoading: isSubLoading } = useMyHomeworkSubmissions(
        open ? homeworkId : null
    );

    const isLoading = isHwLoading || isSubLoading;

    const deadlineObj = homework ? dayjs(homework.deadline) : null;
    const isOverdue = deadlineObj ? dayjs().isAfter(deadlineObj) : false;

    // Lọc theo yêu cầu của bài tập:
    // requires_coding: có phần Coding hay không
    // requires_game: có phần Game hay không
    const requiresCoding = homework?.requires_coding ?? true;
    const requiresGame = homework?.requires_game ?? false;

    const hasBoth = requiresCoding && requiresGame;
    const hasOnlyCoding = requiresCoding && !requiresGame;
    const hasOnlyGame = !requiresCoding && requiresGame;

    // Phân loại submissions
    const codingSubmissions = submissions.filter((s) => s.submission_type === 'CODING');
    const gameSubmissions = submissions.filter((s) => s.submission_type === 'GAME');

    return (
        <Drawer
            title={
                <div className="flex flex-col gap-1 pr-2">
                    <span className="font-bold text-base leading-snug line-clamp-1 text-gray-900">
                        {homework?.title || 'Chi tiết bài tập'}
                    </span>
                    <div className="flex items-center gap-2 flex-wrap">
                        {deadlineObj && (
                            <span className="inline-flex items-center gap-1 text-xs text-gray-500 font-normal">
                                <CalendarOutlined className="text-gray-400" />
                                Hạn nộp: {deadlineObj.format('DD/MM/YYYY HH:mm')}
                            </span>
                        )}
                        {isOverdue ? (
                            <Tag color="red" icon={<WarningOutlined />} className="text-xs m-0 font-medium">
                                Quá hạn
                            </Tag>
                        ) : (
                            <Tag color="blue" icon={<ClockCircleOutlined />} className="text-xs m-0 font-medium">
                                Đang mở
                            </Tag>
                        )}
                    </div>
                </div>
            }
            extra={
                homework?.link ? (
                    <Button
                        type="primary"
                        href={homework.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        icon={<ExportOutlined />}
                        size="small"
                        className="bg-indigo-600 hover:bg-indigo-700 font-semibold"
                    >
                        Làm bài Quiz
                    </Button>
                ) : null
            }
            placement="right"
            width={screens.md ? 520 : '100%'}
            open={open}
            onClose={onClose}
            styles={{ body: { padding: '16px 20px' } }}
        >
            {isLoading ? (
                <div className="py-20 flex flex-col justify-center items-center gap-3">
                    <Spin size="large" />
                    <Text type="secondary" className="text-xs">Đang tải lịch sử làm bài...</Text>
                </div>
            ) : !homework ? (
                <Empty description="Không tìm thấy thông tin bài tập" />
            ) : (
                <div className="space-y-4">
                    {/* Yêu cầu nộp bài Alert */}
                    <Alert
                        type="info"
                        showIcon
                        icon={<ThunderboltOutlined />}
                        className="text-xs rounded-xl"
                        message={
                            <span>
                                Tiêu chuẩn hoàn thành:
                                {hasBoth && (
                                    <b> Nộp file Coding và Hoàn thành Game trắc nghiệm (đúng 100%).</b>
                                )}
                                {hasOnlyCoding && <b> Nộp file bài tập Coding thành công.</b>}
                                {hasOnlyGame && <b> Hoàn thành Game trắc nghiệm đúng 100% câu hỏi.</b>}
                            </span>
                        }
                    />

                    {/* HIỂN THỊ THEO YÊU CẦU BÀI TẬP: */}
                    {hasBoth ? (
                        /* Trường hợp có CẢ HAI: Hiển thị 2 Tab Coding & Game */
                        <Tabs
                            defaultActiveKey="coding"
                            items={[
                                {
                                    key: 'coding',
                                    label: (
                                        <span className="flex items-center gap-1.5 font-semibold">
                                            <CodeOutlined />
                                            Bài tập Coding
                                            {codingSubmissions.length > 0 ? (
                                                <Tag color="success" className="m-0 text-[10px] ml-1">Đã nộp</Tag>
                                            ) : (
                                                <Tag color="default" className="m-0 text-[10px] ml-1">Chưa nộp</Tag>
                                            )}
                                        </span>
                                    ),
                                    children: (
                                        <SubmissionTimeline
                                            submissions={codingSubmissions}
                                            type="CODING"
                                            deadline={homework.deadline}
                                            homeworkLink={homework.link}
                                        />
                                    ),
                                },
                                {
                                    key: 'game',
                                    label: (
                                        <span className="flex items-center gap-1.5 font-semibold">
                                            <TrophyOutlined />
                                            Trắc nghiệm Game
                                            {gameSubmissions.length > 0 ? (
                                                <Tag color="success" className="m-0 text-[10px] ml-1">Đã xong</Tag>
                                            ) : (
                                                <Tag color="default" className="m-0 text-[10px] ml-1">Chưa xong</Tag>
                                            )}
                                        </span>
                                    ),
                                    children: (
                                        <SubmissionTimeline
                                            submissions={gameSubmissions}
                                            type="GAME"
                                            deadline={homework.deadline}
                                            homeworkLink={homework.link}
                                        />
                                    ),
                                },
                            ]}
                        />
                    ) : hasOnlyCoding ? (
                        /* Trường hợp CHỈ CÓ Coding: Chỉ hiển thị 1 SubmissionType Coding */
                        <div className="pt-2">
                            <div className="flex items-center gap-2 mb-4 pb-2 border-b border-gray-100">
                                <CodeOutlined className="text-indigo-600 text-base" />
                                <Title level={5} className="!mb-0 text-sm font-bold text-gray-800">
                                    Lịch sử nộp bài Coding
                                </Title>
                            </div>
                            <SubmissionTimeline
                                submissions={codingSubmissions}
                                type="CODING"
                                deadline={homework.deadline}
                                homeworkLink={homework.link}
                            />
                        </div>
                    ) : hasOnlyGame ? (
                        /* Trường hợp CHỈ CÓ Game: Chỉ hiển thị 1 SubmissionType Game */
                        <div className="pt-2">
                            <div className="flex items-center gap-2 mb-4 pb-2 border-b border-gray-100">
                                <TrophyOutlined className="text-purple-600 text-base" />
                                <Title level={5} className="!mb-0 text-sm font-bold text-gray-800">
                                    Lịch sử chơi Game trắc nghiệm
                                </Title>
                            </div>
                            <SubmissionTimeline
                                submissions={gameSubmissions}
                                type="GAME"
                                deadline={homework.deadline}
                                homeworkLink={homework.link}
                            />
                        </div>
                    ) : (
                        /* Fallback nếu không cấu hình: hiển thị Coding */
                        <div className="pt-2">
                            <div className="flex items-center gap-2 mb-4 pb-2 border-b border-gray-100">
                                <CodeOutlined className="text-indigo-600 text-base" />
                                <Title level={5} className="!mb-0 text-sm font-bold text-gray-800">
                                    Lịch sử nộp bài tập
                                </Title>
                            </div>
                            <SubmissionTimeline
                                submissions={codingSubmissions}
                                type="CODING"
                                deadline={homework.deadline}
                                homeworkLink={homework.link}
                            />
                        </div>
                    )}
                </div>
            )}
        </Drawer>
    );
};

export default MyHomeworkDetailDrawer;
