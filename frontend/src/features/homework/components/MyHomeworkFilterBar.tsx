import React from 'react';
import { Input, Tabs } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import type { HomeworkFilterStatus, MyHomeworksStats } from '../types/homework.types';

export interface MyHomeworkFilterBarProps {
    activeTab: HomeworkFilterStatus;
    onTabChange: (status: HomeworkFilterStatus) => void;
    searchInput: string;
    onSearchChange: (value: string) => void;
    stats: MyHomeworksStats;
}

export const MyHomeworkFilterBar: React.FC<MyHomeworkFilterBarProps> = ({
    activeTab,
    onTabChange,
    searchInput,
    onSearchChange,
    stats,
}) => {
    return (
        <div className="flex flex-col md:flex-row justify-between items-stretch md:items-center gap-4">
            <Tabs
                activeKey={activeTab}
                onChange={(key) => onTabChange(key as HomeworkFilterStatus)}
                className="flex-1 border-b-0"
                items={[
                    { key: 'all', label: `Tất cả (${stats.total ?? 0})` },
                    { key: 'uncompleted', label: `Chưa hoàn thành (${stats.uncompleted ?? 0})` },
                    { key: 'completed', label: `Đã hoàn thành (${stats.completed ?? 0})` },
                    { key: 'overdue', label: `Quá hạn (${stats.overdue ?? 0})` },
                ]}
            />
            <Input
                prefix={<SearchOutlined className="text-gray-400" />}
                placeholder="Tìm theo tên bài tập..."
                value={searchInput}
                onChange={(e) => onSearchChange(e.target.value)}
                allowClear
                className="w-full md:w-64 h-10 rounded-xl shadow-2xs"
            />
        </div>
    );
};

export default MyHomeworkFilterBar;
