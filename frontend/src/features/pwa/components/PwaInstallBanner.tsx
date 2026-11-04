import React, { useState } from 'react';
import { Button } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';
import { usePwaInstall } from '../hooks/usePwaInstall';
import { IosInstallModal } from './IosInstallModal';

export const PwaInstallBanner: React.FC = () => {
  const {
    isMobile,
    isInstalled,
    isInstallable,
    installStrategy,
    promptInstall,
  } = usePwaInstall();

  const [showModal, setShowModal] = useState<boolean>(false);
  const [isPrompting, setIsPrompting] = useState<boolean>(false);

  // Chỉ hiển thị trên điện thoại / máy tính bảng (Mobile/Tablet) chưa cài đặt PWA
  // Tuyệt đối không hiển thị trên Desktop (máy tính) hoặc khi đã cài đặt (Standalone PWA)
  if (!isMobile || isInstalled) {
    return null;
  }

  const handleInstallClick = async () => {
    // 1. Nếu trình duyệt hỗ trợ Native Prompt (Android Chrome, Edge, Samsung Internet...)
    if (installStrategy === 'native_prompt' && isInstallable) {
      setIsPrompting(true);
      try {
        await promptInstall();
      } finally {
        setIsPrompting(false);
      }
      return;
    }

    // 2. Với iOS Safari, In-App WebView hoặc Android không có prompt: Mở modal hướng dẫn
    setShowModal(true);
  };

  return (
    <>
      <div className="w-full bg-gradient-to-r from-blue-50/95 via-indigo-50/95 to-blue-50/95 border-b border-indigo-200/80 px-3 sm:px-4 py-2 text-xs transition-all shadow-sm">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-2">
          {/* Logo / Icon & Thông điệp kêu gọi cài app */}
          <div className="flex items-center gap-2 min-w-0 flex-1">
            <div className="w-5 h-5 rounded-md bg-blue-600 flex items-center justify-center shrink-0 shadow-xs">
              <img
                src="/icons/icon-192x192.png"
                alt="DUT AI"
                className="w-4 h-4 rounded-sm object-contain"
              />
            </div>
            <span className="text-blue-950 font-medium text-[11px] sm:text-xs truncate">
              <span className="hidden xs:inline sm:inline">
                Cài đặt DUT AI Manager về màn hình chính để mở nhanh và tiện lợi hơn.
              </span>
              <span className="xs:hidden sm:hidden">
                Cài đặt ứng dụng DUT AI Manager
              </span>
            </span>
          </div>

          {/* Duy nhất một nút hành động chính (Không có nút "Để sau") */}
          <div className="shrink-0 flex items-center">
            <Button
              size="small"
              type="primary"
              loading={isPrompting}
              icon={<DownloadOutlined className="text-xs" />}
              onClick={handleInstallClick}
              className="bg-indigo-600 hover:bg-indigo-700 text-white text-[11px] sm:text-xs h-7 px-2.5 sm:px-3 rounded-md font-medium shadow-xs"
            >
              <span className="hidden xs:inline sm:inline">Cài đặt ngay</span>
              <span className="xs:hidden sm:hidden">Tải app</span>
            </Button>
          </div>
        </div>
      </div>

      {/* Modal hướng dẫn trực quan dành cho iOS Safari / In-App WebView / Fallback */}
      <IosInstallModal
        open={showModal}
        onClose={() => setShowModal(false)}
        strategy={installStrategy}
      />
    </>
  );
};
