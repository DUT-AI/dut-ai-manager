import React from 'react';
import { Tag } from 'antd';
import type { Homework } from '@/types/homework.types';

import { useAuth } from '@/context/AuthContext';

interface SubmissionStatusTagProps {
    record: Homework;
}

export const SubmissionStatusTag: React.FC<SubmissionStatusTagProps> = ({ record }) => {
    const { user } = useAuth();
    const isSubmitted = (record.submission_count ?? 0) > 0;
    const mySubmission = record.submissions?.find(s => s.owner_id === user?.id);
    const status = mySubmission?.status || (isSubmitted ? 'đã nộp' : 'chưa nộp');

    const statusConfig: Record<string, { color: string }> = {
        'đã nộp': { color: 'blue' },
        'leader đã check': { color: 'warning' },
        'finish': { color: 'success' },
        'chưa nộp': { color: 'error' },
    };

    const config = statusConfig[status] || { color: 'default' };

    return (
        <Tag 
            color={config.color} 
            className="m-0 uppercase font-bold text-[10px] md:text-[11px] px-2 md:px-3 py-0.5 rounded-full text-center min-w-[70px] md:min-w-[80px]"
        >
            {status}
        </Tag>
    );
};
