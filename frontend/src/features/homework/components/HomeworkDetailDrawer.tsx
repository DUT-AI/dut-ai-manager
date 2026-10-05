import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import {
    Drawer, Tabs, Avatar, Badge, Empty, Spin, Tag, Grid, Typography, Button,
    Modal, Timeline, Space, message, Tooltip, Input, Progress, Segmented
} from 'antd';
import {
    UserOutlined, CheckCircleOutlined, CloseCircleOutlined, WarningOutlined,
    SyncOutlined, HistoryOutlined, CodeOutlined, PlayCircleOutlined,
    SearchOutlined, LinkOutlined, ClockCircleOutlined, CalendarOutlined,
    CheckOutlined, TeamOutlined, TrophyOutlined, ExclamationCircleOutlined,
    FilterOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/vi';

import {
    useHomeworkSubmissionStatus,
    useSyncHomeworkFromQuiz,
    useHomeworkSubmissions
} from '@/features/homework/hooks/useHomeworks';
import type { Homework, UserSubmissionInfo, SubmissionHistoryItem } from '@/features/homework/types/homework.types';

dayjs.extend(relativeTime);
dayjs.locale('vi');

const { Text, Title } = Typography;
const { useBreakpoint } = Grid;

const MIN_WIDTH = 380;
const MAX_WIDTH = 960;
const DEFAULT_WIDTH = 580;

interface HomeworkDetailDrawerProps {
    homework: Homework | null;
    onClose: () => void;
}

// -------------------------------------------------------------
// MODAL: Lịch sử nộp bài (Audit Log) của học viên
// -------------------------------------------------------------
const SubmissionHistoryModal: React.FC<{
    homeworkId: number | null;
    user: UserSubmissionInfo | null;
    open: boolean;
    onClose: () => void;
}> = ({ homeworkId, user, open, onClose }) => {
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

// -------------------------------------------------------------
// COMPONENT: Item hiển thị một học viên
// -------------------------------------------------------------
const UserCardItem: React.FC<{
    user: UserSubmissionInfo;
    isSubmitted: boolean;
    onViewHistory?: (user: UserSubmissionInfo) => void;
}> = ({ user, isSubmitted, onViewHistory }) => {
    return (
        <div className="group flex items-center justify-between gap-3 p-3 rounded-xl bg-white dark:bg-zinc-800/80 border border-gray-100 dark:border-zinc-700/60 hover:border-indigo-300 dark:hover:border-zinc-500 hover:shadow-xs transition-all mb-2">
            <div className="flex items-center gap-3 min-w-0 flex-1">
                <div className="relative flex-shrink-0">
                    <Avatar
                        src={user.avatar_url || undefined}
                        icon={<UserOutlined />}
                        size={40}
                        className={
                            isSubmitted
                                ? (user.is_late ? 'bg-amber-500' : 'bg-indigo-600')
                                : 'bg-gray-400'
                        }
                    />
                    <span
                        className={`absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-white dark:border-zinc-800 ${isSubmitted
                            ? (user.is_late ? 'bg-amber-500' : 'bg-emerald-500')
                            : 'bg-rose-400'
                            }`}
                        title={isSubmitted ? (user.is_late ? 'Nộp trễ' : 'Đã nộp') : 'Chưa nộp'}
                    />
                </div>

                <div className="flex flex-col min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm text-gray-800 dark:text-gray-100 truncate">
                            {user.name || `Học viên #${user.user_id}`}
                        </span>
                        <span className="text-[11px] text-gray-400 font-mono">
                            #{user.user_id}
                        </span>
                    </div>

                    <div className="flex items-center gap-1.5 flex-wrap mt-0.5">
                        {isSubmitted && user.submitted_at ? (
                            <>
                                <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                                    <ClockCircleOutlined className="text-[11px]" />
                                    {dayjs(user.submitted_at).format('DD/MM/YYYY HH:mm:ss')}
                                </span>
                                <span className="text-[11px] text-gray-400">
                                    ({dayjs(user.submitted_at).fromNow()})
                                </span>
                            </>
                        ) : (
                            <span className="text-xs text-rose-500 dark:text-rose-400 flex items-center gap-1">
                                <CloseCircleOutlined className="text-[11px]" />
                                Chưa nộp bài
                            </span>
                        )}
                    </div>
                </div>
            </div>

            <div className="flex items-center gap-2 flex-shrink-0">
                {isSubmitted && (
                    user.is_late ? (
                        <Tag color="warning" className="m-0 text-xs rounded-md font-medium">
                            Nộp trễ
                        </Tag>
                    ) : (
                        <Tag color="success" className="m-0 text-xs rounded-md font-medium">
                            Đúng hạn
                        </Tag>
                    )
                )}

                {onViewHistory && isSubmitted && (
                    <Tooltip title="Xem lịch sử bài nộp chi tiết">
                        <Button
                            type="text"
                            size="small"
                            icon={<HistoryOutlined className="text-indigo-600 dark:text-indigo-400 text-sm" />}
                            className="hover:bg-indigo-50 dark:hover:bg-indigo-950/50 rounded-lg"
                            onClick={() => onViewHistory(user)}
                        />
                    </Tooltip>
                )}
            </div>
        </div>
    );
};

// -------------------------------------------------------------
// COMPONENT: Danh sách học viên có tích hợp Search & Filter
// -------------------------------------------------------------
const UserCategoryView: React.FC<{
    status?: { submitted: UserSubmissionInfo[]; not_submitted: UserSubmissionInfo[] };
    isLoading: boolean;
    isOverdue: boolean;
    onViewHistory?: (user: UserSubmissionInfo) => void;
}> = ({ status, isLoading, isOverdue, onViewHistory }) => {
    const [searchQuery, setSearchQuery] = useState('');
    const [subTab, setSubTab] = useState<'submitted' | 'not_submitted'>('submitted');
    const [submittedFilter, setSubmittedFilter] = useState<'all' | 'on_time' | 'late'>('all');

    const submitted = useMemo(() => status?.submitted ?? [], [status?.submitted]);
    const notSubmitted = useMemo(() => status?.not_submitted ?? [], [status?.not_submitted]);

    // Lọc danh sách Đã nộp theo Search & Filter Status
    const filteredSubmitted = useMemo(() => {
        return submitted.filter((u) => {
            const query = searchQuery.trim().toLowerCase();
            const matchesSearch = query
                ? (u.name?.toLowerCase().includes(query) || String(u.user_id).includes(query))
                : true;
            if (!matchesSearch) return false;

            if (submittedFilter === 'late') return !!u.is_late;
            if (submittedFilter === 'on_time') return !u.is_late;
            return true;
        });
    }, [submitted, searchQuery, submittedFilter]);

    // Lọc danh sách Chưa nộp theo Search
    const filteredNotSubmitted = useMemo(() => {
        return notSubmitted.filter((u) => {
            const query = searchQuery.trim().toLowerCase();
            return query
                ? (u.name?.toLowerCase().includes(query) || String(u.user_id).includes(query))
                : true;
        });
    }, [notSubmitted, searchQuery]);

    const lateCount = useMemo(() => submitted.filter(u => u.is_late).length, [submitted]);
    const onTimeCount = submitted.length - lateCount;

    return (
        <div className="flex flex-col gap-3 pt-1">
            {/* Search Input Bar */}
            <div className="flex items-center gap-2">
                <Input
                    prefix={<SearchOutlined className="text-gray-400" />}
                    placeholder="Tìm kiếm theo tên hoặc ID học viên..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    allowClear
                    className="rounded-lg text-sm bg-gray-50/70 dark:bg-zinc-800/80 border-gray-200 dark:border-zinc-700"
                />
            </div>

            {/* Sub-tabs: Đã nộp / Chưa nộp tích hợp bộ lọc đồng nhất */}
            <div className="border-b border-gray-100 dark:border-zinc-800">
                <Tabs
                    activeKey={subTab}
                    onChange={(val) => setSubTab(val as 'submitted' | 'not_submitted')}
                    size="small"
                    className="submission-subtabs"
                    tabBarExtraContent={
                        subTab === 'submitted' && submitted.length > 0 ? (
                            <div className="flex items-center gap-1.5 pb-1">
                                <span className="text-[11px] text-gray-400 flex items-center gap-1 font-medium">
                                    <FilterOutlined className="text-gray-400 text-xs" /> Lọc:
                                </span>
                                <Segmented
                                    size="small"
                                    value={submittedFilter}
                                    onChange={(val) => setSubmittedFilter(val as 'all' | 'on_time' | 'late')}
                                    options={[
                                        { label: `Tất cả (${submitted.length})`, value: 'all' },
                                        { label: `Đúng hạn (${onTimeCount})`, value: 'on_time' },
                                        { label: `Trễ (${lateCount})`, value: 'late' },
                                    ]}
                                    className="bg-gray-100 dark:bg-zinc-800 text-xs rounded-md"
                                />
                            </div>
                        ) : null
                    }
                    items={[
                        {
                            key: 'submitted',
                            label: (
                                <span className="flex items-center gap-1.5 font-medium text-xs pb-0.5">
                                    <CheckCircleOutlined className="text-emerald-500 text-sm" />
                                    <span>Đã nộp</span>
                                    <span className="inline-flex items-center justify-center min-w-[20px] px-1.5 py-0.2 text-[11px] font-semibold rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200/60 dark:bg-emerald-950/60 dark:text-emerald-400 dark:border-emerald-800/60">
                                        {filteredSubmitted.length}
                                    </span>
                                </span>
                            ),
                        },
                        {
                            key: 'not_submitted',
                            label: (
                                <span className="flex items-center gap-1.5 font-medium text-xs pb-0.5">
                                    <CloseCircleOutlined className="text-rose-500 text-sm" />
                                    <span>Chưa nộp</span>
                                    <span className="inline-flex items-center justify-center min-w-[20px] px-1.5 py-0.2 text-[11px] font-semibold rounded-full bg-rose-50 text-rose-600 border border-rose-200/60 dark:bg-rose-950/60 dark:text-rose-400 dark:border-rose-800/60">
                                        {filteredNotSubmitted.length}
                                    </span>
                                </span>
                            ),
                        },
                    ]}
                />
            </div>

            {/* Search query tag result notification */}
            {searchQuery.trim() && (
                <div className="flex items-center justify-between text-xs text-gray-500 bg-indigo-50/60 dark:bg-indigo-950/40 px-3 py-1.5 rounded-lg">
                    <span>
                        Kết quả cho: <b className="text-indigo-600 dark:text-indigo-400">"{searchQuery.trim()}"</b>
                    </span>
                    <span className="font-medium">
                        {subTab === 'submitted' ? filteredSubmitted.length : filteredNotSubmitted.length} học viên
                    </span>
                </div>
            )}

            {/* List Body */}
            <div className="min-h-[220px]">
                {isLoading ? (
                    <div className="flex flex-col items-center justify-center py-16 gap-2 text-gray-400">
                        <Spin size="default" />
                        <span className="text-xs">Đang tải danh sách bài nộp...</span>
                    </div>
                ) : subTab === 'submitted' ? (
                    filteredSubmitted.length === 0 ? (
                        <div className="py-12 flex flex-col items-center justify-center">
                            <Empty
                                image={Empty.PRESENTED_IMAGE_SIMPLE}
                                description={
                                    searchQuery.trim()
                                        ? `Không tìm thấy học viên đã nộp nào khớp với "${searchQuery}"`
                                        : "Chưa có học viên nào nộp bài"
                                }
                            />
                            {searchQuery.trim() && (
                                <Button
                                    size="small"
                                    onClick={() => setSearchQuery('')}
                                    className="mt-2 text-xs"
                                >
                                    Xóa tìm kiếm
                                </Button>
                            )}
                        </div>
                    ) : (
                        <div className="flex flex-col">
                            {filteredSubmitted.map((user) => (
                                <UserCardItem
                                    key={user.user_id}
                                    user={user}
                                    isSubmitted={true}
                                    onViewHistory={onViewHistory}
                                />
                            ))}
                        </div>
                    )
                ) : (
                    filteredNotSubmitted.length === 0 ? (
                        <div className="py-12 flex flex-col items-center justify-center">
                            <Empty
                                image={Empty.PRESENTED_IMAGE_SIMPLE}
                                description={
                                    searchQuery.trim()
                                        ? `Không tìm thấy học viên chưa nộp nào khớp với "${searchQuery}"`
                                        : "Tất cả học viên đều đã nộp bài 🎉"
                                }
                            />
                            {searchQuery.trim() && (
                                <Button
                                    size="small"
                                    onClick={() => setSearchQuery('')}
                                    className="mt-2 text-xs"
                                >
                                    Xóa tìm kiếm
                                </Button>
                            )}
                        </div>
                    ) : (
                        <div className="flex flex-col">
                            {filteredNotSubmitted.map((user) => (
                                <UserCardItem
                                    key={user.user_id}
                                    user={user}
                                    isSubmitted={false}
                                />
                            ))}
                        </div>
                    )
                )}
            </div>
        </div>
    );
};

// -------------------------------------------------------------
// COMPONENT CHÍNH: HomeworkDetailDrawer
// -------------------------------------------------------------
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
                    <UserCategoryView
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
                    <UserCategoryView
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
                    <UserCategoryView
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
                <div className="mb-4 p-3.5 rounded-2xl bg-gradient-to-br from-indigo-50/60 via-slate-50 to-purple-50/40 dark:from-zinc-900 dark:via-zinc-800/80 dark:to-zinc-900 border border-indigo-100/60 dark:border-zinc-700/60 shadow-xs">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-1.5">
                            <TrophyOutlined className="text-indigo-600" /> Tiến độ hoàn thành bài tập
                        </span>
                        <span className="text-xs font-bold text-indigo-600 dark:text-indigo-400">
                            {submissionPercent}% ({totalSubmitted}/{totalAssigned} học viên)
                        </span>
                    </div>

                    <Progress
                        percent={submissionPercent}
                        showInfo={false}
                        strokeColor={{
                            '0%': '#6366f1',
                            '100%': '#10b981',
                        }}
                        trailColor="#e2e8f0"
                        size={['100%', 8]}
                        className="mb-3"
                    />

                    <div className="grid grid-cols-3 gap-2 text-center">
                        <div className="p-2 rounded-xl bg-white dark:bg-zinc-800/90 border border-gray-100 dark:border-zinc-700/60 shadow-2xs">
                            <div className="text-[11px] text-gray-400 flex items-center justify-center gap-1">
                                <TeamOutlined /> Được giao
                            </div>
                            <div className="text-base font-bold text-gray-800 dark:text-gray-100 mt-0.5">
                                {totalAssigned}
                            </div>
                        </div>

                        <div className="p-2 rounded-xl bg-white dark:bg-zinc-800/90 border border-gray-100 dark:border-zinc-700/60 shadow-2xs">
                            <div className="text-[11px] text-emerald-600 dark:text-emerald-400 flex items-center justify-center gap-1 font-medium">
                                <CheckCircleOutlined /> Đã nộp
                            </div>
                            <div className="text-base font-bold text-emerald-600 dark:text-emerald-400 mt-0.5">
                                {totalSubmitted}
                            </div>
                        </div>

                        <div className="p-2 rounded-xl bg-white dark:bg-zinc-800/90 border border-gray-100 dark:border-zinc-700/60 shadow-2xs">
                            <div className="text-[11px] text-rose-500 dark:text-rose-400 flex items-center justify-center gap-1 font-medium">
                                <CloseCircleOutlined /> Chưa nộp
                            </div>
                            <div className="text-base font-bold text-rose-500 dark:text-rose-400 mt-0.5">
                                {Math.max(0, totalAssigned - totalSubmitted)}
                            </div>
                        </div>
                    </div>
                </div>

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
