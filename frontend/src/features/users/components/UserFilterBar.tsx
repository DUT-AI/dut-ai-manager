import { FilterOutlined, SearchOutlined, DeleteOutlined } from '@ant-design/icons';
import { Button, Col, Input, Row, Select } from 'antd';
import { UserStatus } from '../types/user.types';
import type { RoleResponse } from '@/features/rbac';

const { Option } = Select;

interface UserFilterBarProps {
    searchText: string;
    onSearchTextChange: (value: string) => void;
    filterRole?: string;
    onFilterRoleChange: (value?: string) => void;
    filterStatus?: string;
    onFilterStatusChange: (value?: string) => void;
    roles: RoleResponse[];
    onResetFilters: () => void;
}

export const UserFilterBar = ({
    searchText,
    onSearchTextChange,
    filterRole,
    onFilterRoleChange,
    filterStatus,
    onFilterStatusChange,
    roles,
    onResetFilters,
}: UserFilterBarProps) => {
    const isFiltering = Boolean(searchText || filterRole || filterStatus);

    return (
        <div className="px-3 md:px-0 mb-4">
            <Row gutter={[12, 12]}>
                <Col xs={24} md={8}>
                    <Input
                        placeholder="Tìm kiếm tên, email, SĐT..."
                        prefix={<SearchOutlined className="text-gray-400" />}
                        value={searchText}
                        onChange={(e) => onSearchTextChange(e.target.value)}
                        allowClear
                        className="w-full"
                    />
                </Col>
                <Col xs={12} md={5}>
                    <Select
                        placeholder="Vai trò"
                        value={filterRole}
                        onChange={onFilterRoleChange}
                        allowClear
                        className="w-full"
                        suffixIcon={<FilterOutlined />}
                    >
                        {roles.map((role) => (
                            <Option key={role.id} value={role.name}>
                                {role.name.toUpperCase()}
                            </Option>
                        ))}
                    </Select>
                </Col>
                <Col xs={12} md={5}>
                    <Select
                        placeholder="Trạng thái"
                        value={filterStatus}
                        onChange={onFilterStatusChange}
                        allowClear
                        className="w-full"
                        suffixIcon={<FilterOutlined />}
                    >
                        <Option value={UserStatus.ACTIVE}>Active</Option>
                        <Option value={UserStatus.INACTIVE}>Inactive</Option>
                    </Select>
                </Col>
                {isFiltering && (
                    <Col xs={24} md={6}>
                        <Button
                            onClick={onResetFilters}
                            block
                            icon={<DeleteOutlined className="text-xs" />}
                        >
                            Xóa lọc
                        </Button>
                    </Col>
                )}
            </Row>
        </div>
    );
};
