import React from 'react';
import { Typography, Tag } from 'antd';
import dayjs from 'dayjs';
import type { Homework } from '@/types/homework.types';

const { Text } = Typography;

interface DeadlineTextProps {
    date: string;
    record: Homework;
    showOverdueTag?: boolean;
}

export const DeadlineText: React.FC<DeadlineTextProps> = ({ date, record, showOverdueTag = true }) => {
    const isSubmitted = (record.submission_count ?? 0) > 0;
    const isOverdue = dayjs().isAfter(dayjs(date));
    const isDanger = isOverdue && !isSubmitted;

    return (
        <div className="flex items-center gap-2">
            <Text 
                type={isDanger ? 'danger' : 'secondary'} 
                className={isDanger ? 'font-bold' : ''}
            >
                {dayjs(date).format('DD/MM/YYYY HH:mm')}
            </Text>
            {isDanger && showOverdueTag && (
                <Tag color="red" className="m-0 text-[10px] scale-90 origin-left">
                    Quá hạn
                </Tag>
            )}
        </div>
    );
};
