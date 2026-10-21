import React, { useState } from 'react';
import { Button, Card, Typography } from 'antd';
import { DownloadOutlined, CloseOutlined, ExportOutlined, PlusSquareOutlined } from '@ant-design/icons';
import { usePwaInstall } from '../hooks/usePwaInstall';

const { Text, Paragraph } = Typography;

export const PwaInstallPrompt: React.FC = () => {
  const { isInstallable, isInstalled, isIos, promptInstall } = usePwaInstall();
  const [dismissed, setDismissed] = useState<boolean>(() => {
    return sessionStorage.getItem('pwa_prompt_dismissed') === 'true';
  });

  if (isInstalled || dismissed) {
    return null;
  }

  // Không hiển thị nếu không phải thiết bị iOS và trình duyệt cũng chưa sẵn sàng prompt
  if (!isInstallable && !isIos) {
    return null;
  }

  const handleDismiss = () => {
    sessionStorage.setItem('pwa_prompt_dismissed', 'true');
    setDismissed(true);
  };

  const handleInstallClick = async () => {
    const success = await promptInstall();
    if (success) {
      setDismissed(true);
    }
  };

  return (
    <div className="fixed bottom-4 left-4 right-4 z-50 max-w-md mx-auto animate-fade-in">
      <Card
        className="shadow-2xl border-blue-500/30 bg-white/95 backdrop-blur-md rounded-2xl overflow-hidden"
        bodyStyle={{ padding: '16px' }}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex gap-3">
            <div className="w-12 h-12 rounded-xl bg-blue-600 flex items-center justify-center shrink-0 shadow-md">
              <img src="/icons/icon-192x192.png" alt="DUT AI" className="w-10 h-10 rounded-lg object-contain" />
            </div>
            <div>
              <Text strong className="text-base text-gray-900 block leading-tight">
                Cài đặt DUT AI Manager
              </Text>
              <Text type="secondary" className="text-xs">
                Trải nghiệm mượt mà và nhận thông báo như app điện thoại
              </Text>
            </div>
          </div>
          <Button
            type="text"
            shape="circle"
            size="small"
            icon={<CloseOutlined className="text-gray-400 hover:text-gray-600 text-xs" />}
            onClick={handleDismiss}
          />
        </div>

        {isIos ? (
          <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-600 space-y-1.5">
            <Paragraph className="!mb-1 text-xs">
              Để cài đặt trên iPhone/iPad:
            </Paragraph>
            <div className="flex items-center gap-1.5 bg-gray-50 p-2 rounded-lg text-gray-700">
              <span>1. Chạm biểu tượng <strong>Chia sẻ</strong></span>
              <ExportOutlined className="text-blue-600 text-sm" />
            </div>
            <div className="flex items-center gap-1.5 bg-gray-50 p-2 rounded-lg text-gray-700">
              <span>2. Kéo xuống chọn <strong>Thêm vào MH chính</strong></span>
              <PlusSquareOutlined className="text-blue-600 text-sm" />
            </div>
          </div>
        ) : (
          <div className="mt-3 flex justify-end gap-2">
            <Button size="small" onClick={handleDismiss}>
              Để sau
            </Button>
            <Button
              type="primary"
              size="small"
              icon={<DownloadOutlined />}
              onClick={handleInstallClick}
              className="bg-blue-600 hover:bg-blue-700"
            >
              Cài đặt ngay
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
};
