import React from 'react';
import { Avatar, Tag, Tooltip, Button } from 'antd';
import {
    UserOutlined,
    ClockCircleOutlined,
    CloseCircleOutlined,
    HistoryOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import type { UserSubmissionInfo } from '@/features/homework/types/homework.types';

export interface UserSubmissionCardProps {
    user: UserSubmissionInfo;
    isSubmitted: boolean;
    onViewHistory?: (user: UserSubmissionInfo) => void;
}

export const UserSubmissionCard: React.FC<UserSubmissionCardProps> = ({
    user,
    isSubmitted,
    onViewHistory
}) => {
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
                        className={`absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-white dark:border-zinc-800 ${
                            isSubmitted
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
