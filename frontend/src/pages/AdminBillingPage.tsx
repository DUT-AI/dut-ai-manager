import { useState } from 'react';
import { Card, Button, Typography, Space, Form, message, Grid, Tabs, Select, DatePicker, Row, Col, Statistic } from 'antd';
import { PlusOutlined, AuditOutlined, CalendarOutlined, TableOutlined, BarChartOutlined, DollarOutlined, ImportOutlined, ExportOutlined, CheckCircleOutlined, ClockCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { useAllInvoices, useCreateInvoice, useUpdateInvoice, useInvoiceDetail, useDeleteInvoice } from '@/hooks/useBilling';
import { useUsers } from '@/hooks';
import { useTeams } from '@/hooks/useTeams';
import CreateMonthlyInvoiceModal from '@/components/billing/CreateMonthlyInvoiceModal';
import type { InvoiceCreate, Invoice } from '@/types/billing.types';
import { motion, type Variants } from 'motion/react';

// Sub-components
import BillingTable from './billing/components/BillingTable';
import CreateInvoiceModal from './billing/components/CreateInvoiceModal';
import UpdateInvoiceModal from './billing/components/UpdateInvoiceModal';
import InvoiceDetailModal from './billing/components/InvoiceDetailModal';
import BillingMatrixReport from './billing/components/BillingMatrixReport';
import ExpenseManagementPage from './ExpenseManagementPage';

const { Title, Text } = Typography;
const { useBreakpoint } = Grid;

const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.1
        }
    }
};

const itemVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
        opacity: 1,
        y: 0,
        transition: { duration: 0.4, ease: "easeOut" }
    }
};

