import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import {
    Drawer, Tabs, Spin, Tag, Grid, Button, Space, message
} from 'antd';
import {
    WarningOutlined, SyncOutlined, CodeOutlined, PlayCircleOutlined,
    LinkOutlined, ClockCircleOutlined, CalendarOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/vi';

import {
    useHomeworkSubmissionStatus,
    useSyncHomeworkFromQuiz
} from '@/features/homework/hooks/useHomeworks';
import type { Homework, UserSubmissionInfo } from '@/features/homework/types/homework.types';
import { HomeworkOverviewStats } from './HomeworkOverviewStats';
import { UserSubmissionCategoryView } from './UserSubmissionCategoryView';
import { SubmissionHistoryModal } from './SubmissionHistoryModal';

dayjs.extend(relativeTime);
dayjs.locale('vi');

const { useBreakpoint } = Grid;

const MIN_WIDTH = 380;
const MAX_WIDTH = 960;
const DEFAULT_WIDTH = 580;

interface HomeworkDetailDrawerProps {
    homework: Homework | null;
    onClose: () => void;
}

export const HomeworkDetailDrawer: React.FC<HomeworkDetailDrawerProps> = ({ homework, onClose }) => {
    const screens = useBreakpoint();
    const isOverdue = homework ? dayjs().isAfter(dayjs(homework.deadline)) : false;

    const [drawerWidth, setDrawerWidth] = useState(DEFAULT_WIDTH);
    const isResizing = useRef(false);
    const startX = useRef(0);
    const startWidth = useRef(0);

    // Reset width when switching responsive breakpoints
    useEffect(() => {
        if (!screens.md) setDrawerWidth(window.innerWidth);
        else setDrawerWidth(DEFAULT_WIDTH);
    }, [screens.md]);

    const handleMouseMove = useCallback((e: MouseEvent) => {
        if (!isResizing.current) return;
        const delta = startX.current - e.clientX;
        const newWidth = Math.min(Math.max(startWidth.current + delta, MIN_WIDTH), MAX_WIDTH);
        setDrawerWidth(newWidth);
    }, []);

    const handleMouseUp = useCallback(() => {
        isResizing.current = false;
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
    }, [handleMouseMove]);

    const handleResizeMouseDown = useCallback((e: React.MouseEvent) => {
        e.preventDefault();
        isResizing.current = true;
        startX.current = e.clientX;
        startWidth.current = drawerWidth;
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
    }, [drawerWidth, handleMouseMove, handleMouseUp]);

    useEffect(() => {
        return () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };
    }, [handleMouseMove, handleMouseUp]);

    const { data: statusData, isLoading, refetch } = useHomeworkSubmissionStatus(homework?.id ?? null);
    const syncMutation = useSyncHomeworkFromQuiz();
    const [historyUser, setHistoryUser] = useState<UserSubmissionInfo | null>(null);

    const handleSync = async () => {
        if (!homework) return;
        try {
            const res = await syncMutation.mutateAsync(homework.id);
            message.success(res?.message || 'Đồng bộ bài tập từ Quiz thành công!');
            refetch();
        } catch (error: any) {
            message.error(error?.response?.data?.message || 'Đồng bộ từ Quiz thất bại');
        }
    };

    const handleViewHistory = (user: UserSubmissionInfo) => {
        setHistoryUser(user);
    };

    // Chuẩn bị dữ liệu Coding & Game
    const codingStatus = useMemo(() => {
        return statusData?.coding ?? {
            submitted: statusData?.submitted ?? [],
            not_submitted: statusData?.not_submitted ?? []
        };
    }, [statusData]);

    const gameStatus = useMemo(() => {
        return statusData?.game ?? { submitted: [], not_submitted: [] };
    }, [statusData]);

    const hasCoding = homework?.requires_coding ?? true;
    const hasGame = homework?.requires_game ?? false;

    // Số liệu thống kê tổng thể
    const codingSubmittedCount = codingStatus.submitted.length;
    const codingTotalCount = codingSubmittedCount + codingStatus.not_submitted.length;

    const gameSubmittedCount = gameStatus.submitted.length;
    const gameTotalCount = gameSubmittedCount + gameStatus.not_submitted.length;

    // Tính tổng người đã nộp và tổng người được giao
    const totalSubmitted = statusData?.submitted?.length ?? (
        hasCoding && !hasGame
            ? codingSubmittedCount
            : !hasCoding && hasGame
                ? gameSubmittedCount
                : Math.max(codingSubmittedCount, gameSubmittedCount)
    );

    const totalAssigned = (statusData?.submitted?.length ?? 0) + (statusData?.not_submitted?.length ?? 0) || (
        hasCoding && !hasGame
            ? codingTotalCount
            : !hasCoding && hasGame
                ? gameTotalCount
                : Math.max(codingTotalCount, gameTotalCount)
    );

    const submissionPercent = totalAssigned > 0
        ? Math.round((totalSubmitted / totalAssigned) * 100)
        : 0;

    // Tabs thông minh theo yêu cầu của bài tập
    const tabItems = useMemo(() => {
        const items = [];

        if (hasCoding) {
            items.push({
                key: 'coding',
                label: (
                    <span className="flex items-center gap-1.5 font-medium">
                        <CodeOutlined className="text-indigo-600" />
                        Coding Homework
                        {codingTotalCount > 0 && (
                            <Tag color="default" className="m-0 text-xs px-1.5 py-0 rounded-full font-normal">
                                {codingSubmittedCount}/{codingTotalCount}
                            </Tag>
                        )}
                    </span>
                ),
                children: (
                    <UserSubmissionCategoryView
                        status={codingStatus}
                        isLoading={isLoading}
                        isOverdue={isOverdue}
                        onViewHistory={handleViewHistory}
                    />
                ),
            });
        }

        if (hasGame) {
            items.push({
                key: 'game',
                label: (
                    <span className="flex items-center gap-1.5 font-medium">
                        <PlayCircleOutlined className="text-purple-600" />
                        Quiz Game
                        {gameTotalCount > 0 && (
                            <Tag color="default" className="m-0 text-xs px-1.5 py-0 rounded-full font-normal">
                                {gameSubmittedCount}/{gameTotalCount}
                            </Tag>
                        )}
                    </span>
                ),
                children: (
                    <UserSubmissionCategoryView
                        status={gameStatus}
                        isLoading={isLoading}
                        isOverdue={isOverdue}
                        onViewHistory={handleViewHistory}
                    />
                ),
            });
        }

        // Fallback nếu bài tập không tick cả 2
        if (items.length === 0) {
            items.push({
                key: 'coding',
                label: 'Bài nộp',
                children: (
                    <UserSubmissionCategoryView
                        status={codingStatus}
                        isLoading={isLoading}
                        isOverdue={isOverdue}
                        onViewHistory={handleViewHistory}
                    />
                ),
            });
        }

        return items;
    }, [hasCoding, hasGame, codingStatus, gameStatus, codingSubmittedCount, codingTotalCount, gameSubmittedCount, gameTotalCount, isLoading, isOverdue]);

    return (
        <>
            <Drawer
                title={
                    <div className="flex flex-col gap-1 py-1">
                        <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-bold text-base text-gray-900 dark:text-gray-50 leading-tight">
                                {homework?.title}
                            </span>
                            {homework?.slug && (
                                <Tag color="geekblue" className="m-0 text-xs font-mono rounded-md">
                                    {homework.slug}
                                </Tag>
                            )}
                        </div>

                        <div className="flex items-center gap-2 flex-wrap text-xs text-gray-500 font-normal">
                            <span className="flex items-center gap-1">
                                <CalendarOutlined className="text-gray-400" />
                                Hạn nộp: <b className="text-gray-700 dark:text-gray-300">
                                    {homework ? dayjs(homework.deadline).format('DD/MM/YYYY HH:mm') : ''}
                                </b>
                            </span>

                            {isOverdue ? (
                                <Tag color="error" icon={<WarningOutlined />} className="text-xs m-0 rounded-md">
                                    Đã quá hạn ({dayjs(homework?.deadline).fromNow()})
                                </Tag>
                            ) : (
                                <Tag color="processing" icon={<ClockCircleOutlined />} className="text-xs m-0 rounded-md">
                                    Đang mở (Còn {dayjs(homework?.deadline).fromNow(true)})
                                </Tag>
                            )}

                            {homework?.link && (
                                <a
                                    href={homework.link}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="inline-flex items-center gap-1 text-indigo-600 hover:text-indigo-700 text-xs ml-1"
                                >
                                    <LinkOutlined /> Mở đề bài
                                </a>
                            )}
                        </div>
                    </div>
                }
                extra={
                    <Space size="small">
                        <Button
                            type="primary"
                            icon={<SyncOutlined spin={syncMutation.isPending} />}
                            loading={syncMutation.isPending}
                            onClick={handleSync}
                            size="small"
                            className="bg-indigo-600 hover:bg-indigo-700 rounded-lg flex items-center shadow-xs"
                        >
                            Đồng bộ từ Quiz
                        </Button>
                    </Space>
                }
                placement="right"
                width={screens.md ? drawerWidth : '100%'}
                onClose={onClose}
                open={!!homework}
                styles={{
                    header: { padding: '12px 20px', borderBottom: '1px solid #f1f5f9' },
                    body: { padding: '16px 20px', position: 'relative', overflowY: 'auto' }
                }}
            >
                {/* Resize Handle ở cạnh trái (Desktop) */}
                {screens.md && (
                    <div
                        onMouseDown={handleResizeMouseDown}
                        title="Kéo sang trái để mở rộng kích thước drawer"
                        style={{
                            position: 'absolute',
                            left: 0,
                            top: 0,
                            bottom: 0,
                            width: '6px',
                            cursor: 'col-resize',
                            zIndex: 20,
                            background: 'transparent',
                            transition: 'background 0.2s',
                        }}
                        onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(99, 102, 241, 0.35)')}
                        onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                    />
                )}

                {/* Bento Overview Stats Card */}
                <HomeworkOverviewStats
                    submissionPercent={submissionPercent}
                    totalSubmitted={totalSubmitted}
                    totalAssigned={totalAssigned}
                />

                {/* Main Content Tabs */}
                {isLoading && !statusData ? (
                    <div className="flex flex-col items-center justify-center h-48 gap-3 text-gray-400">
                        <Spin size="large" />
                        <span className="text-xs">Đang nạp trạng thái nộp bài của học viên...</span>
                    </div>
                ) : (
                    <Tabs
                        defaultActiveKey={hasCoding ? 'coding' : 'game'}
                        items={tabItems}
                        size="middle"
                        className="homework-detail-tabs"
                    />
                )}
            </Drawer>

            {/* Modal Lịch sử bài nộp của 1 học viên */}
            <SubmissionHistoryModal
                homeworkId={homework?.id ?? null}
                user={historyUser}
                open={!!historyUser}
                onClose={() => setHistoryUser(null)}
            />
        </>
    );
};
