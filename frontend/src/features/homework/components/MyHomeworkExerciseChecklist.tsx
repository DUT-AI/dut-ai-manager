import React from 'react';
import { Tag, Typography } from 'antd';
import {
    CheckCircleOutlined,
    ClockCircleOutlined,
    CloseCircleOutlined,
    CodeOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import type { MyHomeworkExerciseStatus } from '../types/homework.types';

const { Text } = Typography;

export interface MyHomeworkExerciseChecklistProps {
    exercises: MyHomeworkExerciseStatus[];
}

export const MyHomeworkExerciseChecklist: React.FC<MyHomeworkExerciseChecklistProps> = ({
    exercises,
}) => {
    if (!exercises || exercises.length === 0) {
        return null;
    }

    const passedCount = exercises.filter((ex) => ex.is_passed).length;

    return (
        <div className="space-y-3 mb-5">
            <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-2">
                    <CodeOutlined className="text-indigo-600" />
                    <Text strong className="text-sm text-gray-800 dark:text-gray-100">
                        Danh sách bài tập lập trình bắt buộc ({passedCount}/{exercises.length} đạt)
                    </Text>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {exercises.map((ex) => {
                    const isPassed = ex.is_passed === true;
                    const isSubmitted = ex.is_submitted === true;
                    const isLate = ex.is_late === true;

                    return (
                        <div
                            key={ex.exercise_id}
                            className={`p-3.5 rounded-xl border transition-all ${
                                isPassed
                                    ? isLate
                                        ? 'bg-teal-50/40 border-teal-200/80'
                                        : 'bg-emerald-50/40 border-emerald-200/80'
                                    : isSubmitted
                                        ? 'bg-amber-50/40 border-amber-200/80'
                                        : 'bg-gray-50/60 border-gray-200/80'
                            }`}
                        >
                            <div className="flex items-start justify-between gap-2">
                                <div className="min-w-0 flex-1">
                                    <div className="font-semibold text-sm text-gray-900 truncate">
                                        {ex.order_index > 0 ? `${ex.order_index}. ` : ''}
                                        {ex.title}
                                    </div>
                                    <div className="text-xs text-gray-500 mt-1 flex flex-wrap gap-x-3 gap-y-0.5">
                                        <span>Số lần nộp: {ex.attempt_count ?? 0}</span>
                                        {ex.best_score !== null && ex.best_score !== undefined && (
                                            <span>Điểm cao nhất: {ex.best_score}</span>
                                        )}
                                        {ex.first_passed_at && (
                                            <span>
                                                Đạt lúc: {dayjs(ex.first_passed_at).format('DD/MM/YYYY HH:mm')}
                                            </span>
                                        )}
                                    </div>
                                </div>

                                <div className="shrink-0">
                                    {isPassed ? (
                                        <Tag
                                            color={isLate ? 'cyan' : 'success'}
                                            icon={<CheckCircleOutlined />}
                                            className="m-0 rounded-md text-xs font-semibold"
                                        >
                                            {isLate ? 'Đạt (Trễ hạn)' : 'Đạt đúng hạn'}
                                        </Tag>
                                    ) : isSubmitted ? (
                                        <Tag
                                            color="warning"
                                            icon={<CloseCircleOutlined />}
                                            className="m-0 rounded-md text-xs font-semibold"
                                        >
                                            Chưa đạt
                                        </Tag>
                                    ) : (
                                        <Tag
                                            color={isLate ? 'error' : 'default'}
                                            icon={<ClockCircleOutlined />}
                                            className="m-0 rounded-md text-xs font-semibold"
                                        >
                                            {isLate ? 'Chưa nộp (Quá hạn)' : 'Chưa nộp'}
                                        </Tag>
                                    )}
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default MyHomeworkExerciseChecklist;
