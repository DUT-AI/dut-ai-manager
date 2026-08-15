# Hướng Dẫn Tuân Thủ Nghị Định 13/2023/NĐ-CP & Cấp Quyền Đồng Thuận Dữ Liệu (Granting Permission Consent) Trên Zalo Mini App

> **Tài liệu tham khảo chính thức**: [Zalo Mini App Platform - Update information about compliance with decree & Granting Permission Consent](https://miniapp.zaloplatforms.com/documents/tutorial/update-information-about-compliance-with-decree/granting-permission-consent)

---

## 📌 1. Tổng Quan Về Nghị Định 13 & Yêu Cầu Của Zalo

**Nghị định 13/2023/NĐ-CP** (có hiệu lực từ ngày 01/07/2023) quy định nghiêm ngặt về việc **Bảo vệ Dữ liệu Cá nhân (PDP)** tại Việt Nam.

Đối với tất cả các nhà phát triển và doanh nghiệp vận hành **Zalo Mini App**, việc tuân thủ Nghị định 13 là **ĐIỀU KIỆN BẮT BUỘC** để phiên bản Mini App được **Zalo duyệt lên môi trường Production**.

### Các Nguyên Tắc Cốt Lõi:
1. **Sự đồng thuận minh bạch (Consent)**: Phải xin sự đồng ý của người dùng trước khi thu thập bất kỳ dữ liệu cá nhân nào (Số điện thoại, Họ tên, Vị trí, v.v.).
2. **Cung cấp Điều khoản sử dụng**: Phải có liên kết rõ ràng đến *Điều khoản sử dụng* và *Chính sách bảo mật* trước/trong khi xin quyền.
3. **Quyền rút lại sự đồng thuận & Yêu cầu xóa dữ liệu**: Người dùng có quyền yêu cầu ngừng xử lý hoặc xóa thông tin cá nhân của họ khỏi hệ thống.
4. **Lưu trữ dữ liệu an toàn**: Dữ liệu người dùng Việt Nam phải được lưu trữ và bảo vệ an toàn trên hệ thống máy chủ.

---

## ⚙️ 2. Các Bước Thiết Lập Trên Zalo Developers Console

Để đáp ứng quy định kiểm duyệt của Zalo, bạn cần hoàn thành các bước cấu hình sau trên trang quản trị Zalo Mini App:

### Bước 1: Cập nhật Điều khoản sử dụng & Chính sách bảo mật
1. Truy cập [Zalo Mini App Developers Portal](https://mini.zalo.me/developers).
2. Chọn Mini App của bạn (ví dụ: **DUT AI Manager**).
3. Vào menu **Thiết lập chung** (General Settings) -> mục **Điều khoản sử dụng & Chính sách bảo vệ dữ liệu**.
4. Cập nhật đường link hoặc nội dung chi tiết về:
   - Mục đích thu thập dữ liệu (ví dụ: xác thực tài khoản sinh hoạt CLB, gửi thông báo lịch họp).
   - Loại dữ liệu thu thập (Số điện thoại, họ tên, email).
   - Cam kết bảo mật và không chia sẻ cho bên thứ ba.
   - Đầu mối liên hệ hỗ trợ xóa/sửa dữ liệu cá nhân.

### Bước 2: Kích hoạt UI Cấp quyền đồng thuận (Consent UI)
1. Trong mục **Thiết lập chung**, tìm phần **Hiển thị xác nhận cấp quyền truy cập**.
2. **Bật (Enable)** tùy chọn này để Zalo hiển thị Popup xác nhận điều khoản kèm liên kết đến Điều khoản sử dụng của bạn mỗi khi Mini App yêu cầu quyền dữ liệu cá nhân.

---

## 🎯 3. Quy Tắc Ngữ Cảnh Xin Quyền (Contextual Consent)

> [!CAUTION]
> **LÝ DO PHỔ BIẾN NHẤT KHIẾN ZALO TỪ CHỐI XÉT DUYỆT (REJECT APP):**
> Ứng dụng vừa khởi chạy (màn hình Splash / Trang chủ) đã lập tức bật Popup xin quyền Số điện thoại hoặc Thông tin cá nhân mà người dùng chưa thực hiện bất kỳ hành động nào.

### ❌ Hành vi KHÔNG ĐƯỢC PHÉP (Sẽ bị Reject):
- Gọi `getPhoneNumber()` hoặc `getUserInfo()` ngay trong hàm `useEffect()` khi trang vừa load.
- Chặn người dùng xem thông tin công khai nếu họ chưa cấp quyền số điện thoại.

### ✅ Hành vi ĐẠT CHUẨN (Pass Review 100%):
- **Cho phép khám phá trước**: Người dùng có thể mở Mini App và xem các thông tin giới thiệu, tin tức, bảng tin.
- **Xin quyền theo ngữ cảnh (Contextual)**: Chỉ gọi API xin số điện thoại/thông tin cá nhân khi người dùng **CHỦ ĐỘNG BẤM VÀO MỘT NÚT HÀNH ĐỘNG CỤ THỂ** (Ví dụ: Bấm nút *"Đăng nhập nhanh bằng Zalo"*, *"Xác thực hội viên"*, hoặc *"Đăng ký tham gia"*).

---

## 💻 4. Hướng Dẫn Tích Hợp Kỹ Thuật (Frontend ZMP SDK)

### 4.1. Luồng xin cấp quyền Số điện thoại chuẩn trong Code

```tsx
import React, { useState } from 'react';
import { getPhoneNumber, authorize } from 'zmp-sdk/apis';
import { Button, useSnackbar } from 'zmp-ui';
import { authService } from '@/services/api/auth.service';

export const ZaloPhoneLoginButton = () => {
  const [loading, setLoading] = useState(false);
  const { openSnackbar } = useSnackbar();

  const handleLoginWithZaloPhone = async () => {
    try {
      setLoading(true);

      // 1. Chỉ gọi getPhoneNumber sau khi người dùng chủ động click nút
      const data = await getPhoneNumber();

      if (data && data.number) {
        // Trường hợp Mini App được cấp trực tiếp token số điện thoại
        const token = data.number;
        const res = await authService.loginWithZaloPhone({ token });
        if (res.is_success) {
          openSnackbar({ text: 'Đăng nhập thành công!', type: 'success' });
          // Điều hướng vào màn hình chính
        }
      } else {
        openSnackbar({ text: 'Không lấy được số điện thoại', type: 'error' });
      }
    } catch (error: any) {
      console.warn('[Zalo Consent] Người dùng từ chối cấp quyền hoặc có lỗi:', error);
      // Xử lý mềm dẻo khi người dùng bấm Hủy / Từ chối (không làm crash app)
      openSnackbar({ 
        text: 'Bạn cần đồng ý cấp quyền số điện thoại để đăng nhập.', 
        type: 'warning' 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button
      fullWidth
      loading={loading}
      onClick={handleLoginWithZaloPhone}
      className="bg-primary text-white"
    >
      Đăng nhập bằng Số điện thoại Zalo
    </Button>
  );
};
```

---

## 📋 5. Checklist Tự Kiểm Tra Trước Khi Gửi Duyệt Phiên Bản

Trước khi bấm nút **"Gửi duyệt phiên bản"** trên Zalo Developer, hãy kiểm tra kỹ 5 tiêu chí sau:

- [ ] **1. Điều khoản sử dụng**: Đã điền đầy đủ nội dung/link Điều khoản & Chính sách bảo mật trong *Thiết lập chung*.
- [ ] **2. Bật Consent UI**: Đã bật tính năng hiển thị xác nhận cấp quyền trong trang quản trị Zalo.
- [ ] **3. Không xin quyền cưỡng bức**: Khi mở ứng dụng lần đầu, màn hình xuất hiện bình thường và **KHÔNG** tự động hiện popup xin quyền.
- [ ] **4. Xin quyền đúng lúc**: Popup xin quyền chỉ hiển thị sau khi người dùng bấm nút đăng nhập / thao tác cụ thể.
- [ ] **5. Xử lý khi từ chối**: Nếu người dùng bấm *"Từ chối/Hủy"* trên popup của Zalo, ứng dụng không bị trắng màn hình và hiển thị thông báo hướng dẫn rõ ràng.

---

*Tài liệu này được soạn thảo theo bộ quy chuẩn phát triển Zalo Mini App của DUT AI Manager.*
