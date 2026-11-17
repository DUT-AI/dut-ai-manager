import { useState, useMemo } from 'react';
import { Form, Select, DatePicker, Button, Space, Table, Typography, Tag, Row, Col, Card, Statistic, Drawer, Modal, Badge, message } from 'antd';
import { 
  SearchOutlined, 
  ImportOutlined, 
  ExportOutlined, 
  WalletOutlined, 
  CheckCircleOutlined, 
  ClockCircleOutlined, 
  FilterOutlined, 
  RightOutlined, 
  ReloadOutlined 
} from '@ant-design/icons';
import dayjs, { Dayjs } from 'dayjs';
import { useMatrixReport, useBillingSummary } from '@/features/billing/hooks/useBilling';
import { useExpenses } from '@/features/expense/hooks/useExpense';
import { useUserOptions } from '@/features/users';
import type { UserOptionDto } from '@/features/users/types/user.types';
import { useTeams } from '@/features/teams';
import { InvoiceItemType } from '@/features/billing/types/billing.types';
import { ExpenseStatus } from '@/features/expense/types/expense.types';

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
  const [isSummaryModalOpen, setIsSummaryModalOpen] = useState(false);
  const [isFilterDrawerOpen, setIsFilterDrawerOpen] = useState(false);

  const [queryParams, setQueryParams] = useState<{
    start_month: number;
    start_year: number;
    end_month: number;
    end_year: number;
    user_ids?: number[];
    team_id?: number;
    fund_code?: string;
  } | null>(null);

  const { data: users = [] } = useUserOptions();
  const { data: teams = [] } = useTeams();
  const { data: invoices = [], isFetching } = useMatrixReport(queryParams!, !!queryParams);

  // General Summary Data (Incoming & Outgoing)
  const { data: incomingSummary } = useBillingSummary({
    team_id: queryParams?.team_id,
    fund_code: queryParams?.fund_code,
  });
  const { data: allOutgoingInvoices = [] } = useExpenses({
    team_id: queryParams?.team_id,
    fund_code: queryParams?.fund_code,
  });

  // Hóa đơn nhập vào (Thu)
  const incomingTotal = incomingSummary?.total_amount ?? 0;
  const incomingPaid = incomingSummary?.paid_amount ?? 0;
  const incomingUnpaid = incomingSummary?.unpaid_amount ?? 0;

  // Hóa đơn xuất ra (Chi)
  const outgoingTotal = useMemo(() => (allOutgoingInvoices ?? []).reduce((acc, curr) => acc + (curr.amount ?? 0), 0), [allOutgoingInvoices]);
  const outgoingPaid = useMemo(() => (allOutgoingInvoices ?? []).filter(exp => exp.status === ExpenseStatus.PAID).reduce((acc, curr) => acc + (curr.amount ?? 0), 0), [allOutgoingInvoices]);
  const outgoingUnpaid = useMemo(() => (allOutgoingInvoices ?? []).filter(exp => exp.status === ExpenseStatus.UNPAID).reduce((acc, curr) => acc + (curr.amount ?? 0), 0), [allOutgoingInvoices]);

  // Số dư đối ứng (Thu - Chi)
  const balanceTotal = incomingTotal - outgoingTotal;
  const balancePaid = incomingPaid - outgoingPaid;

  const activeFilterCount = useMemo(() => {
    if (!queryParams) return 0;
    let count = 1;
    if (queryParams.fund_code) count++;
    if (queryParams.team_id) count++;
    if (queryParams.user_ids?.length) count++;
    return count;
  }, [queryParams]);

  const selectedTeamId = Form.useWatch('team_id', form);

  const filteredUsers = useMemo(() => {
    if (!selectedTeamId) return users;
    const team = (teams ?? []).find(t => t.id === selectedTeamId);
    if (!team) return users;
    const memberIds = team.members.map(m => m.user_id);
    return users.filter(u => memberIds.includes(u.id));
  }, [users, teams, selectedTeamId]);

  interface MatrixInvoiceItem {
    id: number;
    reference_code: string;
    status: string;
    amount: number;
    items: string[];
  }

  interface FilterFormValues {
    dateRange?: [Dayjs, Dayjs];
    startDate?: Dayjs;
    endDate?: Dayjs;
    user_ids?: number[];
    team_id?: number;
    fund_code?: string;
  }

  const openFilterDrawer = () => {
    const currentRange = form.getFieldValue('dateRange');
    if (currentRange && currentRange.length === 2) {
      form.setFieldsValue({
        startDate: currentRange[0],
        endDate: currentRange[1],
      });
    }
    setIsFilterDrawerOpen(true);
  };

  const onFinish = (values: FilterFormValues) => {
    let start: Dayjs | undefined;
    let end: Dayjs | undefined;

    if (values.dateRange && values.dateRange.length === 2) {
      [start, end] = values.dateRange;
    } else if (values.startDate && values.endDate) {
      start = values.startDate;
      end = values.endDate;
      if (start.isAfter(end)) {
        [start, end] = [end, start];
      }
    }

    if (!start || !end) {
      message.warning('Vui lòng chọn kỳ hóa đơn');
      return;
    }

    form.setFieldsValue({
      dateRange: [start, end],
      startDate: start,
      endDate: end,
    });

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
      team_id: values.team_id || undefined,
      fund_code: values.fund_code || undefined,
    });
    setIsFilterDrawerOpen(false);
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
        render: (invoicesData: MatrixInvoiceItem[]) => {
          if (!invoicesData || invoicesData.length === 0) return <Text type="secondary">-</Text>;

          return (
            <div className="flex flex-col gap-2 min-w-37.5">
              {invoicesData.map(inv => {
                const uniqueTypes = Array.from(new Set(inv.items)) as string[];
                const isPaid = inv.status === 'PAID';

                return (
                  <div key={inv.id} className={`p-2 rounded-md border shadow-xs ${isPaid ? 'bg-emerald-50/40 border-emerald-200' : 'bg-rose-50/40 border-rose-200'}`}>
                    <div className="flex justify-between items-center mb-1">
                      <Text className="text-[10px] text-gray-500 font-mono">#{inv.reference_code}</Text>
                      <span className={`text-[10px] font-semibold flex items-center gap-1 ${isPaid ? 'text-emerald-600' : 'text-amber-600'}`}>
                        {isPaid ? <CheckCircleOutlined className="text-[9px]" /> : <ClockCircleOutlined className="text-[9px]" />}
                        {isPaid ? 'Đã TT' : 'Chưa TT'}
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

    const scopedInvoices = queryParams.fund_code
      ? invoices.filter(inv => inv.fund_code === queryParams.fund_code)
      : invoices;

    // Map of userId -> monthKey -> invoices
    const userMatrix: Record<number, Record<string, MatrixInvoiceItem[]>> = {};

    // Track which users actually have invoices to display them
    const activeUserIds = new Set<number>();

    scopedInvoices.forEach(invoice => {
      const dDate = dayjs(invoice.billing_period);
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
        reference_code: invoice.reference_code ?? '',
        status: invoice.status,
        amount: invoice.amount ?? invoice.total_amount ?? 0,
        items: invoice.items.map(i => i.item_type)
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
      const rowData: Record<string, unknown> = {
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
      render: (user: UserOptionDto) => (
        <div className="flex flex-col">
          <Text strong>{user?.name}</Text>
          <Text type="secondary" className="text-xs">{user?.email}</Text>
        </div>
      )
    },
    ...monthColumns
  ];

  const renderStatsContent = () => (
    <div className="w-full flex flex-col gap-4">
      {/* Nhóm 1: Hóa đơn nhập vào (Thu) */}
      <div>
        <div className="text-xs font-bold text-emerald-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
          <ImportOutlined /> Hóa đơn nhập vào (Thu vào Quỹ & Phạt)
        </div>
        <Row gutter={[12, 12]}>
          <Col xs={24} sm={8}>
            <Card size="small" className="shadow-xs border-emerald-100 bg-emerald-50/20">
              <Statistic
                title="Tổng tiền nhập vào"
                value={incomingTotal}
                formatter={(val) => `${Number(val).toLocaleString()} VNĐ`}
                styles={{ content: { color: '#047857', fontSize: '18px', fontWeight: 600 } }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card size="small" className="shadow-xs border-emerald-100 bg-emerald-50/40">
              <Statistic
                title="Đã thu vào (Đã thanh toán)"
                value={incomingPaid}
                formatter={(val) => `${Number(val).toLocaleString()} VNĐ`}
                styles={{ content: { color: '#059669', fontSize: '18px', fontWeight: 600 } }}
                prefix={<CheckCircleOutlined className="text-emerald-500 mr-1.5" />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card size="small" className="shadow-xs border-emerald-100 bg-amber-50/30">
              <Statistic
                title="Còn nợ nhập vào (Chưa thu)"
                value={incomingUnpaid}
                formatter={(val) => `${Number(val).toLocaleString()} VNĐ`}
                styles={{ content: { color: '#d97706', fontSize: '18px', fontWeight: 600 } }}
                prefix={<ClockCircleOutlined className="text-amber-500 mr-1.5" />}
              />
            </Card>
          </Col>
        </Row>
      </div>

      {/* Nhóm 2: Hóa đơn xuất ra (Chi) */}
      <div>
        <div className="text-xs font-bold text-rose-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
          <ExportOutlined /> Hóa đơn xuất ra (Chi phí hệ thống)
        </div>
        <Row gutter={[12, 12]}>
          <Col xs={24} sm={8}>
            <Card size="small" className="shadow-xs border-rose-100 bg-rose-50/20">
              <Statistic
                title="Tổng tiền xuất ra"
                value={outgoingTotal}
                formatter={(val) => `${Number(val).toLocaleString()} VNĐ`}
                styles={{ content: { color: '#be123c', fontSize: '18px', fontWeight: 600 } }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card size="small" className="shadow-xs border-rose-100 bg-rose-50/40">
              <Statistic
                title="Đã chi xuất ra (Đã trả)"
                value={outgoingPaid}
                formatter={(val) => `${Number(val).toLocaleString()} VNĐ`}
                styles={{ content: { color: '#e11d48', fontSize: '18px', fontWeight: 600 } }}
                prefix={<CheckCircleOutlined className="text-rose-500 mr-1.5" />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card size="small" className="shadow-xs border-rose-100 bg-amber-50/30">
              <Statistic
                title="Còn nợ xuất ra (Chưa chi)"
                value={outgoingUnpaid}
                formatter={(val) => `${Number(val).toLocaleString()} VNĐ`}
                styles={{ content: { color: '#d97706', fontSize: '18px', fontWeight: 600 } }}
                prefix={<ClockCircleOutlined className="text-amber-500 mr-1.5" />}
              />
            </Card>
          </Col>
        </Row>
      </div>

      {/* Nhóm 3: Số dư đối ứng (Thu - Chi) */}
      <div>
        <div className="text-xs font-bold text-indigo-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
          <WalletOutlined /> Số dư đối ứng (Thu - Chi)
        </div>
        <Row gutter={[12, 12]}>
          <Col xs={24} sm={12}>
            <Card size="small" className="shadow-xs border-indigo-100 bg-indigo-50/20">
              <Statistic
                title="Tổng số dư (Tổng Thu - Tổng Chi)"
                value={balanceTotal}
                formatter={(val) => `${Number(val).toLocaleString()} VNĐ`}
                styles={{ content: { color: balanceTotal >= 0 ? '#4338ca' : '#dc2626', fontSize: '18px', fontWeight: 700 } }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12}>
            <Card size="small" className="shadow-xs border-indigo-100 bg-indigo-50/40">
              <Statistic
                title="Số dư thực tế (Đã thu - Đã chi)"
                value={balancePaid}
                formatter={(val) => `${Number(val).toLocaleString()} VNĐ`}
                styles={{ content: { color: balancePaid >= 0 ? '#4f46e5' : '#dc2626', fontSize: '18px', fontWeight: 700 } }}
              />
            </Card>
          </Col>
        </Row>
      </div>
    </div>
  );

  return (
    <div className="flex flex-col gap-4">
      {/* KPI Stats - Desktop (Nguyên bản như cũ, full chiều rộng) */}
      <div className="hidden md:block">
        <div className="bg-white p-4 rounded-xl border border-gray-100">
          {renderStatsContent()}
        </div>
      </div>

      {/* Quick Summary Card - Mobile (Tone trắng xanh sáng) */}
      <div
        onClick={() => setIsSummaryModalOpen(true)}
        className="md:hidden bg-white border border-gray-100 p-3.5 rounded-xl shadow-xs cursor-pointer active:scale-[0.99] transition-all flex items-center justify-between"
      >
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
            <WalletOutlined className="text-base" />
          </div>
          <div>
            <div className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider">Số dư thực tế đối ứng</div>
            <div className={`text-base font-bold tracking-tight ${balancePaid >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
              {balancePaid >= 0 ? '+' : ''}{balancePaid.toLocaleString()} VNĐ
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1 text-xs text-indigo-600 font-medium bg-indigo-50 border border-indigo-100 px-2.5 py-1 rounded-lg">
          <span>Chi tiết</span>
          <RightOutlined className="text-[10px]" />
        </div>
      </div>

      {/* Filters Bar - Desktop */}
      <div className="hidden md:block bg-white p-4 rounded-xl border border-gray-100">
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          className="flex flex-wrap items-end gap-3"
        >
          <Form.Item
            name="fund_code"
            label="Quỹ / Tổ chức"
            className="mb-0 min-w-45 flex-1"
          >
            <Select placeholder="Tất cả quỹ" allowClear>
              <Option value="DUT_AI">DUT AI (Chính)</Option>
              <Option value="DUT_MAKER">DUT Maker (Chia sẻ)</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="team_id"
            label="Đội nhóm"
            className="mb-0 min-w-45 flex-1"
          >
            <Select placeholder="Tất cả nhóm" allowClear>
              {(teams ?? []).map(t => (
                <Option key={t.id} value={t.id}>{t.team_name}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="user_ids"
            label="Thành viên"
            className="mb-0 min-w-55 flex-1"
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
            label="Kỳ hóa đơn (Khoảng thời gian)"
            rules={[{ required: true, message: 'Vui lòng chọn kỳ hóa đơn' }]}
            className="mb-0 min-w-60 flex-1"
          >
            <RangePicker picker="month" format="MM/YYYY" className="w-full" placeholder={['Tháng bắt đầu', 'Tháng kết thúc']} />
          </Form.Item>

          <div className="flex items-end mb-0">
            <Button type="primary" htmlType="submit" icon={<SearchOutlined />} className="h-8">
              Xem báo cáo
            </Button>
          </div>
        </Form>
      </div>

      {/* Quick Filter Trigger Bar - Mobile */}
      <div className="md:hidden flex items-center justify-between bg-white p-3 rounded-xl border border-gray-100 shadow-xs">
        <div className="flex items-center gap-2 text-xs text-gray-600 truncate mr-2">
          <FilterOutlined className="text-indigo-600" />
          <span className="truncate">
            {queryParams ? `Kỳ: ${queryParams.start_month}/${queryParams.start_year} - ${queryParams.end_month}/${queryParams.end_year}` : 'Chưa chọn kỳ báo cáo'}
          </span>
        </div>
        <Badge count={activeFilterCount} size="small" offset={[-2, 2]}>
          <Button 
            type="primary" 
            ghost
            size="small"
            icon={<FilterOutlined />} 
            onClick={openFilterDrawer}
            className="border-indigo-600 text-indigo-600"
          >
            Bộ lọc
          </Button>
        </Badge>
      </div>

      {/* Mobile Drawer Filter */}
      <Drawer
        title={
          <div className="flex items-center gap-2 font-semibold text-slate-800">
            <FilterOutlined /> Bộ lọc báo cáo tổng hợp
          </div>
        }
        placement="bottom"
        height="auto"
        open={isFilterDrawerOpen}
        onClose={() => setIsFilterDrawerOpen(false)}
        styles={{ body: { paddingBottom: 24 } }}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          className="flex flex-col gap-3"
        >
          <Form.Item
            name="fund_code"
            label="Quỹ / Tổ chức"
            className="mb-1"
          >
            <Select placeholder="Tất cả quỹ" allowClear>
              <Option value="DUT_AI">DUT AI (Chính)</Option>
              <Option value="DUT_MAKER">DUT Maker (Chia sẻ)</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="team_id"
            label="Đội nhóm"
            className="mb-1"
          >
            <Select placeholder="Tất cả nhóm" allowClear>
              {(teams ?? []).map(t => (
                <Option key={t.id} value={t.id}>{t.team_name}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="user_ids"
            label="Thành viên"
            className="mb-1"
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

          <div>
            <div className="text-xs font-semibold text-gray-700 mb-1.5 uppercase tracking-wider">
              Kỳ hóa đơn (Khoảng thời gian) <span className="text-rose-500">*</span>
            </div>
            <div className="grid grid-cols-2 gap-2 mb-3">
              <Form.Item
                name="startDate"
                className="mb-0"
                rules={[{ required: true, message: 'Chọn tháng bắt đầu' }]}
              >
                <DatePicker
                  picker="month"
                  format="MM/YYYY"
                  placeholder="Từ tháng"
                  className="w-full"
                />
              </Form.Item>
              <Form.Item
                name="endDate"
                className="mb-0"
                rules={[{ required: true, message: 'Chọn tháng kết thúc' }]}
              >
                <DatePicker
                  picker="month"
                  format="MM/YYYY"
                  placeholder="Đến tháng"
                  className="w-full"
                />
              </Form.Item>
            </div>
          </div>

          <div className="flex gap-2 pt-2 border-t border-gray-100">
            <Button
              className="flex-1"
              icon={<ReloadOutlined />}
              onClick={() => {
                form.resetFields();
                setQueryParams(null);
                setIsFilterDrawerOpen(false);
              }}
            >
              Đặt lại
            </Button>
            <Button
              type="primary"
              htmlType="submit"
              icon={<SearchOutlined />}
              className="flex-1"
            >
              Xem báo cáo
            </Button>
          </div>
        </Form>
      </Drawer>

      {/* Mobile Stats Modal */}
      <Modal
        title={
          <div className="flex items-center gap-2 font-semibold text-slate-800">
            <WalletOutlined /> Chi tiết thống kê tài chính
          </div>
        }
        open={isSummaryModalOpen}
        onCancel={() => setIsSummaryModalOpen(false)}
        footer={[
          <Button key="close" type="primary" onClick={() => setIsSummaryModalOpen(false)}>
            Đóng
          </Button>
        ]}
        width={700}
      >
        <div className="py-2">
          {renderStatsContent()}
        </div>
      </Modal>

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
