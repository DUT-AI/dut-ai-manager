import React from 'react';
import { Modal, Button, Typography } from 'antd';
import {
  ExportOutlined,
  PlusSquareOutlined,
  MoreOutlined,
  CompassOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import type { PwaInstallStrategy } from '../hooks/usePwaInstall';

const { Text, Paragraph } = Typography;

interface IosInstallModalProps {
  open: boolean;
  onClose: () => void;
  strategy: PwaInstallStrategy;
}

export const IosInstallModal: React.FC<IosInstallModalProps> = ({
  open,
  onClose,
  strategy,
}) => {
  return (
    <Modal
      open={open}
      onCancel={onClose}
      footer={[
        <Button
          key="understand"
          type="primary"
          onClick={onClose}
          className="w-full bg-blue-600 hover:bg-blue-700 h-9 rounded-lg font-medium text-sm"
        >
          Đã hiểu
        </Button>,
      ]}
      centered
      width={380}
      className="pwa-install-modal"
    >
      <div className="pt-2 pb-1 text-center">
        <div className="w-14 h-14 mx-auto mb-3 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
          <img
            src="/icons/icon-192x192.png"
            alt="DUT AI Manager"
            className="w-11 h-11 rounded-xl object-contain"
          />
        </div>
        <Text strong className="text-lg text-gray-900 block leading-snug">
          Cài đặt DUT AI Manager
        </Text>
        <Text type="secondary" className="text-xs text-gray-500 block mt-1">
          Đưa ứng dụng ra màn hình chính để mở nhanh và không bỏ lỡ thông báo
        </Text>
      </div>

      <div className="mt-4 space-y-2.5 text-xs text-gray-700">
        {/* Trường hợp người dùng mở link trong Zalo / Facebook In-App Browser */}
        {strategy === 'in_app_browser' && (
          <div className="bg-amber-50 border border-amber-200/80 p-2.5 rounded-xl text-amber-900 mb-3 space-y-1.5">
            <div className="flex items-center gap-1.5 font-medium text-amber-800">
              <CompassOutlined className="text-amber-600 text-sm" />
              <span>Đang mở trong ứng dụng (Zalo/Facebook)</span>
            </div>
            <Paragraph className="!mb-0 text-[11px] text-amber-700 leading-relaxed">
              Trình duyệt nhúng không hỗ trợ cài đặt trực tiếp. Vui lòng bấm biểu tượng{' '}
              <strong>ba chấm (•••)</strong> ở góc trên và chọn{' '}
              <strong>"Mở bằng trình duyệt" (Safari / Chrome)</strong> để cài app.
            </Paragraph>
          </div>
        )}

        {/* Hướng dẫn dành cho iOS Safari */}
        {strategy !== 'android_manual' && (
          <>
            <div className="flex items-center gap-2.5 bg-gray-50/80 p-2.5 rounded-xl border border-gray-100">
              <div className="w-6 h-6 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-xs shrink-0">
                1
              </div>
              <div className="flex-1 flex items-center justify-between gap-1">
                <span>
                  Chạm vào biểu tượng <strong>Chia sẻ</strong> ở thanh dưới Safari
                </span>
                <ExportOutlined className="text-blue-600 text-base shrink-0" />
              </div>
            </div>

            <div className="flex items-center gap-2.5 bg-gray-50/80 p-2.5 rounded-xl border border-gray-100">
              <div className="w-6 h-6 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-xs shrink-0">
                2
              </div>
              <div className="flex-1 flex items-center justify-between gap-1">
                <span>
                  Cuộn xuống và chọn <strong>"Thêm vào Màn hình chính"</strong>
                </span>
                <PlusSquareOutlined className="text-blue-600 text-base shrink-0" />
              </div>
            </div>
          </>
        )}

        {/* Hướng dẫn dành cho Android không có native prompt */}
        {strategy === 'android_manual' && (
          <>
            <div className="flex items-center gap-2.5 bg-gray-50/80 p-2.5 rounded-xl border border-gray-100">
              <div className="w-6 h-6 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-xs shrink-0">
                1
              </div>
              <div className="flex-1 flex items-center justify-between gap-1">
                <span>
                  Chạm vào biểu tượng <strong>Menu ba chấm</strong> góc trên
                </span>
                <MoreOutlined className="text-blue-600 text-base shrink-0" />
              </div>
            </div>

            <div className="flex items-center gap-2.5 bg-gray-50/80 p-2.5 rounded-xl border border-gray-100">
              <div className="w-6 h-6 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-xs shrink-0">
                2
              </div>
              <div className="flex-1 flex items-center justify-between gap-1">
                <span>
                  Chọn <strong>"Cài đặt ứng dụng"</strong> hoặc <strong>"Thêm vào MH chính"</strong>
                </span>
                <CheckCircleOutlined className="text-blue-600 text-base shrink-0" />
              </div>
            </div>
          </>
        )}
      </div>
    </Modal>
  );
};
