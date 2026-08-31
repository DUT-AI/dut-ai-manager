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
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  SwapOutlined,
  DollarOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { useUsers } from '@/features/users';
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

const { Text } = Typography;

const ExpenseManagementPage: React.FC = () => {
  // Filters: Selected Spender, Team, Status, Month/Year
  const [filterSpender, setFilterSpender] = useState<number | undefined>(undefined);
  const [filterTeam, setFilterTeam] = useState<number | undefined>(undefined);
  const [selectedStatus, setSelectedStatus] = useState<ExpenseStatusType | undefined>(undefined);
  const [selectedPeriod, setSelectedPeriod] = useState<dayjs.Dayjs | null>(null);

  const selectedMonth = selectedPeriod ? selectedPeriod.month() + 1 : undefined;
  const selectedYear = selectedPeriod ? selectedPeriod.year() : undefined;

  const { data: usersData } = useUsers();
  const { data: teamsData } = useTeams();
  const users = usersData || [];
  const teams = teamsData || [];

  // Modals state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingExpense, setEditingExpense] = useState<ExpenseInvoice | null>(null);

  // Queries & Mutations
  const { data: expensesData, isLoading: isLoadingExpenses } = useExpenses({
    month: selectedMonth,
    year: selectedYear,
    status: selectedStatus,
    spender_id: filterSpender,
    team_id: filterTeam,
  });
  const expenses = expensesData || [];

  const { data: summary, isLoading: isLoadingSummary } = useExpenseSummary({
    month: selectedMonth,
    year: selectedYear,
    spender_id: filterSpender,
    team_id: filterTeam,
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
        <div>
          <div className="font-medium text-gray-800">{text}</div>
          {record.note && <div className="text-xs text-gray-500 italic">Ghi chú: {record.note}</div>}
        </div>
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
      title: 'Nhóm',
      dataIndex: 'team',
      key: 'team',
      width: 160,
      render: (_: any, record: ExpenseInvoice) => (
        <Tag color="blue" className="font-medium">
          {record.team?.team_name || 'N/A'}
        </Tag>
      ),
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

      {/* KPI Stats Cards */}
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

      {/* Main Table Card */}
      <Card className="shadow-sm border-gray-100">
        {/* Filters Bar */}
        <Row gutter={[16, 16]} align="middle" className="bg-gray-50/50 p-4 rounded-xl border border-gray-100 mb-4">
          <Col xs={24} sm={12} md={6} lg={6}>
            <div className="text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wider">Người chi</div>
            <Select
              showSearch
              placeholder="Tất cả người chi"
              style={{ width: '100%' }}
              allowClear
              value={filterSpender}
              onChange={(value) => setFilterSpender(value)}
              optionFilterProp="children"
            >
              {users.map((u) => (
                <Select.Option key={u.id} value={u.id}>
                  {u.name} ({u.email})
                </Select.Option>
              ))}
            </Select>
          </Col>

          <Col xs={24} sm={12} md={6} lg={6}>
            <div className="text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wider">Nhóm (Team)</div>
            <Select
              showSearch
              placeholder="Tất cả nhóm"
              style={{ width: '100%' }}
              allowClear
              value={filterTeam}
              onChange={(value) => setFilterTeam(value)}
              optionFilterProp="children"
            >
              {teams.map((t) => (
                <Select.Option key={t.id} value={t.id}>
                  {t.team_name}
                </Select.Option>
              ))}
            </Select>
          </Col>

          <Col xs={24} sm={8} md={8} lg={6}>
            <div className="text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wider">Trạng thái</div>
            <Select
              placeholder="Tất cả trạng thái"
              style={{ width: '100%' }}
              allowClear
              value={selectedStatus}
              onChange={(value) => setSelectedStatus(value)}
            >
              <Select.Option value={ExpenseStatus.UNPAID}>Chưa trả (UNPAID)</Select.Option>
              <Select.Option value={ExpenseStatus.PAID}>Đã trả (PAID)</Select.Option>
            </Select>
          </Col>

          <Col xs={24} sm={8} md={8} lg={6}>
            <div className="text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wider">Kỳ hóa đơn</div>
            <DatePicker
              picker="month"
              format="MM/YYYY"
              placeholder="Tất cả các kỳ"
              style={{ width: '100%' }}
              allowClear
              value={selectedPeriod}
              onChange={(date) => setSelectedPeriod(date)}
            />
          </Col>
        </Row>

        {/* Table */}
        <Table
          dataSource={expenses}
          columns={columns}
          rowKey="id"
          loading={isLoadingExpenses}
          pagination={{ pageSize: 15, showSizeChanger: true }}
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
