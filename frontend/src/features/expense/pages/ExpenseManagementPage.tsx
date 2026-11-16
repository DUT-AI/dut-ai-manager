import React, { useState } from 'react';
import {
  Table,
  Card,
  Tag,
  Button,
  Typography,
  Space,
  DatePicker,
  Popconfirm,
  Row,
  Col,
  Statistic,
  Tooltip,
  Select,
  Input,
  Drawer,
  Badge,
  Modal,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  SwapOutlined,
  DollarOutlined,
  SearchOutlined,
  FilterOutlined,
  RightOutlined,
  ExportOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { useUserOptions } from '@/features/users';
import { useTeams } from '@/features/teams';
import {
  useExpenses,
  useExpenseSummary,
  useUpdateExpenseStatus,
  useDeleteExpense,
} from '@/features/expense/hooks/useExpense';
import { ExpenseStatus, type ExpenseInvoice, type ExpenseStatusType } from '@/features/expense/types/expense.types';
import { CreateExpenseModal } from '@/features/expense/components/CreateExpenseModal';
import { UpdateExpenseModal } from '@/features/expense/components/UpdateExpenseModal';
import { useTablePagination } from '@/hooks/useTablePagination';

const { Text } = Typography;

const ExpenseManagementPage: React.FC = () => {
  // Filters: Selected Spender, Team, Fund, Status, Month/Year, Search
  const [filterSearch, setFilterSearch] = useState('');
  const [filterSpender, setFilterSpender] = useState<number | undefined>(undefined);
  const [filterFund, setFilterFund] = useState<string | undefined>(undefined);
  const [filterTeam, setFilterTeam] = useState<number | undefined>(undefined);
  const [selectedStatus, setSelectedStatus] = useState<ExpenseStatusType | undefined>(undefined);
  const [selectedPeriod, setSelectedPeriod] = useState<dayjs.Dayjs | null>(null);

  const selectedMonth = selectedPeriod ? selectedPeriod.month() + 1 : undefined;
  const selectedYear = selectedPeriod ? selectedPeriod.year() : undefined;

  const { data: usersData } = useUserOptions();
  const { data: teamsData } = useTeams();
  const users = usersData || [];
  const teams = teamsData || [];

  // Modals state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isFilterDrawerOpen, setIsFilterDrawerOpen] = useState(false);
  const [isSummaryModalOpen, setIsSummaryModalOpen] = useState(false);
  const [editingExpense, setEditingExpense] = useState<ExpenseInvoice | null>(null);

  const activeFilterCount = [
    filterSpender,
    filterFund,
    filterTeam,
    selectedStatus,
    selectedPeriod,
  ].filter((val) => val !== undefined && val !== null).length;

  // Pagination hook
  const { page, pageSize, resetPage, getPaginationProps } = useTablePagination();

  // Queries & Mutations
  const { data: expensesData, isLoading: isLoadingExpenses } = useExpenses({
    month: selectedMonth,
    year: selectedYear,
    status: selectedStatus,
    spender_id: filterSpender,
    team_id: filterTeam,
    fund_code: filterFund,
    search: filterSearch ? filterSearch.trim() : undefined,
    page,
    pageSize,
  });
  const expenses = expensesData || [];
  const totalCount = (expensesData as any)?.pagination?.total ?? (expenses as any)?.pagination?.total ?? expenses.length;

  const { data: summary, isLoading: isLoadingSummary } = useExpenseSummary({
    month: selectedMonth,
    year: selectedYear,
    spender_id: filterSpender,
    team_id: filterTeam,
    fund_code: filterFund,
  });

  const updateStatusMutation = useUpdateExpenseStatus();
  const deleteExpenseMutation = useDeleteExpense();

  const handleToggleStatus = async (record: ExpenseInvoice) => {
    const nextStatus = record.status === ExpenseStatus.PAID ? ExpenseStatus.UNPAID : ExpenseStatus.PAID;
    await updateStatusMutation.mutateAsync({
      id: record.id,
      status: nextStatus,
    });
  };

  const handleDelete = async (id: string) => {
    await deleteExpenseMutation.mutateAsync(id);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(amount);
  };

  const columns = [
    {
      title: 'Ngày chi',
      dataIndex: 'expense_date',
      key: 'expense_date',
      width: 120,
      render: (dateStr: string) => dayjs(dateStr).format('DD/MM/YYYY'),
    },
    {
      title: 'Số tiền',
      dataIndex: 'amount',
      key: 'amount',
      width: 150,
      render: (amount: number) => (
        <Text strong className="text-blue-600 font-semibold">
          {formatCurrency(amount)}
        </Text>
      ),
    },
    {
      title: 'Nội dung chi',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text: string, record: ExpenseInvoice) => (
        <Tooltip
          placement="topLeft"
          title={
            <div className="space-y-1.5 p-1 max-w-md break-words">
              <div>
                <div className="font-semibold text-xs text-gray-300 mb-0.5">Nội dung chi:</div>
                <div className="text-sm text-white font-medium whitespace-pre-wrap">{text}</div>
              </div>
              {record.note && (
                <div className="pt-1.5 border-t border-gray-600/60">
                  <div className="font-semibold text-xs text-gray-300 mb-0.5">Ghi chú:</div>
                  <div className="text-xs text-gray-200 italic whitespace-pre-wrap">{record.note}</div>
                </div>
              )}
            </div>
          }
        >
          <div className="cursor-pointer max-w-full">
            <div className="font-medium text-gray-800 truncate">{text}</div>
            {record.note && (
              <div className="text-xs text-gray-500 italic truncate">
                Ghi chú: {record.note}
              </div>
            )}
          </div>
        </Tooltip>
      ),
    },
    {
      title: 'Người chi',
      dataIndex: 'spender',
      key: 'spender',
      width: 200,
      render: (_: any, record: ExpenseInvoice) => (
        <div>
          <div className="font-medium">{record.spender?.name || 'N/A'}</div>
          {record.spender?.email && (
            <div className="text-xs text-gray-400">{record.spender.email}</div>
          )}
        </div>
      ),
    },
    {
      title: 'Quỹ',
      key: 'fund_code',
      width: 130,
      render: (_: any, record: ExpenseInvoice) => {
        const isMaker = record.fund_code === 'DUT_MAKER';
        return (
          <Tag color={isMaker ? 'purple' : 'cyan'}>
            {isMaker ? 'DUT Maker' : 'DUT AI'}
          </Tag>
        );
      },
    },
    {
      title: 'Nhóm',
      dataIndex: 'team',
      key: 'team',
      width: 160,
      render: (_: any, record: ExpenseInvoice) => {
        const name = record.team?.team_name;
        if (!name || name === 'DUT AI' || name === 'DUT Maker') {
          return <Text type="secondary">-</Text>;
        }
        return (
          <Tag color="blue" className="font-medium">
            {name}
          </Tag>
        );
      },
    },
    {
      title: 'Tình trạng',
      dataIndex: 'status',
      key: 'status',
      width: 140,
      render: (statusVal: ExpenseStatusType) => {
        if (statusVal === ExpenseStatus.PAID) {
          return (
            <Tag color="success" icon={<CheckCircleOutlined />}>
              Đã trả
            </Tag>
          );
        }
        return (
          <Tag color="warning" icon={<ClockCircleOutlined />}>
            Chưa trả
          </Tag>
        );
      },
    },
    {
      title: 'Thao tác',
      key: 'action',
      width: 180,
      fixed: 'right' as const,
      render: (_: any, record: ExpenseInvoice) => (
        <Space size="small">
          <Tooltip title={record.status === ExpenseStatus.PAID ? 'Đánh dấu chưa trả' : 'Đánh dấu đã trả'}>
            <Button
              type="text"
              icon={<SwapOutlined />}
              onClick={() => handleToggleStatus(record)}
              loading={updateStatusMutation.isPending}
            />
          </Tooltip>
          <Tooltip title="Chỉnh sửa">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => setEditingExpense(record)}
            />
          </Tooltip>
          <Popconfirm
            title="Xóa hóa đơn chi"
            description="Bạn có chắc chắn muốn xóa hóa đơn chi này không?"
            onConfirm={() => handleDelete(record.id)}
            okText="Xóa"
            cancelText="Hủy"
            okButtonProps={{ danger: true }}
          >
            <Tooltip title="Xóa">
              <Button type="text" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      {/* Action Header */}
      <div className="flex justify-between items-center mb-2">
        <Text type="secondary" className="text-xs font-medium">Danh sách & Thống kê các khoản chi tiêu của hệ thống</Text>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          className="bg-indigo-600 border-none font-semibold rounded-lg shadow-md hover:bg-indigo-700"
          onClick={() => setIsCreateModalOpen(true)}
        >
          Tạo hóa đơn xuất ra
        </Button>
      </div>

      {/* KPI Stats Cards - Desktop */}
      <div className="hidden md:block mb-4">
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={8}>
            <Card loading={isLoadingSummary} className="shadow-sm border-gray-100">
              <Statistic
                title="Tổng cộng tiền chi"
                value={summary?.total || 0}
                formatter={(val) => formatCurrency(Number(val))}
                prefix={<DollarOutlined className="text-blue-500 mr-2" />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card loading={isLoadingSummary} className="shadow-sm border-gray-100">
              <Statistic
                title="Đã thanh toán (Đã trả)"
                value={summary?.total_paid || 0}
                formatter={(val) => formatCurrency(Number(val))}
                styles={{ content: { color: '#52c41a' } }}
                prefix={<CheckCircleOutlined className="text-green-500 mr-2" />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card loading={isLoadingSummary} className="shadow-sm border-gray-100">
              <Statistic
                title="Còn nợ (Chưa trả)"
                value={summary?.total_unpaid || 0}
                formatter={(val) => formatCurrency(Number(val))}
                styles={{ content: { color: '#faad14' } }}
                prefix={<ClockCircleOutlined className="text-amber-500 mr-2" />}
              />
            </Card>
          </Col>
        </Row>
      </div>

      {/* Quick Summary Card - Mobile */}
      <div
        onClick={() => setIsSummaryModalOpen(true)}
        className="md:hidden bg-white border border-gray-100 p-3.5 rounded-xl shadow-xs cursor-pointer active:scale-[0.99] transition-all mb-3 flex items-center justify-between"
      >
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-lg bg-rose-50 border border-rose-100 flex items-center justify-center text-rose-600">
            <ExportOutlined className="text-base" />
          </div>
          <div>
            <div className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider">Tổng chi tiêu</div>
            <div className="text-base font-bold text-gray-900 tracking-tight">
              {formatCurrency(Number(summary?.total || 0))}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1 text-xs text-rose-600 font-medium bg-rose-50 border border-rose-100 px-2.5 py-1 rounded-lg">
          <span>Chi tiết</span>
          <RightOutlined className="text-[10px]" />
        </div>
      </div>

      {/* Main Table Card */}
      <Card className="shadow-sm border-gray-100">
        {/* Filters Bar - Desktop */}
        <div className="hidden md:block mb-4">
          <Row gutter={[12, 12]} align="middle" className="bg-gray-50/50 p-4 rounded-xl border border-gray-100">
            <Col xs={24} sm={12} md={8} lg={4}>
              <div className="text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wider">Nội dung chi</div>
              <Input
                placeholder="Tìm nội dung, ghi chú..."
                prefix={<SearchOutlined className="text-gray-400" />}
                allowClear
                value={filterSearch}
                onChange={(e) => {
                  setFilterSearch(e.target.value);
                  resetPage();
                }}
              />
            </Col>

            <Col xs={24} sm={12} md={8} lg={4}>
              <div className="text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wider">Người chi</div>
              <Select
                showSearch
                placeholder="Tất cả người chi"
                style={{ width: '100%' }}
                allowClear
                value={filterSpender}
                onChange={(value) => {
                  setFilterSpender(value);
                  resetPage();
                }}
                optionFilterProp="children"
              >
                {users.map((u) => (
                  <Select.Option key={u.id} value={u.id}>
                    {u.name} ({u.email})
                  </Select.Option>
                ))}
              </Select>
            </Col>

            <Col xs={24} sm={12} md={8} lg={4}>
              <div className="text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wider">Quỹ / Tổ chức</div>
              <Select
                placeholder="Tất cả quỹ"
                style={{ width: '100%' }}
                allowClear
                value={filterFund}
                onChange={(value) => {
                  setFilterFund(value);
                  resetPage();
                }}
              >
                <Select.Option value="DUT_AI">DUT AI (Chính)</Select.Option>
                <Select.Option value="DUT_MAKER">DUT Maker (Chia sẻ)</Select.Option>
              </Select>
            </Col>

            <Col xs={24} sm={12} md={8} lg={4}>
              <div className="text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wider">Nhóm</div>
              <Select
                showSearch
                placeholder="Tất cả nhóm"
                style={{ width: '100%' }}
                allowClear
                value={filterTeam}
                onChange={(value) => {
                  setFilterTeam(value);
                  resetPage();
                }}
                optionFilterProp="children"
              >
                {teams.map((t) => (
                  <Select.Option key={t.id} value={t.id}>
                    {t.team_name}
                  </Select.Option>
                ))}
              </Select>
            </Col>

            <Col xs={24} sm={12} md={8} lg={4}>
              <div className="text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wider">Trạng thái</div>
              <Select
                placeholder="Tất cả trạng thái"
                style={{ width: '100%' }}
                allowClear
                value={selectedStatus}
                onChange={(value) => {
                  setSelectedStatus(value);
                  resetPage();
                }}
              >
                <Select.Option value={ExpenseStatus.UNPAID}>Chưa trả (UNPAID)</Select.Option>
                <Select.Option value={ExpenseStatus.PAID}>Đã trả (PAID)</Select.Option>
              </Select>
            </Col>

            <Col xs={24} sm={12} md={8} lg={4}>
              <div className="text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wider">Kỳ hóa đơn</div>
              <DatePicker
                picker="month"
                format="MM/YYYY"
                placeholder="Tất cả các kỳ"
                style={{ width: '100%' }}
                allowClear
                value={selectedPeriod}
                onChange={(date) => {
                  setSelectedPeriod(date);
                  resetPage();
                }}
              />
            </Col>
          </Row>
        </div>

        {/* Quick Search & Filter Trigger - Mobile */}
        <div className="md:hidden flex items-center gap-2 mb-3">
          <Input
            placeholder="Tìm theo nội dung..."
            prefix={<SearchOutlined className="text-gray-400" />}
            allowClear
            value={filterSearch}
            onChange={(e) => {
              setFilterSearch(e.target.value);
              resetPage();
            }}
            className="flex-1 rounded-lg"
          />
          <Badge count={activeFilterCount} size="small" offset={[-2, 2]}>
            <Button
              icon={<FilterOutlined />}
              onClick={() => setIsFilterDrawerOpen(true)}
              className={`rounded-lg flex items-center gap-1 ${activeFilterCount > 0 ? 'border-rose-500 text-rose-600 bg-rose-50/50' : ''
                }`}
            >
              Lọc
            </Button>
          </Badge>
        </div>

        {/* Mobile Filter Drawer */}
        <Drawer
          title={
            <div className="flex items-center justify-between">
              <span className="font-semibold text-gray-800">Bộ lọc chi tiêu</span>
              {activeFilterCount > 0 && (
                <Button
                  type="link"
                  size="small"
                  onClick={() => {
                    setFilterSpender(undefined);
                    setFilterFund(undefined);
                    setFilterTeam(undefined);
                    setSelectedStatus(undefined);
                    setSelectedPeriod(null);
                    resetPage();
                  }}
                  className="text-xs text-rose-600 p-0"
                >
                  Đặt lại ({activeFilterCount})
                </Button>
              )}
            </div>
          }
          placement="bottom"
          height="auto"
          open={isFilterDrawerOpen}
          onClose={() => setIsFilterDrawerOpen(false)}
          className="rounded-t-2xl"
          footer={
            <div className="flex gap-2 p-1">
              <Button
                block
                onClick={() => {
                  setFilterSpender(undefined);
                  setFilterFund(undefined);
                  setFilterTeam(undefined);
                  setSelectedStatus(undefined);
                  setSelectedPeriod(null);
                  resetPage();
                }}
              >
                Thiết lập lại
              </Button>
              <Button
                type="primary"
                block
                onClick={() => setIsFilterDrawerOpen(false)}
              >
                Áp dụng
              </Button>
            </div>
          }
        >
          <div className="space-y-3.5 py-1">
            <div>
              <div className="text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wider">Quỹ / Tổ chức</div>
              <Select
                placeholder="Tất cả quỹ"
                style={{ width: '100%' }}
                allowClear
                value={filterFund}
                onChange={(value) => {
                  setFilterFund(value);
                  resetPage();
                }}
              >
                <Select.Option value="DUT_AI">DUT AI (Chính)</Select.Option>
                <Select.Option value="DUT_MAKER">DUT Maker (Chia sẻ)</Select.Option>
              </Select>
            </div>

            <div>
              <div className="text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wider">Người chi</div>
              <Select
                showSearch
                placeholder="Tất cả người chi"
                style={{ width: '100%' }}
                allowClear
                value={filterSpender}
                onChange={(value) => {
                  setFilterSpender(value);
                  resetPage();
                }}
                optionFilterProp="children"
              >
                {users.map((u) => (
                  <Select.Option key={u.id} value={u.id}>
                    {u.name} ({u.email})
                  </Select.Option>
                ))}
              </Select>
            </div>

            <div>
              <div className="text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wider">Nhóm</div>
              <Select
                showSearch
                placeholder="Tất cả nhóm"
                style={{ width: '100%' }}
                allowClear
                value={filterTeam}
                onChange={(value) => {
                  setFilterTeam(value);
                  resetPage();
                }}
                optionFilterProp="children"
              >
                {teams.map((t) => (
                  <Select.Option key={t.id} value={t.id}>
                    {t.team_name}
                  </Select.Option>
                ))}
              </Select>
            </div>

            <div>
              <div className="text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wider">Trạng thái</div>
              <Select
                placeholder="Tất cả trạng thái"
                style={{ width: '100%' }}
                allowClear
                value={selectedStatus}
                onChange={(value) => {
                  setSelectedStatus(value);
                  resetPage();
                }}
              >
                <Select.Option value={ExpenseStatus.UNPAID}>Chưa trả (UNPAID)</Select.Option>
                <Select.Option value={ExpenseStatus.PAID}>Đã trả (PAID)</Select.Option>
              </Select>
            </div>

            <div>
              <div className="text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wider">Kỳ hóa đơn</div>
              <DatePicker
                picker="month"
                format="MM/YYYY"
                placeholder="Tất cả các kỳ"
                style={{ width: '100%' }}
                allowClear
                value={selectedPeriod}
                onChange={(date) => {
                  setSelectedPeriod(date);
                  resetPage();
                }}
              />
            </div>
          </div>
        </Drawer>

        {/* Mobile Summary Modal */}
        <Modal
          title={
            <div className="flex items-center gap-2">
              <DollarOutlined className="text-rose-500" />
              <span>Chi tiết thống kê chi tiêu</span>
            </div>
          }
          open={isSummaryModalOpen}
          onCancel={() => setIsSummaryModalOpen(false)}
          footer={null}
          centered
          width={400}
        >
          <div className="space-y-3 pt-2">
            <Card size="small" className="bg-slate-50 border-slate-100">
              <Statistic
                title="Tổng cộng tiền chi"
                value={summary?.total || 0}
                formatter={(val) => formatCurrency(Number(val))}
                prefix={<DollarOutlined className="text-rose-500 mr-2" />}
              />
            </Card>
            <Card size="small" className="bg-emerald-50/50 border-emerald-100">
              <Statistic
                title="Đã thanh toán (Đã trả)"
                value={summary?.total_paid || 0}
                formatter={(val) => formatCurrency(Number(val))}
                styles={{ content: { color: '#059669' } }}
                prefix={<CheckCircleOutlined className="text-emerald-500 mr-2" />}
              />
            </Card>
            <Card size="small" className="bg-amber-50/50 border-amber-100">
              <Statistic
                title="Còn nợ (Chưa trả)"
                value={summary?.total_unpaid || 0}
                formatter={(val) => formatCurrency(Number(val))}
                styles={{ content: { color: '#d97706' } }}
                prefix={<ClockCircleOutlined className="text-amber-500 mr-2" />}
              />
            </Card>
          </div>
        </Modal>

        {/* Table */}
        <Table
          dataSource={expenses}
          columns={columns}
          rowKey="id"
          loading={isLoadingExpenses}
          pagination={getPaginationProps(totalCount)}
          scroll={{ x: 800 }}
        />
      </Card>

      {/* Modals */}
      <CreateExpenseModal
        open={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
      />
      <UpdateExpenseModal
        open={!!editingExpense}
        expense={editingExpense}
        onClose={() => setEditingExpense(null)}
      />
    </div>
  );
};

export default ExpenseManagementPage;
