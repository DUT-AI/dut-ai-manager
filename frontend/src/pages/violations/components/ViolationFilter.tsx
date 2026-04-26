import { Select, DatePicker, Button } from 'antd';
import { UserOutlined, CalendarOutlined } from '@ant-design/icons';
import type { Dayjs } from 'dayjs';
import type { UserResponse } from '@/types/user.types';

const { Option } = Select;

interface ViolationFilterProps {
    filterUserId: number | undefined;
    setFilterUserId: (id: number | undefined) => void;
    filterDate: Dayjs | null;
    setFilterDate: (date: Dayjs | null) => void;
    users: UserResponse[];
}

const ViolationFilter = ({
    filterUserId,
    setFilterUserId,
    filterDate,
    setFilterDate,
    users
}: ViolationFilterProps) => {
    return (
        <div className="flex flex-wrap items-center gap-4 mb-6 mx-3 md:mx-0 bg-gray-50/50 p-4 rounded-lg border border-gray-100">
            <div className="flex flex-col gap-1.5 min-w-[200px] w-full md:w-auto">
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-1.5">
                    <UserOutlined className="text-red-400" /> Lọc theo thành viên
                </span>
                <Select
                    allowClear
                    showSearch
                    placeholder="Tất cả thành viên"
                    className="w-full"
                    value={filterUserId}
                    onChange={setFilterUserId}
                    optionFilterProp="children"
                    filterOption={(input, option) =>
                        String(option?.children ?? '').toLowerCase().includes(input.toLowerCase())
                    }
                >
                    {users.map(u => (
                        <Option key={u.id} value={u.id}>{u.name}</Option>
                    ))}
                </Select>
            </div>
            <div className="flex flex-col gap-1.5 min-w-[160px] w-full md:w-auto">
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-1.5">
                    <CalendarOutlined className="text-red-400" /> Lọc theo tháng/năm
                </span>
                <DatePicker 
                    picker="month" 
                    className="w-full"
                    placeholder="Tất cả thời gian"
                    value={filterDate}
                    onChange={setFilterDate}
                    format="MM/YYYY"
                />
            </div>
            {(filterUserId || filterDate) && (
                <Button 
                    type="link" 
                    danger 
                    className="md:self-end h-10 px-2"
                    onClick={() => {
                        setFilterUserId(undefined);
                        setFilterDate(null);
                    }}
                >
                    Xóa bộ lọc
                </Button>
            )}
        </div>
    );
};

export default ViolationFilter;
