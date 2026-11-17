import React from 'react';
import { Progress } from 'antd';
import {
    TrophyOutlined,
    TeamOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined
} from '@ant-design/icons';

export interface HomeworkOverviewStatsProps {
    submissionPercent: number;
    totalSubmitted: number;
    totalAssigned: number;
}

export const HomeworkOverviewStats: React.FC<HomeworkOverviewStatsProps> = ({
    submissionPercent,
    totalSubmitted,
    totalAssigned
}) => {
    return (
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
    );
};
