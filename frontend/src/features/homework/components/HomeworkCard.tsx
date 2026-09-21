import React from 'react';
import { Button } from 'antd';
import {
    BookOutlined,
    CheckCircleOutlined,
    ClockCircleOutlined,
    ExclamationCircleOutlined,
    ExportOutlined,
    EyeOutlined,
    CalendarOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/vi';
import type { Homework } from '../types/homework.types';

dayjs.extend(relativeTime);
dayjs.locale('vi');

export interface HomeworkCardProps {
    homework: Homework & {
        isSubmitted?: boolean;
        isOverdue?: boolean;
    };
    onViewDetail?: (homework: Homework) => void;
}

export const HomeworkCard: React.FC<HomeworkCardProps> = ({ homework, onViewDetail }) => {
    const isSubmitted = homework.isSubmitted ?? (homework.submission_count ?? 0) > 0;
    const isOverdue = homework.isOverdue ?? (!isSubmitted && dayjs().isAfter(dayjs(homework.deadline)));

    const deadlineObj = dayjs(homework.deadline);
    const formattedDeadline = deadlineObj.format('DD/MM/YYYY HH:mm');
    const relativeDeadline = deadlineObj.fromNow();

    return (
        <div
            className={`group relative overflow-hidden rounded-2xl border transition-all duration-300 bg-white shadow-2xs hover:shadow-md hover:-translate-y-0.5 p-4 sm:p-5 ${isOverdue
                ? 'border-rose-200/80 bg-gradient-to-r from-rose-50/40 via-white to-white'
                : isSubmitted
                    ? 'border-emerald-200/80 bg-gradient-to-r from-emerald-50/30 via-white to-white'
                    : 'border-slate-200/80 bg-gradient-to-r from-slate-50/40 via-white to-white'
                }`}
        >
            {/* Left Accent Bar */}
            <div
                className={`w-1.5 h-full absolute left-0 top-0 rounded-l-2xl ${isOverdue
                    ? 'bg-gradient-to-b from-rose-500 to-red-600'
                    : isSubmitted
                        ? 'bg-gradient-to-b from-emerald-400 to-teal-600'
                        : 'bg-gradient-to-b from-indigo-500 to-violet-600'
                    }`}
            />

            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pl-2 sm:pl-3">
                {/* Main Content Area */}
                <div className="flex items-start gap-3.5 flex-1 min-w-0">
                    {/* Status Icon Container */}
                    <div
                        className={`w-11 h-11 sm:w-12 sm:h-12 rounded-xl flex items-center justify-center shrink-0 shadow-2xs transition-transform duration-300 group-hover:scale-105 ${isOverdue
                            ? 'bg-rose-100/80 text-rose-600 ring-1 ring-rose-200/50'
                            : isSubmitted
                                ? 'bg-emerald-100/80 text-emerald-600 ring-1 ring-emerald-200/50'
                                : 'bg-indigo-100/80 text-indigo-600 ring-1 ring-indigo-200/50'
                            }`}
                    >
                        {isOverdue ? (
                            <ExclamationCircleOutlined className="text-xl" />
                        ) : isSubmitted ? (
                            <CheckCircleOutlined className="text-xl" />
                        ) : (
                            <BookOutlined className="text-xl" />
                        )}
                    </div>

                    {/* Title & Metadata */}
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                            {isSubmitted ? (
                                <span className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-700 border border-emerald-200/60 shadow-2xs">
                                    <CheckCircleOutlined className="text-xs" />
                                    Đã nộp bài
                                </span>
                            ) : isOverdue ? (
                                <span className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-700 border border-rose-200/60 shadow-2xs">
                                    <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>
                                    Quá hạn nộp
                                </span>
                            ) : (
                                <span className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-200/60 shadow-2xs">
                                    <ClockCircleOutlined className="text-xs" />
                                    Chưa nộp
                                </span>
                            )}
                        </div>

                        <h3
                            onClick={() => onViewDetail && onViewDetail(homework)}
                            className="text-base sm:text-lg font-bold text-gray-900 group-hover:text-indigo-600 transition-colors line-clamp-1 mb-0 cursor-pointer"
                        >
                            {homework.title}
                        </h3>

                        {/* Deadline Chips */}
                        <div className="flex flex-wrap items-center gap-2 mt-2.5">
                            <span
                                className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-lg border ${isOverdue
                                    ? 'bg-rose-50/80 text-rose-700 border-rose-200/60'
                                    : 'bg-gray-100/80 text-gray-700 border-gray-200/60'
                                    }`}
                            >
                                <CalendarOutlined className="text-gray-400" />
                                Hạn nộp: <strong className="font-semibold">{formattedDeadline}</strong>
                            </span>

                            <span
                                className={`inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg border font-medium ${isOverdue
                                    ? 'bg-rose-50 text-rose-600 border-rose-200/50 font-semibold'
                                    : isSubmitted
                                        ? 'bg-emerald-50 text-emerald-700 border-emerald-100'
                                        : 'bg-amber-50/80 text-amber-700 border-amber-200/50'
                                    }`}
                            >
                                <ClockCircleOutlined className="text-xs" />
                                {isOverdue ? `Hết hạn ${relativeDeadline}` : `Còn ${relativeDeadline}`}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Right Action Buttons */}
                <div className="flex items-center gap-2.5 w-full md:w-auto justify-end pt-3 md:pt-0 border-t md:border-t-0 border-gray-100 shrink-0">
                    {homework.link && (
                        <Button
                            type="primary"
                            href={homework.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{ color: '#ffffff' }}
                            className={`h-9 sm:h-10 px-4 sm:px-5 rounded-xl font-semibold text-xs sm:text-sm !text-white border-0 shadow-sm hover:shadow-md hover:scale-[1.02] active:scale-[0.98] transition-all duration-200 flex items-center justify-center gap-2 ${
                                isSubmitted
                                    ? '!bg-emerald-600 hover:!bg-emerald-500'
                                    : '!bg-indigo-600 hover:!bg-indigo-500'
                            }`}
                        >
                            <span style={{ color: '#ffffff' }} className="!text-white font-semibold">
                                {isSubmitted ? 'Xem bài nộp trên Quiz' : 'Làm bài ngay'}
                            </span>
                            <ExportOutlined style={{ color: '#ffffff' }} className="text-xs !text-white" />
                        </Button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default HomeworkCard;
