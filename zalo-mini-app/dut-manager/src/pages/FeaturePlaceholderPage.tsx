import React from 'react';
import { Page, Box, Text, Button, Icon } from 'zmp-ui';
import Header from '@/components/Header';
import { useNavigate, useLocation } from 'react-router-dom';

interface FeaturePageProps {
  title: string;
  description?: string;
  icon?: string;
}

const FeaturePlaceholderPage: React.FC<FeaturePageProps> = ({
  title,
  description = 'Tính năng đang được đồng bộ dữ liệu từ Backend DUT AI Manager',
  icon = 'zi-calendar',
}) => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Page className="bg-surface flex flex-col min-h-screen">
      <Header title={title} showBack={true} />

      <div className="px-4 py-8 flex-1 flex flex-col items-center justify-center text-center gap-4">
        <div className="w-16 h-16 rounded-3xl bg-blue-50 text-blue-600 flex items-center justify-center shadow-sm">
          <Icon icon={icon as any} size={32} />
        </div>

        <div className="flex flex-col gap-1 max-w-xs">
          <h3 className="font-bold text-base text-gray-900">{title}</h3>
          <p className="text-xs text-gray-500">{description}</p>
        </div>

        <div className="bg-white border border-gray-100 rounded-2xl p-4 w-full shadow-sm text-left flex flex-col gap-2">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span>Đường dẫn hiện tại:</span>
            <span className="font-mono text-gray-600 font-semibold">{location.pathname}</span>
          </div>
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span>Trạng thái kết nối API:</span>
            <span className="text-green-600 font-semibold">Sẵn sàng</span>
          </div>
        </div>

        <Button
          variant="secondary"
          size="small"
          onClick={() => navigate(-1)}
          className="rounded-xl mt-2"
        >
          Quay lại trang trước
        </Button>
      </div>
    </Page>
  );
};

export default FeaturePlaceholderPage;