const AdminBillingPage = () => {
  const screens = useBreakpoint();
  const [filterUser, setFilterUser] = useState<number | undefined>(undefined);
  const [filterTeam, setFilterTeam] = useState<number | undefined>(undefined);
  const [filterStatus, setFilterStatus] = useState<string | undefined>(undefined);
  const [filterPeriod, setFilterPeriod] = useState<dayjs.Dayjs | null>(null);

  const { data: invoices = [], isLoading } = useAllInvoices({
    user_id: filterUser,
    team_id: filterTeam,
    status: filterStatus,
    billing_period: filterPeriod ? filterPeriod.startOf('month').format('YYYY-MM-DD') : undefined,
  });
  const { data: users = [] } = useUsers();
  const { data: teams = [] } = useTeams();
  const createInvoice = useCreateInvoice();
  const updateInvoice = useUpdateInvoice();
  const deleteInvoice = useDeleteInvoice();
  
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isUpdateModalOpen, setIsUpdateModalOpen] = useState(false);
  const [isMonthlyModalOpen, setIsMonthlyModalOpen] = useState(false);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<number | null>(null);
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  
  const [form] = Form.useForm();
  const [updateForm] = Form.useForm();

  const { data: detail } = useInvoiceDetail(selectedInvoiceId || 0, isDetailModalOpen);

  const handleCreate = async (values: any) => {
    try {
      const payload: InvoiceCreate = {
        user_id: values.user_id,
        team_id: values.team_id,
        description: values.description,
        billing_period: values.billing_period ? values.billing_period.startOf('month').format('YYYY-MM-DD') : '',
        items: values.items.map((item: any) => ({
          item_type: item.item_type,
          amount: item.amount,
          note: item.note
        }))
      };
      
      await createInvoice.mutateAsync(payload);
      message.success('Tạo hóa đơn thành công');
      setIsCreateModalOpen(false);
      form.resetFields();
    } catch (error: any) {
      message.error(error?.response?.data?.message || 'Có lỗi xảy ra khi tạo hóa đơn');
    }
  };

  const handleUpdate = async (values: any) => {
    if (!selectedInvoiceId) return;
    try {
      const payload = {
        description: values.description,
        items: values.items.map((item: any) => ({
          item_type: item.item_type,
          amount: item.amount,
          note: item.note,
          reference_id: item.reference_id,
        }))
      };
      
      await updateInvoice.mutateAsync({ id: selectedInvoiceId, data: payload });
      message.success('Cập nhật hóa đơn thành công');
      setIsUpdateModalOpen(false);
      setSelectedInvoiceId(null);
      setSelectedInvoice(null);
      updateForm.resetFields();
    } catch (error: any) {
      message.error(error?.response?.data?.message || 'Có lỗi xảy ra khi cập nhật hóa đơn');
    }
  };

  const handleDelete = async (id: number) => {
    setSelectedInvoiceId(id);
    try {
      await deleteInvoice.mutateAsync(id);
      message.success('Xóa hóa đơn thành công');
    } catch (error: any) {
      message.error(error?.response?.data?.message || 'Không thể xóa hóa đơn');
    } finally {
      setSelectedInvoiceId(null);
    }
  };

  const handleViewDetail = (id: number) => {
    setSelectedInvoiceId(id);
    setIsDetailModalOpen(true);
  };

  const handleEdit = (invoice: Invoice) => {
    setSelectedInvoiceId(invoice.id);
    setSelectedInvoice(invoice);
    setIsUpdateModalOpen(true);
  };

  // Calculate Fund and Fine statistics
  const fundAndFineInvoices = invoices.filter((inv) => {
    if (!inv.items || inv.items.length === 0) return true;
    return inv.items.some(
      (item) => item.item_type === 'FUND' || item.item_type === 'VIOLATION'
    );
  });

  const totalFundAndFineAmount = fundAndFineInvoices.reduce((acc, curr) => acc + curr.amount, 0);
  const paidFundAndFineAmount = fundAndFineInvoices
    .filter((inv) => inv.status === 'PAID')
    .reduce((acc, curr) => acc + curr.amount, 0);
  const unpaidFundAndFineAmount = fundAndFineInvoices
    .filter((inv) => inv.status === 'PENDING')
    .reduce((acc, curr) => acc + curr.amount, 0);

  const tabItems = [
    {
      key: '1',
      label: (
        <span className="flex items-center gap-2 px-2">
          <ImportOutlined />
          Hóa đơn nhập vào (Thu)
        </span>
      ),
      children: (
        <div className="p-4">
          {/* KPI Stat Cards (Quỹ & Phạt) */}
          <Row gutter={[16, 16]} className="mb-4">
            <Col xs={24} sm={8}>
              <Card loading={isLoading} className="shadow-sm border-gray-100">
                <Statistic
                  title="Tổng số tiền quỹ (Quỹ & Phạt)"
                  value={totalFundAndFineAmount}
                  formatter={(val) => `${Number(val).toLocaleString()} VNĐ`}
                  prefix={<DollarOutlined className="text-blue-500 mr-2" />}
                />
              </Card>
            </Col>
            <Col xs={24} sm={8}>
              <Card loading={isLoading} className="shadow-sm border-gray-100">
                <Statistic
                  title="Đã nhập vào (Đã thanh toán)"
                  value={paidFundAndFineAmount}
                  formatter={(val) => `${Number(val).toLocaleString()} VNĐ`}
                  styles={{ content: { color: '#52c41a' } }}
                  prefix={<CheckCircleOutlined className="text-green-500 mr-2" />}
                />
              </Card>
            </Col>
            <Col xs={24} sm={8}>
              <Card loading={isLoading} className="shadow-sm border-gray-100">
                <Statistic
                  title="Chưa thanh toán (Chờ nộp quỹ & phạt)"
                  value={unpaidFundAndFineAmount}
                  formatter={(val) => `${Number(val).toLocaleString()} VNĐ`}
                  styles={{ content: { color: '#faad14' } }}
                  prefix={<ClockCircleOutlined className="text-amber-500 mr-2" />}
                />
              </Card>
            </Col>
          </Row>

          {/* Filters Bar */}
          <Row gutter={[16, 16]} align="middle" className="bg-gray-50/50 p-4 rounded-xl border border-gray-100 mb-4">
            <Col xs={24} sm={12} md={6} lg={6}>
              <div className="text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wider">Thành viên</div>
              <Select
                showSearch
                placeholder="Tất cả thành viên"
                style={{ width: '100%' }}
                allowClear
                onChange={(value) => setFilterUser(value)}
                optionFilterProp="children"
              >
                {users.map((u) => (
                  <Select.Option key={u.id} value={u.id}>
                    {u.name}
                  </Select.Option>
                ))}
              </Select>
            </Col>

            <Col xs={24} sm={12} md={6} lg={6}>
              <div className="text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wider">Nhóm</div>
              <Select
                showSearch
                placeholder="Tất cả nhóm"
                style={{ width: '100%' }}
                allowClear
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
            
            <Col xs={24} sm={12} md={6} lg={6}>
              <div className="text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wider">Trạng thái</div>
              <Select
                placeholder="Tất cả trạng thái"
                style={{ width: '100%' }}
                allowClear
                onChange={(value) => setFilterStatus(value)}
              >
                <Select.Option value="PENDING">Chờ thanh toán (PENDING)</Select.Option>
                <Select.Option value="PAID">Đã thanh toán (PAID)</Select.Option>
                <Select.Option value="CANCELLED">Đã hủy (CANCELLED)</Select.Option>
                <Select.Option value="EXPIRED">Hết hạn (EXPIRED)</Select.Option>
              </Select>
            </Col>

            <Col xs={24} sm={12} md={6} lg={6}>
              <div className="text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wider">Kỳ hóa đơn</div>
              <DatePicker
                picker="month"
                format="MM/YYYY"
                placeholder="Tất cả các kỳ"
                style={{ width: '100%' }}
                allowClear
                onChange={(value) => setFilterPeriod(value)}
              />
            </Col>
          </Row>

          <BillingTable
            invoices={invoices}
            isLoading={isLoading}
            users={users}
            onViewDetail={handleViewDetail}
            onEdit={handleEdit}
            onDelete={handleDelete}
            deletingId={deleteInvoice.isPending ? selectedInvoiceId : null}
          />
        </div>
      ),
    },
    {
      key: '2',
      label: (
        <span className="flex items-center gap-2 px-2">
          <ExportOutlined />
          Hóa đơn xuất ra (Chi)
        </span>
      ),
      children: (
        <div className="p-4 bg-gray-50/30">
          <ExpenseManagementPage />
        </div>
      ),
    },
    {
      key: '3',
      label: (
        <span className="flex items-center gap-2 px-2">
          <BarChartOutlined />
          Báo cáo tổng hợp
        </span>
      ),
      children: (
        <div className="p-4 bg-gray-50 border-t border-gray-100">
          <BillingMatrixReport />
        </div>
      ),
    },
  ];

  return (
    <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="p-4 md:p-6 bg-[#f8fafc] min-h-full"
    >
      <motion.div variants={itemVariants}>
        <Card 
            className="shadow-sm border-gray-100 rounded-xl overflow-hidden"
            styles={{
            header: { padding: '20px 24px', borderBottom: '1px solid #f1f5f9' },
            body: { padding: '0' }
            }}
            title={
            <Space size={12}>
                <div className="bg-indigo-50 p-2.5 rounded-xl text-indigo-600 shadow-sm">
                <AuditOutlined className="text-xl" />
                </div>
                <div className="flex flex-col">
                <Title level={4} className="mb-0! leading-tight">Quản lý Hóa đơn</Title>
                <Text type="secondary" className="text-xs font-medium opacity-70">Công cụ dành cho quản trị viên</Text>
                </div>
            </Space>
            }
            extra={
            <Space size={12}>
                <Button 
                icon={<CalendarOutlined />} 
                onClick={() => setIsMonthlyModalOpen(true)}
                className="h-10 px-6 font-semibold rounded-lg border-indigo-200 text-indigo-600 hover:text-indigo-700 hover:border-indigo-300 transition-all"
                >
                Tạo hóa đơn tháng
                </Button>
                <Button 
                type="primary" 
                icon={<PlusOutlined />} 
                onClick={() => setIsCreateModalOpen(true)}
                className="bg-indigo-600 border-none h-10 px-6 font-semibold rounded-lg shadow-md hover:bg-indigo-700 transition-all"
                >
                Tạo hóa đơn
                </Button>
            </Space>
            }
        >
            <Tabs 
            items={tabItems} 
            className="admin-billing-tabs" 
            tabBarStyle={{ padding: '0 24px', marginBottom: 0, backgroundColor: '#fff' }}
            />
        </Card>
      </motion.div>

      {/* Modals */}
      <CreateInvoiceModal
        isOpen={isCreateModalOpen}
        onCancel={() => setIsCreateModalOpen(false)}
        onFinish={handleCreate}
        loading={createInvoice.isPending}
        users={users}
        form={form}
      />

      <UpdateInvoiceModal
        isOpen={isUpdateModalOpen}
        onCancel={() => {
          setIsUpdateModalOpen(false);
          setSelectedInvoiceId(null);
          setSelectedInvoice(null);
        }}
        onFinish={handleUpdate}
        loading={updateInvoice.isPending}
        invoice={selectedInvoice}
        form={updateForm}
      />

      <InvoiceDetailModal
        isOpen={isDetailModalOpen}
        onClose={() => {
          setIsDetailModalOpen(false);
          setSelectedInvoiceId(null);
        }}
        detail={detail}
        users={users}
        isMobile={!screens.md}
      />

      <CreateMonthlyInvoiceModal 
        open={isMonthlyModalOpen}
        onCancel={() => setIsMonthlyModalOpen(false)}
        onSuccess={() => {}}
      />
    </motion.div>
  );
};

export default AdminBillingPage;
