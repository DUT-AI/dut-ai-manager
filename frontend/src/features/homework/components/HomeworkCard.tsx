import React from 'react';
import { Button, Tag, Tooltip, message } from 'antd';
import {
    BookOutlined,
    CheckCircleOutlined,
    ClockCircleOutlined,
    ExclamationCircleOutlined,
    ExportOutlined,
    CalendarOutlined,
    CodeOutlined,
    TrophyOutlined,
    EyeOutlined,
    SyncOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/vi';
import type { Homework } from '../types/homework.types';
import { useSyncHomeworkFromQuiz } from '../hooks/useHomeworks';

dayjs.extend(relativeTime);
dayjs.locale('vi');

export interface HomeworkCardProps {
    homework: Homework;
    onViewDetail?: (homework: Homework) => void;
}

export const HomeworkCard: React.FC<HomeworkCardProps> = ({ homework, onViewDetail }) => {
    // Pure presentation driven 100% by Backend SSOT 2-dimensional evaluation
    const completionStatus = homework.completion_status ?? 'NOT_STARTED';
    const timelinessStatus = homework.timeliness_status ?? 'UPCOMING';

    const isCompleted = completionStatus === 'COMPLETED';
    const isInProgress = completionStatus === 'IN_PROGRESS';
    const isCompletedLate = isCompleted && timelinessStatus === 'LATE';
    const isOverdue = timelinessStatus === 'OVERDUE';

    const deadlineObj = homework.deadline ? dayjs(homework.deadline) : null;
    const formattedDeadline = deadlineObj ? deadlineObj.format('DD/MM/YYYY HH:mm') : 'Chưa thiết lập';
    const relativeDeadline = deadlineObj ? deadlineObj.fromNow() : '';
    const syncedAtLabel = homework.last_synced_at
        ? `Đồng bộ ${dayjs(homework.last_synced_at).fromNow()}`
        : null;

    const { mutate: syncHomework, isPending: isSyncing } = useSyncHomeworkFromQuiz();

    const handleSync = (e: React.MouseEvent) => {
        e.stopPropagation();
        if (!homework.id) return;
        syncHomework(homework.id, {
            onSuccess: (data) => {
                message.success(data?.message || 'Đồng bộ kết quả từ Quiz thành công!');
            },
            onError: () => {
                message.error('Không thể đồng bộ từ Quiz. Vui lòng thử lại sau.');
            },
        });
    };

    const cardBorderClass = isCompleted
        ? isCompletedLate
            ? 'border-teal-200/80 bg-gradient-to-r from-teal-50/30 via-white to-white'
            : 'border-emerald-200/80 bg-gradient-to-r from-emerald-50/30 via-white to-white'
        : isInProgress
            ? 'border-amber-200/80 bg-gradient-to-r from-amber-50/40 via-white to-white'
            : isOverdue
                ? 'border-rose-200/80 bg-gradient-to-r from-rose-50/40 via-white to-white'
                : 'border-slate-200/80 bg-gradient-to-r from-slate-50/40 via-white to-white';

    const accentBarClass = isCompleted
        ? isCompletedLate
            ? 'bg-gradient-to-b from-teal-400 to-amber-500'
            : 'bg-gradient-to-b from-emerald-400 to-teal-600'
        : isInProgress
            ? 'bg-gradient-to-b from-amber-400 to-orange-500'
            : isOverdue
                ? 'bg-gradient-to-b from-rose-500 to-red-600'
                : 'bg-gradient-to-b from-indigo-500 to-violet-600';

    const iconBoxClass = isCompleted
        ? isCompletedLate
            ? 'bg-teal-100/80 text-teal-700 ring-1 ring-teal-200/60'
            : 'bg-emerald-100/80 text-emerald-600 ring-1 ring-emerald-200/50'
        : isInProgress
            ? 'bg-amber-100/80 text-amber-600 ring-1 ring-amber-200/50'
            : isOverdue
                ? 'bg-rose-100/80 text-rose-600 ring-1 ring-rose-200/50'
                : 'bg-indigo-100/80 text-indigo-600 ring-1 ring-indigo-200/50';

    const renderPrimaryBadge = () => {
        if (isCompleted && !isCompletedLate) {
            return (
                <span className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-700 border border-emerald-200/60 shadow-2xs">
                    <CheckCircleOutlined className="text-xs" />
                    Đã hoàn thành • Đúng hạn
                </span>
            );
        }
        if (isCompletedLate) {
            return (
                <span className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full text-xs font-semibold bg-teal-100 text-teal-800 border border-amber-300/80 shadow-2xs">
                    <CheckCircleOutlined className="text-xs text-teal-700" />
                    Đã hoàn thành • Nộp trễ
                </span>
            );
        }
        if (isInProgress) {
            return (
                <span className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-300 shadow-2xs">
                    <ClockCircleOutlined className="text-xs text-amber-600" />
                    {isOverdue ? 'Quá hạn (Làm dở)' : 'Đang làm dở'}
                </span>
            );
        }
        if (isOverdue) {
            return (
                <span className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-700 border border-rose-200/60 shadow-2xs">
                    <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
                    Quá hạn nộp
                </span>
            );
        }
        return (
            <span className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200/60 shadow-2xs">
                <ClockCircleOutlined className="text-xs" />
                Chưa nộp bài
            </span>
        );
    };

    const renderCodingTag = () => {
        if (!homework.has_coding) return null;
        const done = homework.total_coding_completed ?? 0;
        const req = homework.total_coding_required ?? 0;
        const isCodingDone = homework.coding_submitted === true;
        const isCodingPartial = !isCodingDone && done > 0 && req > 1;

        const color = isCodingDone
            ? homework.coding_is_late
                ? 'cyan'
                : 'success'
            : isCodingPartial
                ? 'warning'
                : isOverdue
                    ? 'error'
                    : 'default';

        const label = isCodingDone
            ? req > 1
                ? `Đã xong (${done}/${req})`
                : 'Đã xong'
            : isCodingPartial
                ? `${done}/${req} bài con`
                : req > 1
                    ? `0/${req} bài con`
                    : 'Chưa nộp';

        return (
            <Tag icon={<CodeOutlined />} color={color} className="rounded-md font-medium text-xs m-0">
                Coding: {label}
            </Tag>
        );
    };

    const renderGameTag = () => {
        if (!homework.has_game) return null;
        const isGameDone = homework.game_submitted === true;
        const color = isGameDone
            ? homework.game_is_late
                ? 'cyan'
                : 'success'
            : isOverdue
                ? 'error'
                : 'default';

        return (
            <Tag icon={<TrophyOutlined />} color={color} className="rounded-md font-medium text-xs m-0">
                Game: {isGameDone ? 'Đã xong' : 'Chưa chơi'}
            </Tag>
        );
    };

    return (
        <div
            className={`group relative overflow-hidden rounded-2xl border transition-all duration-300 bg-white shadow-2xs hover:shadow-md hover:-translate-y-0.5 p-4 sm:p-5 ${cardBorderClass}`}
        >
            {/* Left Accent Bar */}
            <div className={`w-1.5 h-full absolute left-0 top-0 rounded-l-2xl ${accentBarClass}`} />

            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pl-2 sm:pl-3">
                {/* Main Content Area */}
                <div className="flex items-start gap-3.5 flex-1 min-w-0">
                    {/* Status Icon Container */}
                    <div
                        className={`w-11 h-11 sm:w-12 sm:h-12 rounded-xl flex items-center justify-center shrink-0 shadow-2xs transition-transform duration-300 group-hover:scale-105 ${iconBoxClass}`}
                    >
                        {isCompleted ? (
                            <CheckCircleOutlined className="text-xl" />
                        ) : isInProgress ? (
                            <ClockCircleOutlined className="text-xl" />
                        ) : isOverdue ? (
                            <ExclamationCircleOutlined className="text-xl" />
                        ) : (
                            <BookOutlined className="text-xl" />
                        )}
                    </div>

                    {/* Title & Metadata */}
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                            {renderPrimaryBadge()}
                            {renderCodingTag()}
                            {renderGameTag()}
                        </div>

                        <h3
                            onClick={() => onViewDetail && onViewDetail(homework)}
                            className="text-base sm:text-lg font-bold text-gray-900 group-hover:text-indigo-600 transition-colors line-clamp-1 mb-0 cursor-pointer"
                        >
                            {homework.title}
                        </h3>

                        {/* Uncompleted Items Helper Note */}
                        {!isCompleted && homework.uncompleted_items && homework.uncompleted_items.length > 0 && isInProgress && (
                            <div className="text-xs text-amber-700 bg-amber-50/80 px-2.5 py-1 rounded-md border border-amber-200/70 mt-1.5 inline-block">
                                Còn thiếu: {homework.uncompleted_items.join(', ')}. Vui lòng hoàn thành để đạt 100% bài tập.
                            </div>
                        )}

                        {/* Deadline & Sync Chips */}
                        <div className="flex flex-wrap items-center gap-2 mt-2.5">
                            <span
                                className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-lg border ${
                                    isOverdue
                                        ? 'bg-rose-50/80 text-rose-700 border-rose-200/60'
                                        : 'bg-gray-100/80 text-gray-700 border-gray-200/60'
                                }`}
                            >
                                <CalendarOutlined className="text-gray-400" />
                                Hạn nộp: <strong className="font-semibold">{formattedDeadline}</strong>
                            </span>

                            {deadlineObj && (
                                <span
                                    className={`inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg border font-medium ${
                                        isOverdue
                                            ? 'bg-rose-50 text-rose-600 border-rose-200/50 font-semibold'
                                            : isCompleted
                                                ? isCompletedLate
                                                    ? 'bg-teal-50 text-teal-700 border-teal-200/60'
                                                    : 'bg-emerald-50 text-emerald-700 border-emerald-100'
                                                : 'bg-amber-50/80 text-amber-700 border-amber-200/50'
                                    }`}
                                >
                                    <ClockCircleOutlined className="text-xs" />
                                    {isCompleted
                                        ? homework.completed_at
                                            ? `Hoàn thành lúc ${dayjs(homework.completed_at).format('DD/MM HH:mm')}`
                                            : 'Đã hoàn thành'
                                        : isOverdue
                                            ? `Hết hạn ${relativeDeadline}`
                                            : `Còn ${relativeDeadline}`}
                                </span>
                            )}

                            {syncedAtLabel && (
                                <Tooltip
                                    title={`Đồng bộ gần nhất từ Quiz: ${dayjs(homework.last_synced_at).format('DD/MM/YYYY HH:mm')}`}
                                >
                                    <span className="inline-flex items-center gap-1 text-[11px] text-gray-400 px-1.5">
                                        <SyncOutlined className="text-[10px]" />
                                        {syncedAtLabel}
                                    </span>
                                </Tooltip>
                            )}
                        </div>
                    </div>
                </div>

                {/* Right Action Buttons */}
                <div className="flex items-center gap-2.5 w-full md:w-auto justify-end pt-3 md:pt-0 border-t md:border-t-0 border-gray-100 shrink-0">
                    {!isCompleted && (
                        <Tooltip title="Đồng bộ kết quả mới nhất từ hệ thống Quiz cho bài tập này">
                            <Button
                                icon={<SyncOutlined spin={isSyncing} />}
                                loading={isSyncing}
                                onClick={handleSync}
                                className="h-9 sm:h-10 px-3 sm:px-3.5 rounded-xl font-medium text-xs sm:text-sm border-blue-200 text-blue-600 hover:border-blue-500 hover:text-blue-700 hover:bg-blue-50/50 transition-colors shadow-2xs"
                            >
                                Đồng bộ
                            </Button>
                        </Tooltip>
                    )}
                    <Button
                        icon={<EyeOutlined />}
                        onClick={() => onViewDetail && onViewDetail(homework)}
                        className="h-9 sm:h-10 px-3.5 sm:px-4 rounded-xl font-medium text-xs sm:text-sm border-gray-200 hover:border-indigo-500 hover:text-indigo-600 transition-colors shadow-2xs"
                    >
                        Chi tiết
                    </Button>
                    {homework.link && (
                        <Button
                            type="primary"
                            href={homework.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{ color: '#ffffff' }}
                            className={`h-9 sm:h-10 px-4 sm:px-5 rounded-xl font-semibold text-xs sm:text-sm !text-white border-0 shadow-sm hover:shadow-md hover:scale-[1.02] active:scale-[0.98] transition-all duration-200 flex items-center justify-center gap-2 ${
                                isCompleted
                                    ? '!bg-emerald-600 hover:!bg-emerald-500'
                                    : isInProgress
                                        ? '!bg-amber-600 hover:!bg-amber-500'
                                        : '!bg-indigo-600 hover:!bg-indigo-500'
                            }`}
                        >
                            <span style={{ color: '#ffffff' }} className="!text-white font-semibold">
                                {isCompleted ? 'Xem trên Quiz' : isInProgress ? 'Làm tiếp bài tập' : 'Làm bài ngay'}
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
