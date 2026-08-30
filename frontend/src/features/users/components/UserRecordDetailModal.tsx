import { Modal, Space, Avatar, Typography, Tag, Table, Spin, Empty } from 'antd';
import { TrophyOutlined, WarningOutlined, UserOutlined, CalendarOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { ColumnsType } from 'antd/es/table';
import type { UserResponse } from '@/features/users/types/user.types';
import type { BonusPointResponse } from '@/features/activity/types/activity.types';
import type { ViolationResponse } from '@/features/violations/types/violation.types';
import { useBonusPoints, useViolations } from '@/hooks';

const { Text, Title } = Typography;

interface UserRecordDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  user: UserResponse | null;
  type: 'bonus' | 'violation';
  totalValue?: number;
  startDate?: string;
  endDate?: string;
  isMobile?: boolean;
}

export const UserRecordDetailModal = ({
  isOpen,
  onClose,
  user,
  type,
  totalValue = 0,
  startDate,
  endDate,
  isMobile,
}: UserRecordDetailModalProps) => {
  const isBonus = type === 'bonus';

  // Fetch bonus points if active tab is bonus
  const { data: bonusPoints = [], isLoading: isBonusLoading } = useBonusPoints({
    userId: user?.id,
    startDate,
    endDate,
    enabled: isOpen && !!user?.id && isBonus,
  });

  // Fetch violations if active tab is violation
  const { data: violations = [], isLoading: isViolationLoading } = useViolations({
    userId: user?.id,
    startDate,
    endDate,
    enabled: isOpen && !!user?.id && !isBonus,
  });

  const loading = isBonus ? isBonusLoading : isViolationLoading;

  const bonusColumns: ColumnsType<BonusPointResponse> = [
    {
      title: 'Thời gian',
      dataIndex: 'date',
      key: 'date',
      width: 140,
      render: (dateStr: string) => (
        <Space size="small">
          <CalendarOutlined className="text-gray-400" />
          <Text className="text-sm">{dayjs(dateStr).format('DD/MM/YYYY')}</Text>
        </Space>
      ),
    },
    {
      title: 'Lý do cộng điểm',
      dataIndex: 'reason',
      key: 'reason',
      render: (reason: string) => <Text>{reason}</Text>,
    },
    {
      title: 'Điểm',
      dataIndex: 'points',
      key: 'points',
      width: 100,
      align: 'right',
      render: (pts: number) => (
        <Tag color="green" className="font-semibold text-sm px-2 py-0.5">
          +{pts}
        </Tag>
      ),
    },
  ];

  const violationColumns: ColumnsType<ViolationResponse> = [
    {
      title: 'Thời gian',
      dataIndex: 'date',
      key: 'date',
      width: 140,
      render: (dateStr: string) => (
        <Space size="small">
          <CalendarOutlined className="text-gray-400" />
          <Text className="text-sm">{dayjs(dateStr).format('DD/MM/YYYY')}</Text>
        </Space>
      ),
    },
    {
      title: 'Lý do vi phạm',
      dataIndex: 'reason',
      key: 'reason',
      render: (reason: string) => <Text>{reason}</Text>,
    },
    {
      title: 'Trạng thái',
      key: 'status',
      width: 110,
      align: 'right',
      render: () => (
        <Tag color="red" className="font-semibold text-xs px-2 py-0.5">
          Vi phạm
        </Tag>
      ),
    },
  ];

  return (
    <Modal
      title={
        <Space size="middle" className="py-1">
          {isBonus ? (
            <TrophyOutlined className="text-yellow-500 text-xl" />
          ) : (
            <WarningOutlined className="text-red-500 text-xl" />
          )}
          <span className="text-lg">
            Chi tiết {isBonus ? 'điểm cộng' : 'vi phạm'} thành viên
          </span>
        </Space>
      }
      open={isOpen}
      onCancel={onClose}
      footer={null}
      width={isMobile ? '95%' : 680}
      centered
      destroyOnClose
    >
      {user && (
        <div className="py-2">
          {/* Header Info Card */}
          <div className="flex items-center justify-between p-4 mb-4 rounded-xl bg-gray-50 border border-gray-100">
            <Space size="middle">
              <Avatar src={user.avatar_url} icon={<UserOutlined />} size={48} className="border border-indigo-100" />
              <div>
                <Title level={5} className="!mb-0">{user.name}</Title>
                <Text type="secondary" className="text-xs">{user.email}</Text>
              </div>
            </Space>
            <div className="text-right">
              <Text type="secondary" className="text-xs block">
                Tổng {isBonus ? 'Điểm cộng' : 'Vi phạm'}
              </Text>
              <Text strong className="text-xl" type={isBonus ? 'success' : 'danger'}>
                {isBonus ? `+${totalValue}` : `${totalValue} lượt`}
              </Text>
            </div>
          </div>

          {/* Records Table / Loading */}
          {loading ? (
            <div className="py-12 text-center">
              <Spin tip="Đang tải danh sách..." />
            </div>
          ) : isBonus ? (
            bonusPoints.length > 0 ? (
              <Table
                columns={bonusColumns}
                dataSource={bonusPoints}
                rowKey="id"
                pagination={{ pageSize: 5 }}
                size="small"
                className="mt-2"
              />
            ) : (
              <Empty description="Không có bản ghi điểm cộng nào" className="my-8" />
            )
          ) : (
            violations.length > 0 ? (
              <Table
                columns={violationColumns}
                dataSource={violations}
                rowKey="id"
                pagination={{ pageSize: 5 }}
                size="small"
                className="mt-2"
              />
            ) : (
              <Empty description="Không có bản ghi vi phạm nào" className="my-8" />
            )
          )}
        </div>
      )}
    </Modal>
  );
};
