import { useEffect, useState, useRef } from 'react';
import { Alert, Tag, Modal, Button, Typography } from 'antd';
import { UserOutlined, WarningOutlined, SafetyOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { useCapacity } from '@/context/CapacityContext';

const { Text } = Typography;

export const CapacityWarning = () => {
  const { capacity } = useCapacity();
  const [warningModalVisible, setWarningModalVisible] = useState(false);
  const [overloadModalVisible, setOverloadModalVisible] = useState(false);
  const prevStatus = useRef<string | null>(null);

  useEffect(() => {
    if (!capacity) return;

    // Only show popup when status CHANGES to warning/overload
    // (avoid popup every 15 min if status unchanged)
    if (capacity.status === 'warning' && prevStatus.current !== 'warning') {
      setWarningModalVisible(true);
    }
    if (capacity.status === 'overload' && prevStatus.current !== 'overload') {
      setOverloadModalVisible(true);
    }
    prevStatus.current = capacity.status;
  }, [capacity]);

  if (!capacity) return null;

  const { status, current_count, future_count, max_capacity } = capacity;

  const config = {
    safe: {
      icon: <SafetyOutlined />,
      color: 'success',
      message: `Không gian an toàn (${current_count}/${max_capacity})`,
      description: `Hiện tại ${current_count} người. Dự báo: ${future_count} người.`,
    },
    warning: {
      icon: <WarningOutlined />,
      color: 'warning',
      message: `Cảnh báo sắp đầy (${current_count}/${max_capacity})`,
      description: `Hiện tại ${current_count} người. Dự báo: ${future_count} người - sắp đạt giới hạn!`,
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
    <>
      {/* Compact inline indicator */}
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

      {/* Popup WARNING */}
      <Modal
        open={warningModalVisible}
        onCancel={() => setWarningModalVisible(false)}
        title={
          <div className="flex items-center gap-2">
            <ExclamationCircleOutlined className="text-yellow-500 text-xl" />
            <span>Cảnh báo: Sắp đạt giới hạn sức chứa</span>
          </div>
        }
        footer={[
          <Button key="close" onClick={() => setWarningModalVisible(false)}>
            Đã hiểu
          </Button>
        ]}
      >
        <div className="py-3">
          <p>Phòng lab hiện có <Text strong>{capacity?.current_count}</Text> người.</p>
          <p>Dự báo 30 phút tới: <Text strong>{capacity?.future_count}/{capacity?.max_capacity}</Text> người.</p>
          <p className="text-gray-500 mt-2">Hạn chế đăng ký thêm buổi họp để tránh quá tải.</p>
        </div>
      </Modal>

      {/* Popup OVERLOAD */}
      <Modal
        open={overloadModalVisible}
        onCancel={() => setOverloadModalVisible(false)}
        title={
          <div className="flex items-center gap-2">
            <ExclamationCircleOutlined className="text-red-500 text-xl" />
            <span>Quá tải: Phòng lab đã vượt giới hạn</span>
          </div>
        }
        footer={[
          <Button key="close" danger onClick={() => setOverloadModalVisible(false)}>
            Xác nhận
          </Button>
        ]}
      >
        <div className="py-3">
          <p>Dự báo số người: <Text strong type="danger">{capacity?.future_count}/{capacity?.max_capacity}</Text>.</p>
          <p className="text-red-500 font-medium mt-2">Việc tạo lịch họp mới đã bị tạm thời vô hiệu hóa.</p>
        </div>
      </Modal>
    </>
  );
};
