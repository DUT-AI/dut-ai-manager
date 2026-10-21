import React, { useState } from 'react';
import { Alert, Button } from 'antd';
import { BellOutlined } from '@ant-design/icons';
import { useWebPush } from '../hooks/useWebPush';

export const PushBanner: React.FC = () => {
  const { isSupported, isSubscribed, permission, isLoading, subscribeToPush } = useWebPush();
  const [dismissed, setDismissed] = useState<boolean>(() => {
    return sessionStorage.getItem('push_banner_dismissed') === 'true';
  });

  // Không hiển thị nếu không hỗ trợ, đã đăng ký rồi, hoặc đã bị chặn quyền / người dùng đã đóng
  if (!isSupported || isSubscribed || permission === 'denied' || dismissed) {
    return null;
  }

  const handleDismiss = () => {
    sessionStorage.setItem('push_banner_dismissed', 'true');
    setDismissed(true);
  };

  const handleEnable = async () => {
    const success = await subscribeToPush();
    if (success) {
      setDismissed(true);
    }
  };

  return (
    <div className="w-full bg-blue-50/90 border-b border-blue-200 px-4 py-2 text-xs transition-all">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-blue-900">
          <BellOutlined className="text-blue-600 text-sm animate-bounce" />
          <span>
            Bật thông báo đẩy để nhận cảnh báo lịch họp và nhắc nhở bài tập ngay trên màn hình khóa.
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="small"
            type="text"
            className="text-gray-500 hover:text-gray-800 text-xs h-7"
            onClick={handleDismiss}
          >
            Để sau
          </Button>
          <Button
            size="small"
            type="primary"
            loading={isLoading}
            onClick={handleEnable}
            className="bg-blue-600 hover:bg-blue-700 text-xs h-7 rounded-md"
          >
            Bật thông báo
          </Button>
        </div>
      </div>
    </div>
  );
};
