import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Drawer, Tabs, List, Avatar, Badge, Empty, Spin, Tag, Grid, Typography, Button, Modal, Timeline, Space, message, Tooltip } from 'antd';
import {
    UserOutlined, CheckCircleOutlined, CloseCircleOutlined, WarningOutlined,
    SyncOutlined, HistoryOutlined, CodeOutlined, PlayCircleOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import {
    useHomeworkSubmissionStatus,
    useSyncHomeworkFromQuiz,
    useHomeworkSubmissions
} from '@/features/homework/hooks/useHomeworks';
import type { Homework, UserSubmissionInfo, SubmissionHistoryItem } from '@/features/homework/types/homework.types';

const { Text } = Typography;
const { useBreakpoint } = Grid;

const MIN_WIDTH = 320;
const MAX_WIDTH = 900;
const DEFAULT_WIDTH = 460;

interface HomeworkDetailDrawerProps {
    homework: Homework | null;
    onClose: () => void;
}

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
                <Space>
                    <HistoryOutlined className="text-indigo-600" />
                    <span>Lịch sử nộp bài - {user?.name || `User #${user?.user_id}`}</span>
                </Space>
            }
            open={open}
            onCancel={onClose}
            footer={[
                <Button key="close" onClick={onClose}>
                    Đóng
                </Button>
            ]}
            width={520}
        >
            <div className="py-4 max-h-[60vh] overflow-y-auto">
                {isLoading ? (
                    <div className="flex justify-center py-8"><Spin /></div>
                ) : submissions.length === 0 ? (
                    <Empty description="Chưa có dữ liệu lịch sử nộp bài" />
                ) : (
                    <Timeline
                        mode="left"
                        items={submissions.map((sub: SubmissionHistoryItem) => {
                            const isCoding = sub.submission_type === 'CODING';
                            return {
                                color: isCoding ? '#3b82f6' : '#8b5cf6',
                                label: (
                                    <Text type="secondary" className="text-xs">
                                        {dayjs(sub.submitted_at).format('DD/MM/YYYY HH:mm:ss')}
                                    </Text>
                                ),
                                children: (
                                    <div className="bg-gray-50 dark:bg-zinc-800 p-2.5 rounded-lg border border-gray-100 dark:border-zinc-700 mb-2">
                                        <div className="flex items-center justify-between gap-2">
                                            <Tag
                                                icon={isCoding ? <CodeOutlined /> : <PlayCircleOutlined />}
                                                color={isCoding ? 'blue' : 'purple'}
                                                className="m-0 font-medium"
                                            >
                                                {isCoding ? 'Coding Homework' : 'Quiz Game'}
                                            </Tag>
                                            <Tag color={sub.source === 'WEBHOOK' ? 'cyan' : 'default'} className="m-0 text-xs">
                                                {sub.source === 'WEBHOOK' ? 'Quiz Realtime' : 'Manual Sync'}
                                            </Tag>
                                        </div>
                                        {sub.metadata && (
                                            <div className="mt-2 text-xs text-gray-500 bg-white dark:bg-zinc-900 p-1.5 rounded border border-gray-100">
                                                {sub.metadata.game_mode && (
                                                    <div>Chế độ: <b>{sub.metadata.game_mode}</b></div>
                                                )}
                                                {sub.metadata.commit_sha && (
                                                    <div>Commit: <code>{sub.metadata.commit_sha.slice(0, 8)}</code></div>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                ),
                            };
                        })}
                    />
                )}
            </div>
        </Modal>
    );
};

const UserListItem: React.FC<{
    user: UserSubmissionInfo;
    onViewHistory?: (user: UserSubmissionInfo) => void;
}> = ({ user, onViewHistory }) => (
    <List.Item className="!px-0 !py-2">
        <div className="flex items-center gap-3 w-full">
            <Avatar src={user.avatar_url || undefined} icon={<UserOutlined />} size={36} className="flex-shrink-0" />
            <div className="flex flex-col flex-1 min-w-0">
                <Text className="font-medium text-sm truncate">
                    {user.name || `User #${user.user_id}`}
                </Text>
                {user.submitted_at && (
                    <Text type="secondary" className="text-xs">
                        Nộp lúc: {dayjs(user.submitted_at).format('DD/MM/YYYY HH:mm')}
                    </Text>
                )}
            </div>
            {user.is_late && (
                <Tag color="error" className="m-0 font-medium text-xs">
                    Trễ
                </Tag>
            )}
            {onViewHistory && (
                <Tooltip title="Xem lịch sử nộp bài">
                    <Button
                        type="text"
                        size="small"
                        icon={<HistoryOutlined className="text-indigo-600" />}
                        onClick={() => onViewHistory(user)}
                    />
                </Tooltip>
            )}
        </div>
    </List.Item>
);

const UserList: React.FC<{
    data: UserSubmissionInfo[];
    isLoading: boolean;
    emptyText: string;
    onViewHistory?: (user: UserSubmissionInfo) => void;
}> = ({
    data, isLoading, emptyText, onViewHistory,
}) => (
    <div className="mt-2">
        {isLoading ? (
            <div className="flex justify-center py-8"><Spin /></div>
        ) : data.length === 0 ? (
            <Empty description={emptyText} imageStyle={{ height: 60 }} />
        ) : (
            <List
                dataSource={data}
                renderItem={(user) => <UserListItem user={user} onViewHistory={onViewHistory} />}
                split={false}
            />
        )}
    </div>
);

const CategorySubmissionView: React.FC<{
    status?: { submitted: UserSubmissionInfo[]; not_submitted: UserSubmissionInfo[] };
    isLoading: boolean;
    isOverdue: boolean;
    onViewHistory?: (user: UserSubmissionInfo) => void;
}> = ({ status, isLoading, isOverdue, onViewHistory }) => {
    const submitted = status?.submitted ?? [];
    const notSubmitted = status?.not_submitted ?? [];

    const subTabItems = [
        {
            key: 'submitted',
            label: (
                <span className="flex items-center gap-1.5">
                    <CheckCircleOutlined className="text-green-500" />
                    Đã nộp
                    <Badge count={submitted.length} showZero style={{ backgroundColor: '#22c55e' }} />
                </span>
            ),
            children: (
                <UserList
                    data={submitted}
                    isLoading={isLoading}
                    emptyText="Chưa có ai nộp bài"
                    onViewHistory={onViewHistory}
                />
            ),
        },
        ...(isOverdue ? [{
            key: 'not_submitted',
            label: (
                <span className="flex items-center gap-1.5">
                    <CloseCircleOutlined className="text-red-500" />
                    Chưa nộp
                    <Badge count={notSubmitted.length} showZero style={{ backgroundColor: '#ef4444' }} />
                </span>
            ),
            children: (
                <UserList
                    data={notSubmitted}
                    isLoading={isLoading}
                    emptyText="Tất cả đã nộp bài 🎉"
                />
            ),
        }] : []),
    ];

    return <Tabs defaultActiveKey="submitted" items={subTabItems} size="small" />;
};

export const HomeworkDetailDrawer: React.FC<HomeworkDetailDrawerProps> = ({ homework, onClose }) => {
    const screens = useBreakpoint();
    const isOverdue = homework ? dayjs().isAfter(dayjs(homework.deadline)) : false;

    const [drawerWidth, setDrawerWidth] = useState(DEFAULT_WIDTH);
    const isResizing = useRef(false);
    const startX = useRef(0);
    const startWidth = useRef(0);

    // Reset width when switching to mobile
    useEffect(() => {
        if (!screens.md) setDrawerWidth(window.innerWidth);
        else setDrawerWidth(DEFAULT_WIDTH);
    }, [screens.md]);

    const handleMouseMove = useCallback((e: MouseEvent) => {
        if (!isResizing.current) return;
        // Drawer is on the right → drag left = wider
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

    // Cleanup on unmount
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

    const codingStatus = statusData?.coding ?? { submitted: statusData?.submitted ?? [], not_submitted: statusData?.not_submitted ?? [] };
    const gameStatus = statusData?.game ?? { submitted: [], not_submitted: [] };

    const codingSubmittedCount = codingStatus.submitted.length;
    const codingTotalCount = codingSubmittedCount + codingStatus.not_submitted.length;

    const gameSubmittedCount = gameStatus.submitted.length;
    const gameTotalCount = gameSubmittedCount + gameStatus.not_submitted.length;

    const totalSubmitted = statusData?.submitted?.length ?? (codingSubmittedCount + gameSubmittedCount);
    const totalAssigned = (statusData?.submitted?.length ?? 0) + (statusData?.not_submitted?.length ?? 0) || (codingTotalCount > 0 ? codingTotalCount : gameTotalCount);

    const mainTabItems = [
        {
            key: 'coding',
            label: (
                <span className="flex items-center gap-1.5 font-medium">
                    💻 Homework
                    {codingTotalCount > 0 && (
                        <span className="text-xs text-gray-400 font-normal">
                            ({codingSubmittedCount}/{codingTotalCount})
                        </span>
                    )}
                </span>
            ),
            children: (
                <CategorySubmissionView
                    status={codingStatus}
                    isLoading={isLoading}
                    isOverdue={isOverdue}
                    onViewHistory={handleViewHistory}
                />
            ),
        },
        {
            key: 'game',
            label: (
                <span className="flex items-center gap-1.5 font-medium">
                    🎮 Game
                    {gameTotalCount > 0 && (
                        <span className="text-xs text-gray-400 font-normal">
                            ({gameSubmittedCount}/{gameTotalCount})
                        </span>
                    )}
                </span>
            ),
            children: (
                <CategorySubmissionView
                    status={gameStatus}
                    isLoading={isLoading}
                    isOverdue={isOverdue}
                    onViewHistory={handleViewHistory}
                />
            ),
        },
    ];

    return (
        <>
            <Drawer
                title={
                    <div className="flex flex-col gap-1">
                        <span className="font-semibold text-base leading-tight line-clamp-1">
                            {homework?.title}
                        </span>
                        <div className="flex items-center gap-2 flex-wrap">
                            <Text type="secondary" className="text-xs font-normal">
                                Hạn nộp: {homework ? dayjs(homework.deadline).format('DD/MM/YYYY HH:mm') : ''}
                            </Text>
                            {isOverdue ? (
                                <Tag color="red" icon={<WarningOutlined />} className="text-xs m-0">Quá hạn</Tag>
                            ) : (
                                <Tag color="blue" className="text-xs m-0">Đang mở</Tag>
                            )}
                            {!isLoading && totalAssigned > 0 && (
                                <Text type="secondary" className="text-xs font-normal">
                                    · {totalSubmitted}/{totalAssigned} đã nộp
                                </Text>
                            )}
                        </div>
                    </div>
                }
                extra={
                    <Button
                        type="primary"
                        icon={<SyncOutlined spin={syncMutation.isPending} />}
                        loading={syncMutation.isPending}
                        onClick={handleSync}
                        size="small"
                        className="bg-indigo-600 hover:bg-indigo-700"
                    >
                        Đồng bộ Quiz
                    </Button>
                }
                placement="right"
                width={screens.md ? drawerWidth : '100%'}
                onClose={onClose}
                open={!!homework}
                styles={{ body: { padding: '8px 16px', position: 'relative' } }}
            >
                {/* Resize handle – kéo cạnh trái để thay đổi chiều rộng */}
                {screens.md && (
                    <div
                        onMouseDown={handleResizeMouseDown}
                        title="Kéo để thay đổi kích thước"
                        style={{
                            position: 'absolute',
                            left: 0, top: 0, bottom: 0,
                            width: '6px',
                            cursor: 'col-resize',
                            zIndex: 10,
                            background: 'transparent',
                            transition: 'background 0.15s',
                        }}
                        onMouseEnter={e => (e.currentTarget.style.background = 'rgba(99,102,241,0.25)')}
                        onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                    />
                )}

                {isLoading && !statusData ? (
                    <div className="flex justify-center items-center h-40">
                        <Spin size="large" />
                    </div>
                ) : (
                    <Tabs defaultActiveKey="coding" items={mainTabItems} size="middle" />
                )}
            </Drawer>

            <SubmissionHistoryModal
                homeworkId={homework?.id ?? null}
                user={historyUser}
                open={!!historyUser}
                onClose={() => setHistoryUser(null)}
            />
        </>
    );
};
