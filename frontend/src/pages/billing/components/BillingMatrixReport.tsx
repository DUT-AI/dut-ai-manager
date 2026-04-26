import { useState, useMemo } from 'react';
import { Form, Select, DatePicker, Button, Space, Table, Typography, Tag } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import dayjs, { Dayjs } from 'dayjs';
import { useMatrixReport } from '@/hooks/useBilling';
import { useUsers, useTeams } from '@/hooks';
import { InvoiceItemType } from '@/types/billing.types';

const { RangePicker } = DatePicker;
const { Option } = Select;
const { Text } = Typography;

const ITEM_TYPE_COLORS: Record<string, string> = {
  [InvoiceItemType.VIOLATION]: 'red',
  [InvoiceItemType.FUND]: 'green',
  [InvoiceItemType.DINING]: 'orange',
  [InvoiceItemType.OTHER]: 'default',
};

const ITEM_TYPE_LABELS: Record<string, string> = {
  [InvoiceItemType.VIOLATION]: 'Vi phạm',
  [InvoiceItemType.FUND]: 'Tiền quỹ',
  [InvoiceItemType.DINING]: 'Ăn uống',
  [InvoiceItemType.OTHER]: 'Khác',
};

const BillingMatrixReport = () => {
  const [form] = Form.useForm();
  
  const [queryParams, setQueryParams] = useState<{
    start_month: number;
    start_year: number;
    end_month: number;
    end_year: number;
    user_ids?: number[];
  } | null>(null);

  const { data: users = [] } = useUsers();
  const { data: teams = [] } = useTeams();
  const { data: invoices = [], isFetching } = useMatrixReport(queryParams!, !!queryParams);

  const selectedTeamId = Form.useWatch('team_id', form);
  
  const filteredUsers = useMemo(() => {
    if (!selectedTeamId) return users;
    // Assuming team relation exists or we just rely on users if they have team_id
    // But if we can't filter users by team easily here, we just show all users for now
    return users.filter(u => u.team_id === selectedTeamId || !selectedTeamId);
  }, [users, selectedTeamId]);

  const onFinish = (values: any) => {
    if (!values.dateRange || values.dateRange.length !== 2) return;
    
    const [start, end] = values.dateRange as [Dayjs, Dayjs];
    
    let user_ids = values.user_ids || [];
    
    // If a team is selected but no specific users, we might want to pass all user_ids of that team
    if (values.team_id && (!values.user_ids || values.user_ids.length === 0)) {
      user_ids = filteredUsers.map(u => u.id);
    }

    setQueryParams({
      start_month: start.month() + 1,
      start_year: start.year(),
      end_month: end.month() + 1,
      end_year: end.year(),
      user_ids: user_ids.length > 0 ? user_ids : undefined,
    });
  };

  // Generate dynamic columns based on selected date range
  const monthColumns = useMemo(() => {
    if (!queryParams) return [];
    
    const cols = [];
    let current = dayjs().year(queryParams.start_year).month(queryParams.start_month - 1);
    const end = dayjs().year(queryParams.end_year).month(queryParams.end_month - 1);
    
    while (current.isBefore(end) || current.isSame(end, 'month')) {
      const monthStr = current.format('MM/YYYY');
      const monthKey = current.format('YYYY-MM'); // used for data indexing
      cols.push({
        title: monthStr,
        dataIndex: monthKey,
        key: monthKey,
        render: (invoicesData: any[]) => {
          if (!invoicesData || invoicesData.length === 0) return <Text type="secondary">-</Text>;
          
          return (
            <div className="flex flex-col gap-2 min-w-[150px]">
              {invoicesData.map(inv => {
                const uniqueTypes = Array.from(new Set(inv.items)) as string[];
                const isPaid = inv.status === 'PAID';
                
                return (
                  <div key={inv.id} className={`p-2 rounded-md border shadow-sm ${isPaid ? 'bg-green-50/50 border-green-200' : 'bg-red-50/50 border-red-200'}`}>
                    <div className="flex justify-between items-center mb-1">
                      <Text className="text-[10px] text-gray-500 font-mono">#{inv.reference_code}</Text>
                      <span className={`text-[10px] font-bold ${isPaid ? 'text-green-600' : 'text-red-500'}`}>
                        {isPaid ? '✅ Đã TT' : '⏳ Chưa TT'}
                      </span>
                    </div>
                    <div className="text-[11px] font-semibold mb-1.5 text-gray-700">
                      {new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(inv.amount)}
                    </div>
                    <Space size={[4, 4]} wrap>
                      {uniqueTypes.map(type => (
                        <Tag key={type} color={ITEM_TYPE_COLORS[type] || 'default'} className="m-0 text-[10px] border-none leading-none py-0.5">
                          {ITEM_TYPE_LABELS[type] || type}
                        </Tag>
                      ))}
                    </Space>
                  </div>
                );
              })}
            </div>
          );
        }
      });
      current = current.add(1, 'month');
    }
    return cols;
  }, [queryParams]);

  // Process data into matrix format
  const tableData = useMemo(() => {
    if (!invoices.length || !queryParams) return [];
    
    // Map of userId -> monthKey -> invoices
    const userMatrix: Record<number, Record<string, any[]>> = {};
    
    // Track which users actually have invoices to display them
    const activeUserIds = new Set<number>();

    invoices.forEach(invoice => {
      const dDate = dayjs(invoice.created_at);
      const monthKey = dDate.format('YYYY-MM');
      const uid = invoice.user_id;
      
      if (!userMatrix[uid]) {
        userMatrix[uid] = {};
      }
      if (!userMatrix[uid][monthKey]) {
        userMatrix[uid][monthKey] = [];
      }
      
      activeUserIds.add(uid);
      
      userMatrix[uid][monthKey].push({
        id: invoice.id,
        reference_code: invoice.reference_code,
        status: invoice.status,
        amount: invoice.amount,
        items: invoice.items.map((i: any) => i.item_type)
      });
    });

    // We can either show ALL users from filteredUsers, or ONLY users with invoices.
    // Usually a report shows users with data, or all selected users. We will show all selected if explicitly selected, else users with data.
    let displayUsers = users;
    if (queryParams.user_ids && queryParams.user_ids.length > 0) {
      displayUsers = users.filter(u => queryParams.user_ids!.includes(u.id));
    } else {
      displayUsers = users.filter(u => activeUserIds.has(u.id));
    }

    return displayUsers.map(user => {
      const rowData: any = {
        key: user.id,
        user: user,
      };
      
      const userMonths = userMatrix[user.id] || {};
      Object.keys(userMonths).forEach(mKey => {
        rowData[mKey] = userMonths[mKey];
      });
      
      return rowData;
    });

  }, [invoices, users, queryParams]);

  const columns = [
    {
      title: 'Thành viên',
      dataIndex: 'user',
      key: 'user',
      fixed: 'left' as const,
      width: 200,
      render: (user: any) => (
        <div className="flex flex-col">
          <Text strong>{user?.name}</Text>
          <Text type="secondary" className="text-xs">{user?.email}</Text>
        </div>
      )
    },
    ...monthColumns
  ];

  return (
    <div className="flex flex-col gap-4">
      <div className="bg-white p-4 rounded-xl border border-gray-100">
        <Form 
          form={form} 
          layout="vertical" 
          onFinish={onFinish}
          className="flex flex-wrap gap-x-4"
        >
          <Form.Item 
            name="team_id" 
            label="Đội nhóm" 
            className="mb-0 min-w-[200px] flex-1"
          >
            <Select placeholder="Tất cả nhóm" allowClear>
              {teams.map(t => (
                <Option key={t.id} value={t.id}>{t.name}</Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item 
            name="user_ids" 
            label="Thành viên" 
            className="mb-0 min-w-[250px] flex-1"
          >
            <Select 
              mode="multiple" 
              placeholder="Tất cả thành viên" 
              allowClear 
              maxTagCount="responsive"
            >
              {filteredUsers.map(u => (
                <Option key={u.id} value={u.id}>{u.name}</Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item 
            name="dateRange" 
            label="Khoảng thời gian" 
            rules={[{ required: true, message: 'Vui lòng chọn thời gian' }]}
            className="mb-0 min-w-[250px]"
          >
            <RangePicker picker="month" format="MM/YYYY" className="w-full" />
          </Form.Item>
          
          <div className="flex items-end mb-0">
            <Button type="primary" htmlType="submit" icon={<SearchOutlined />} className="h-[32px]">
              Xem báo cáo
            </Button>
          </div>
        </Form>
      </div>

      <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
        {queryParams ? (
          <Table 
            columns={columns} 
            dataSource={tableData} 
            loading={isFetching}
            scroll={{ x: 'max-content' }}
            pagination={false}
            rowClassName="hover:bg-slate-50 transition-colors"
            locale={{ emptyText: 'Không có dữ liệu trong khoảng thời gian này' }}
          />
        ) : (
          <div className="p-12 text-center text-gray-400">
            <Text type="secondary">Vui lòng chọn bộ lọc và nhấn "Xem báo cáo"</Text>
          </div>
        )}
      </div>
    </div>
  );
};

export default BillingMatrixReport;
