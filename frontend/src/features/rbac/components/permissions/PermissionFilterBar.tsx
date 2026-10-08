import React from 'react';
import { Row, Col, DatePicker, Select, Button } from 'antd';
import type dayjs from 'dayjs';

const { Option } = Select;

interface UserOption {
    id: number;
    name: string;
}

interface PermissionFilterBarProps {
    filterDate: dayjs.Dayjs | null;
    filterCategory: string | undefined;
    filterUserId: number | undefined;
    users: UserOption[];
    onDateChange: (date: dayjs.Dayjs | null) => void;
    onCategoryChange: (category: string | undefined) => void;
    onUserChange: (userId: number | undefined) => void;
    onReset: () => void;
}

export const PermissionFilterBar: React.FC<PermissionFilterBarProps> = ({
    filterDate,
    filterCategory,
    filterUserId,
    users,
    onDateChange,
    onCategoryChange,
    onUserChange,
    onReset,
}) => {
    return (
        <div className="bg-gray-50/50 p-4 rounded-xl mb-6 border border-gray-100">
            <Row gutter={[16, 16]} align="middle">
                <Col xs={24} sm={12} md={6}>
                    <DatePicker
                        picker="month"
                        className="w-full h-10 rounded-lg"
                        placeholder="Lọc theo tháng năm"
                        format="MM/YYYY"
                        value={filterDate}
                        onChange={onDateChange}
                    />
                </Col>
                <Col xs={24} sm={12} md={6}>
                    <Select
                        className="w-full h-10 rounded-lg custom-select"
                        placeholder="Loại đơn xin phép"
                        allowClear
                        value={filterCategory}
                        onChange={onCategoryChange}
                    >
                        <Option value="ABSENCE">Vắng sinh hoạt</Option>
                        <Option value="LATE">Đi trễ sinh hoạt</Option>
                        <Option value="POSTPONE">Tạm hoãn bài tập</Option>
                        <Option value="CHANGE_MEETING">Đổi buổi sinh hoạt</Option>
                        <Option value="OTHER">Khác</Option>
                    </Select>
                </Col>
                <Col xs={24} sm={12} md={6}>
                    <Select
                        showSearch
                        className="w-full h-10 rounded-lg"
                        placeholder="Lọc theo User"
                        allowClear
                        value={filterUserId}
                        optionFilterProp="label"
                        onChange={onUserChange}
                        options={users.map((u) => ({
                            label: u.name,
                            value: u.id,
                        }))}
                    />
                </Col>
                <Col xs={24} sm={12} md={6}>
                    <Button
                        className="w-full h-10 rounded-lg"
                        ghost
                        type="primary"
                        onClick={onReset}
                    >
                        Đặt lại bộ lọc
                    </Button>
                </Col>
            </Row>
        </div>
    );
};
