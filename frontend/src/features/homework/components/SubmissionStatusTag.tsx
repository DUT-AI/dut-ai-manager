import React from 'react';
import { Tag } from 'antd';
import type { Homework } from '@/features/homework/types/homework.types';
import { HomeworkStatus } from '@/features/homework/types/homework.types';
import { useAuth } from '@/features/auth/context/AuthContext';
import { useMySubmission } from '@/features/homework/hooks/useHomeworks';

interface SubmissionStatusTagProps {
    record: Homework;
}

export const SubmissionStatusTag: React.FC<SubmissionStatusTagProps> = ({ record }) => {
    const { user } = useAuth();
    const { data: fetchedSubmission } = useMySubmission(record.id);

    // 1. Check record.submissions first
    const submissionInRecord = record.submissions?.find(
        s => Number(s.owner_id) === Number(user?.id)
    );

    // 2. Use fetchedSubmission if submissionInRecord isn't present
    const mySubmission = submissionInRecord || fetchedSubmission;
    const status = mySubmission?.status;

    let label = 'CHƯA NỘP';
    let color = 'error';

    if (status === HomeworkStatus.SUBMITTED) {
        label = 'ĐÃ NỘP';
        color = 'processing';
    } else if (status === HomeworkStatus.LeaderChecked) {
        label = 'LEADER CHECK';
        color = 'warning';
    } else if (status === HomeworkStatus.FINISHED) {
        label = 'HOÀN THÀNH';
        color = 'success';
    } else {
        label = 'CHƯA NỘP';
        color = 'error';
    }

    return (
        <Tag
            color={color}
            className="m-0 uppercase font-bold text-[10px] md:text-[11px] px-2 md:px-3 py-0.5 rounded-full text-center min-w-[70px] md:min-w-[80px]"
        >
            {label}
        </Tag>
    );
};
