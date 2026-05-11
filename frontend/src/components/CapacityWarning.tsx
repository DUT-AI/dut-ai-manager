import { useEffect, useState } from 'react';
import { Alert, Tag } from 'antd';
import { UserOutlined, WarningOutlined, SafetyOutlined } from '@ant-design/icons';

interface CapacityStatus {
  current_count: number;
  incoming_count: number;
  outgoing_count: number;
  future_count: number;
  status: 'safe' | 'warning' | 'overload';
  max_capacity: number;
}

export const CapacityWarning = () => {
  const [capacity, setCapacity] = useState<CapacityStatus | null>(null);
  const [, setLoading] = useState(false);

  const fetchCapacity = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/capacity/forecast');
      const result = await response.json();
      if (result.success) {
        setCapacity(result.data);
      }
    } catch (error) {
      console.error('Failed to fetch capacity:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCapacity();
    const interval = setInterval(fetchCapacity, 5 * 60 * 1000); // Refresh every 5 min
    return () => clearInterval(interval);
  }, []);

  if (!capacity) return null;

  const { status, current_count, future_count, max_capacity } = capacity;

  const config = {
    safe: {
      icon: <SafetyOutlined />,
      color: 'success',
      message: `Không gian an toàn (${current_count}/${max_capacity})`,
      description: `Hiện tại ${current_count} người. Dự báo 30 phút tới: ${future_count} người.`,
    },
    warning: {
      icon: <WarningOutlined />,
      color: 'warning',
      message: `Cảnh báo sắp đầy (${current_count}/${max_capacity})`,
      description: `Hiện tại ${current_count} người. Dự báo 30 phút tới: ${future_count} người - sắp đạt giới hạn!`,
    },
    overload: {
      icon: <UserOutlined />,
      color: 'error',
      message: `Quá tải! (${future_count}/${max_capacity})`,
      description: `Dự báo sẽ vượt quá ${max_capacity} người. Không thể đăng ký thêm.`,
    },
  };

  const { icon, color, message, description } = config[status];

  return (
    <Alert
      icon={icon}
      type={color as 'success' | 'warning' | 'error'}
      message={message}
      description={
        <div>
          <div>{description}</div>
          <div className="mt-2">
            <Tag color="blue">Hiện tại: {current_count}</Tag>
            <Tag color="orange">Sắp đến: +{capacity.incoming_count}</Tag>
            <Tag color="green">Sắp đi: -{capacity.outgoing_count}</Tag>
            <Tag color="purple">Dự báo: {future_count}</Tag>
          </div>
        </div>
      }
      showIcon
      className="mb-4"
    />
  );
};
