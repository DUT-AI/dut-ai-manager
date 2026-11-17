import React, { useState } from 'react';
import { Row, Col, DatePicker, Select, Button, Drawer, Badge, Space } from 'antd';
import { FilterOutlined, ClearOutlined, CalendarOutlined, TagOutlined, UserOutlined } from '@ant-design/icons';
import type dayjs from 'dayjs';
import { useUserOptions } from '@/features/users';

const { Option } = Select;

interface PermissionFilterBarProps {
    filterDate: dayjs.Dayjs | null;
    filterCategory: string | undefined;
    filterUserId: number | undefined;
    onDateChange: (date: dayjs.Dayjs | null) => void;
    onCategoryChange: (category: string | undefined) => void;
    onUserChange: (userId: number | undefined) => void;
    onReset: () => void;
    isMobile?: boolean;
}

export const PermissionFilterBar: React.FC<PermissionFilterBarProps> = ({
    filterDate,
    filterCategory,
    filterUserId,
    onDateChange,
    onCategoryChange,
    onUserChange,
    onReset,
    isMobile = false,
}) => {
    const { data: users = [] } = useUserOptions();
    const [isDrawerOpen, setIsDrawerOpen] = useState(false);

    // Đếm số lượng bộ lọc đang active
    const activeFilterCount =
        (filterDate !== null ? 1 : 0) +
        (filterCategory !== undefined ? 1 : 0) +
        (filterUserId !== undefined ? 1 : 0);

    const handleClearAll = () => {
        onReset();
    };

    // Giao diện trên Mobile: Nút phễu lọc đặt kế nút Tạo Đơn mới (hoặc bấm mở Drawer)
    if (isMobile) {
        return (
            <>
                <div className="flex items-center gap-2">
                    <Badge count={activeFilterCount} offset={[-3, 3]} color="#6366f1">
                        <Button
                            icon={<FilterOutlined className={activeFilterCount > 0 ? "text-indigo-600 font-bold" : "text-gray-500"} />}
                            onClick={() => setIsDrawerOpen(true)}
                            className={`h-10 px-3.5 rounded-xl font-medium flex items-center justify-center gap-1.5 shadow-xs ${
                                activeFilterCount > 0
                                    ? 'border-indigo-400 bg-indigo-50/60 text-indigo-700'
                                    : 'border-gray-200 bg-white text-gray-700'
                            }`}
                        >
                            <span>Lọc</span>
                            {activeFilterCount > 0 && <span className="text-xs font-semibold">({activeFilterCount})</span>}
                        </Button>
                    </Badge>

                    {activeFilterCount > 0 && (
                        <Button
                            type="text"
                            danger
                            size="small"
                            icon={<ClearOutlined />}
                            onClick={handleClearAll}
                            className="text-xs px-2 h-8"
                        >
                            Đặt lại
                        </Button>
                    )}
                </div>

                {/* Drawer trượt từ dưới lên khi bấm vào nút phễu lọc */}
                <Drawer
                    title={
                        <Space>
                            <FilterOutlined className="text-indigo-600" />
                            <span>Bộ lọc Đơn xin phép</span>
                            {activeFilterCount > 0 && (
                                <Badge count={activeFilterCount} color="#6366f1" />
                            )}
                        </Space>
                    }
                    placement="bottom"
                    height="auto"
                    open={isDrawerOpen}
                    onClose={() => setIsDrawerOpen(false)}
                    styles={{
                        body: { paddingBottom: 24 },
                    }}
                    extra={
                        activeFilterCount > 0 && (
                            <Button type="link" danger size="small" onClick={handleClearAll}>
                                Xóa tất cả
                            </Button>
                        )
                    }
                >
                    <div className="flex flex-col gap-4 py-2">
                        {/* Lọc theo tháng năm */}
                        <div className="flex flex-col gap-1.5">
                            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-1.5">
                                <CalendarOutlined className="text-indigo-500" /> Tháng / Năm
                            </span>
                            <DatePicker
                                picker="month"
                                className="w-full h-10 rounded-lg"
                                placeholder="Tất cả thời gian"
                                format="MM/YYYY"
                                value={filterDate}
                                onChange={onDateChange}
                            />
                        </div>

                        {/* Loại đơn xin phép */}
                        <div className="flex flex-col gap-1.5">
                            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-1.5">
                                <TagOutlined className="text-indigo-500" /> Loại đơn xin phép
                            </span>
                            <Select
                                className="w-full h-10 rounded-lg"
                                placeholder="Tất cả loại đơn"
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
                        </div>

                        {/* Lọc theo thành viên */}
                        <div className="flex flex-col gap-1.5">
                            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-1.5">
                                <UserOutlined className="text-indigo-500" /> Thành viên
                            </span>
                            <Select
                                showSearch
                                className="w-full h-10 rounded-lg"
                                placeholder="Tất cả thành viên"
                                allowClear
                                value={filterUserId}
                                optionFilterProp="label"
                                onChange={onUserChange}
                                options={users.map((u) => ({
                                    label: u.name,
                                    value: u.id,
                                }))}
                            />
                        </div>

                        {/* Nút bấm áp dụng */}
                        <Button
                            type="primary"
                            block
                            className="mt-4 bg-indigo-600 hover:bg-indigo-700 h-10 rounded-lg font-medium"
                            onClick={() => setIsDrawerOpen(false)}
                        >
                            Áp dụng bộ lọc {activeFilterCount > 0 ? `(${activeFilterCount})` : ''}
                        </Button>
                    </div>
                </Drawer>
            </>
        );
    }

    // Giao diện trên Desktop: Giữ nguyên bố cục lưới ngang đầy đủ
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
