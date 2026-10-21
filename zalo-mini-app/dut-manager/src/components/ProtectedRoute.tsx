import React, { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { PATHS } from '@/constants/paths';
import PageLoading from '@/components/PageLoading';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

/**
 * Guard Component bảo vệ các trang yêu cầu đăng nhập.
 * Nếu chưa đăng nhập, tự động chuyển hướng về trang Login.
 */
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      // Điều hướng về trang login nếu chưa đăng nhập
      navigate(PATHS.LOGIN, {
        replace: true,
        state: { from: location.pathname },
      });
    }
  }, [isAuthenticated, loading, navigate, location]);

  // Trong lúc đang kiểm tra phiên đăng nhập từ cache/storage
  if (loading) {
    return <PageLoading text="Đang kiểm tra thông tin đăng nhập..." />;
  }

  // Nếu chưa xác thực, không render nội dung trang được bảo vệ
  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
