import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Drawer, Tabs, List, Avatar, Badge, Empty, Spin, Tag, Grid, Typography } from 'antd';
import { UserOutlined, CheckCircleOutlined, CloseCircleOutlined, WarningOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { useHomeworkSubmissionStatus } from '@/features/homework/hooks/useHomeworks';
import type { Homework, UserSubmissionInfo } from '@/features/homework/types/homework.types';

const { Text } = Typography;
const { useBreakpoint } = Grid;

const MIN_WIDTH = 320;
const MAX_WIDTH = 900;
const DEFAULT_WIDTH = 460;

interface HomeworkDetailDrawerProps {
    homework: Homework | null;
    onClose: () => void;
}

const UserListItem: React.FC<{ user: UserSubmissionInfo }> = ({ user }) => (
    <List.Item className="!px-0 !py-2">
        <div className="flex items-center gap-3 w-full">
            <Avatar src={user.avatar_url || undefined} icon={<UserOutlined />} size={36} className="flex-shrink-0" />
            <Text className="font-medium text-sm flex-1 truncate">
                {user.name || `User #${user.user_id}`}
            </Text>
            {user.is_late && (
                <Tag color="error" className="m-0 font-medium text-xs">
                    Trễ
                </Tag>
            )}
        </div>
    </List.Item>
);

const UserList: React.FC<{ data: UserSubmissionInfo[]; isLoading: boolean; emptyText: string }> = ({
    data, isLoading, emptyText,
}) => (
    <div className="mt-2">
        {isLoading ? (
            <div className="flex justify-center py-8"><Spin /></div>
        ) : data.length === 0 ? (
            <Empty description={emptyText} imageStyle={{ height: 60 }} />
        ) : (
            <List dataSource={data} renderItem={(user) => <UserListItem user={user} />} split={false} />
        )}
    </div>
);

const CategorySubmissionView: React.FC<{
    status?: { submitted: UserSubmissionInfo[]; not_submitted: UserSubmissionInfo[] };
    isLoading: boolean;
    isOverdue: boolean;
}> = ({ status, isLoading, isOverdue }) => {
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

    const { data: statusData, isLoading } = useHomeworkSubmissionStatus(homework?.id ?? null);

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
            children: <CategorySubmissionView status={codingStatus} isLoading={isLoading} isOverdue={isOverdue} />,
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
            children: <CategorySubmissionView status={gameStatus} isLoading={isLoading} isOverdue={isOverdue} />,
        },
    ];

    return (
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
    );
};
