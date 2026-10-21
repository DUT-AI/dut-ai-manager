import React from 'react';
import { Page, Spinner } from 'zmp-ui';
import logoImg from '@/assets/logo.png';

export interface PageLoadingProps {
  /** Thông điệp hiển thị dưới spinner */
  text?: string;
  /** ClassName bổ sung */
  className?: string;
  /** Render dạng bọc <Page> (mặc định: true) hay dạng full-screen overlay (false) */
  asPage?: boolean;
}

export const PageLoading: React.FC<PageLoadingProps> = ({
  text = 'Đang tải dữ liệu...',
  className = '',
  asPage = true,
}) => {
  const content = (
    <div className={`w-full min-h-screen flex flex-col items-center justify-center text-center p-4 gap-3 bg-[#f8fafc] ${className}`}>
      <Spinner visible logo={logoImg} />
      {text && (
        <span className="text-xs text-gray-500 font-medium text-center max-w-xs animate-pulse">
          {text}
        </span>
      )}
    </div>
  );

  if (asPage) {
    return (
      <Page className="bg-[#f8fafc] w-full min-h-screen flex flex-col items-center justify-center m-0 p-0">
        {content}
      </Page>
    );
  }

  return (
    <div className="fixed inset-0 z-50 w-screen h-screen flex flex-col items-center justify-center bg-[#f8fafc]">
      {content}
    </div>
  );
};

export default PageLoading;
