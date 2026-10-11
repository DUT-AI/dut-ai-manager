import React from 'react';
import { DatePicker, Typography } from 'antd';
import { FilterOutlined } from '@ant-design/icons';
import type { Dayjs } from 'dayjs';

const { Text } = Typography;

interface MonthFilterBarProps {
    selectedDate: Dayjs | null;
    onChange: (date: Dayjs | null) => void;
}

export const MonthFilterBar: React.FC<MonthFilterBarProps> = ({ selectedDate, onChange }) => (
    <div className="flex flex-wrap items-center gap-3 mb-4 p-3 bg-gray-50 rounded-lg">
        <FilterOutlined className="text-gray-500" />
        <Text type="secondary">Lọc theo tháng:</Text>
        <DatePicker
            picker="month"
            value={selectedDate}
            onChange={(date) => onChange(date)}
            format="MM/YYYY"
            allowClear={true}
            placeholder="Tất cả thời gian"
            className="w-40"
        />
        <Text type="secondary" className="ml-auto text-xs w-full sm:w-auto mt-2 sm:mt-0">
            {selectedDate
                ? `Hiển thị dữ liệu tháng ${selectedDate.format('MM/YYYY')}`
                : 'Hiển thị tất cả thời gian'}
        </Text>
    </div>
);

export default MonthFilterBar;
