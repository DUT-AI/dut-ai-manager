import React, { useState, useEffect } from 'react';
import { Page, Input, Button, Icon, Spinner, Box, useSnackbar } from 'zmp-ui';
import { getPhoneNumber } from 'zmp-sdk/apis';
import Header from '@/components/Header';
import { useAuth } from '@/context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { PATHS } from '@/constants/paths';
import { getSavedCredentials, setSavedCredentials } from '@/utils/storage';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, loginWithZaloPhone, isAuthenticated, loading: authLoading } = useAuth();
  const { openSnackbar } = useSnackbar();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [loadingEmail, setLoadingEmail] = useState(false);
  const [loadingZalo, setLoadingZalo] = useState(false);

  // 1. Tự động lấy tài khoản/mật khẩu đã lưu từ trước
  useEffect(() => {
    const saved = getSavedCredentials();
    if (saved) {
      if (saved.email) setEmail(saved.email);
      if (saved.password) setPassword(saved.password);
      if (typeof saved.rememberMe === 'boolean') setRememberMe(saved.rememberMe);
    }
  }, []);

  // 2. Tự động chuyển hướng về trang chủ nếu đã có Access Token hợp lệ (Auto-login)
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      navigate(PATHS.HOME, { replace: true });
    }
  }, [isAuthenticated, authLoading, navigate]);

  // 3. Đăng nhập bằng Số điện thoại Zalo (1-Touch)
  const handleZaloPhoneLogin = async () => {
    setLoadingZalo(true);
    try {
      // Gọi ZMP SDK xin cấp quyền và lấy phone token
      const phoneRes = await getPhoneNumber();
      const phoneToken =
        (phoneRes as any)?.token ||
        (phoneRes as any)?.numberToken ||
        (phoneRes as any)?.code ||
        (typeof phoneRes === 'string' ? phoneRes : null);

      if (!phoneToken) {
        openSnackbar({
          text: 'Không nhận được token số điện thoại từ Zalo',
          type: 'warning',
        });
        return;
      }

      const response = await loginWithZaloPhone(phoneToken);
      if (response.is_success) {
        openSnackbar({ text: 'Đăng nhập thành công qua Zalo!', type: 'success' });
        navigate(PATHS.HOME, { replace: true });
      } else {
        openSnackbar({
          text: response.message || 'Số điện thoại chưa được cấp quyền trong hệ thống',
          type: 'error',
        });
      }
    } catch (error: any) {
      console.error('[LoginPage] Zalo getPhoneNumber error:', error);
      const errMsg =
        error?.response?.data?.message ||
        error?.message ||
        'Bạn đã từ chối cấp quyền hoặc Zalo App chưa bật quyền SĐT';
      openSnackbar({
        text: errMsg,
        type: 'error',
      });
    } finally {
      setLoadingZalo(false);
    }
  };

  // 4. Đăng nhập bằng Email & Mật khẩu
  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      openSnackbar({ text: 'Vui lòng nhập đầy đủ Email và Mật khẩu', type: 'warning' });
      return;
    }

    setLoadingEmail(true);
    try {
      const response = await login({ email, password });
      if (response && response.is_success) {
        // Lưu lại tài khoản & mật khẩu nếu tích chọn Ghi nhớ
        if (rememberMe) {
          setSavedCredentials({ email, password, rememberMe: true });
        } else {
          setSavedCredentials(null);
        }

        openSnackbar({ text: 'Đăng nhập thành công!', type: 'success' });
        navigate(PATHS.HOME, { replace: true });
      } else {
        openSnackbar({
          text: response?.message || 'Email hoặc mật khẩu không chính xác',
          type: 'error',
          duration: 3000,
        });
      }
    } catch (error: any) {
      console.error('[LoginPage] Error logging in:', error);
      const errMsg =
        error?.response?.data?.message ||
        error?.message ||
        'Có lỗi xảy ra khi kết nối máy chủ';
      openSnackbar({
        text: `Lỗi: ${errMsg}`,
        type: 'error',
        duration: 3500,
      });
    } finally {
      setLoadingEmail(false);
    }
  };

  if (authLoading) {
    return (
      <Box className="flex flex-col items-center justify-center min-h-screen bg-surface gap-3">
        <Spinner visible logo="" />
        <span className="text-xs text-gray-500">Đang tự động xác thực phiên đăng nhập...</span>
      </Box>
    );
  }

  return (
    <Page className="bg-surface flex flex-col min-h-screen">
      <Header title="Đăng nhập" showBack={true} />

      <div className="px-4 py-6 flex-1 flex flex-col justify-between pb-10">
        <div className="flex flex-col gap-6">
          {/* Top intro */}
          <div className="flex flex-col items-center text-center gap-2 mt-2">
            <div className="w-16 h-16 rounded-3xl bg-blue-600 flex items-center justify-center text-white text-2xl font-black shadow-lg shadow-blue-200">
              DUT
            </div>
            <h2 className="text-xl font-bold text-gray-900 mt-2">DUT AI Manager</h2>
            <p className="text-xs text-gray-500 max-w-xs">
              Chọn phương thức đăng nhập để truy cập hệ thống quản lý
            </p>
          </div>

          {/* Option 1: Zalo Phone Login Button */}
          <div className="flex flex-col gap-2">
            <Button
              onClick={handleZaloPhoneLogin}
              loading={loadingZalo}
              className="rounded-2xl w-full font-bold py-3.5 bg-[#0068FF] text-white flex items-center justify-center gap-2 shadow-md shadow-blue-100 active:opacity-90"
            >
              <Icon icon="zi-call" className="text-lg" />
              <span>Đăng nhập bằng Số điện thoại Zalo</span>
            </Button>
            <p className="text-[11px] text-center text-gray-400">
              Xác thực 1 chạm tiện lợi thông qua số điện thoại Zalo
            </p>
          </div>

          {/* Divider */}
          <div className="flex items-center gap-3 my-1">
            <div className="flex-1 h-px bg-gray-200" />
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Hoặc dùng tài khoản
            </span>
            <div className="flex-1 h-px bg-gray-200" />
          </div>

          {/* Option 2: Email & Password Form */}
          <form onSubmit={handleEmailLogin} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-xs font-semibold text-gray-700">Email DUT</label>
              <Input
                type="email"
                placeholder="vd: student@dut.udn.vn"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="rounded-xl"
              />
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-xs font-semibold text-gray-700">Mật khẩu</label>
              <Input.Password
                placeholder="Nhập mật khẩu"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="rounded-xl"
              />
            </div>

            {/* Checkbox Ghi nhớ tài khoản */}
            <div className="flex items-center justify-between pt-1">
              <label className="flex items-center gap-2 cursor-pointer text-xs text-gray-600 font-medium">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 rounded text-blue-600 border-gray-300 focus:ring-blue-500"
                />
                <span>Ghi nhớ tài khoản & mật khẩu</span>
              </label>
            </div>

            <Button
              htmlType="submit"
              loading={loadingEmail}
              variant="secondary"
              className="rounded-xl w-full mt-2 font-bold py-3 border border-gray-300"
            >
              Đăng nhập với Email & Mật khẩu
            </Button>
          </form>
        </div>

        <div className="text-center text-xs text-gray-400 mt-6">
          Hệ thống quản lý nghiên cứu & đào tạo Lab DUT AI
        </div>
      </div>
    </Page>
  );
};

export default LoginPage;

