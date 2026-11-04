# Research: PWA Mobile Install Top Banner (Universal Mobile Support)

## 1. Phát hiện Thiết bị Di động Toàn diện (Universal Mobile Detection)

Để đảm bảo hỗ trợ **100% tất cả các dòng điện thoại phổ biến** tại Việt Nam và quốc tế:
- **Hệ sinh thái Apple**: iPhone (tất cả các dòng từ iPhone SE, X, 11, 12, 13, 14, 15, 16 Series), iPad (iPad Pro, Air, Mini).
- **Hệ sinh thái Android phổ biến**:
  - **Samsung Galaxy**: Dòng S, Z Fold/Flip, A, M, Note chạy Samsung Internet hoặc Google Chrome.
  - **Xiaomi / Redmi / POCO**: Chạy Mi Browser, Google Chrome hoặc Cốc Cốc.
  - **OPPO / Realme / OnePlus**: Chạy ColorOS Browser / Chrome.
  - **Vivo / iQOO**: Chạy Vivo Browser / Chrome.
  - **Google Pixel, Sony Xperia, Huawei / Honor, Asus, Nokia**, v.v.
- **Các trình duyệt di động**: Google Chrome, Safari, Samsung Internet, Cốc Cốc Mobile, Microsoft Edge, Opera Mobile, Firefox Mobile, Brave.

### Quyết định kỹ thuật
Kết hợp 3 lớp nhận diện thiết bị:
1. **User Agent Regex toàn diện**:
   ```ts
   const isMobileUA = /android|iphone|ipad|ipod|blackberry|iemobile|opera mini|mobile|silk|kindle|fennec|lumia|samsung|huawei|xiaomi|redmi|oppo|realme|vivo/i.test(
     navigator.userAgent
   );
   ```
2. **Khả năng cảm ứng phần cứng (Touch capability)**:
   ```ts
   const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
   ```
3. **Responsive Viewport Breakpoint**:
   ```ts
   const isMobileViewport = window.matchMedia('(max-width: 1024px)').matches;
   ```
4. **Kết quả**:
   `isMobile = (isMobileUA || (hasTouch && isMobileViewport))`
   -> Loại trừ 100% các máy tính Desktop/Laptop chạy chuột thông thường, nhận diện chuẩn xác mọi dòng điện thoại.

---

## 2. Phát hiện Trạng thái PWA Standalone (Installed Mode)

Sử dụng các API chuẩn đa nền tảng:
1. **Trình duyệt chuẩn (Chromium, Firefox, Cốc Cốc, Safari iOS 16.4+)**:
   `window.matchMedia('(display-mode: standalone)').matches`
2. **iOS Safari (Tất cả các phiên bản iOS)**:
   `'standalone' in window.navigator && Boolean((window.navigator as any).standalone)`
3. **Android TWA (Trusted Web Activity) & Webview Launcher**:
   `document.referrer.includes('android-app://')`

---

## 3. Cơ chế Cài đặt Thông minh Đa Nền tảng (Universal Install Routing)

Khi người dùng chạm vào nút **"Cài đặt ngay" / "Tải app"**, hệ thống phân luồng xử lý thông minh theo từng loại trình duyệt:

### A. Nhóm Trình duyệt hỗ trợ Native Prompt (Chrome, Samsung Internet, Edge, Cốc Cốc, Opera Android)
- Lắng nghe và lưu `beforeinstallprompt`.
- Khi bấm "Cài đặt ngay" ➔ Kích hoạt ngay hộp thoại cài đặt gốc của hệ điều hành: `await deferredPrompt.prompt()`.
- Lắng nghe sự kiện `appinstalled` ➔ Cập nhật `isInstalled = true` để ẩn vĩnh viễn banner.

### B. Nhóm Trình duyệt iOS Safari (iPhone / iPad)
- Safari không hỗ trợ `beforeinstallprompt`.
- Khi bấm "Cài đặt ngay" ➔ Mở Modal hướng dẫn trực quan đồ họa dành riêng cho iOS:
  1. Chạm vào nút **Chia sẻ** (biểu tượng hộp vuông có mũi tên trỏ lên ⎋ ở thanh công cụ dưới Safari).
  2. Cuộn xuống và chọn **"Thêm vào Màn hình chính"** (Add to Home Screen ⊞).

### C. Nhóm Trình duyệt Android Không gửi sự kiện trước (Firefox Android, Mi Browser hoặc khi prompt bị chặn tạm thời)
- Nếu trên Android nhưng không có `deferredPrompt`:
  - Thay vì để nút bấm vô tác dụng, hệ thống tự động mở Modal hướng dẫn dành riêng cho Android:
    1. Chạm vào biểu tượng **Menu (⋮)** ở góc trên hoặc thanh công cụ trình duyệt.
    2. Chọn **"Cài đặt ứng dụng"** hoặc **"Thêm vào Màn hình chính"** (Install app / Add to Home screen).

### D. Nhóm Trình duyệt nhúng In-App WebView (Khi mở link trong Zalo, Facebook Messenger, TikTok)
- Nếu người dùng mở web từ link trong Zalo hoặc Facebook Messenger trên điện thoại:
  - Cả iOS và Android đều hướng dẫn bước đầu tiên: *"Chạm vào biểu tượng dấu ba chấm (•••) ở góc trên và chọn 'Mở bằng trình duyệt' (Safari / Chrome) để cài đặt app"*.

---

## 4. Bố cục Giao diện Xếp tầng (Stacked Top Banners Layout)

### Quyết định kỹ thuật
Trong [`frontend/src/App.tsx`](file:///Users/nguyenhuynh/Documents/dut-ai-manager/frontend/src/App.tsx), bố trí vùng banner trên cùng dưới dạng flex column container:

```tsx
<div className="w-full flex flex-col z-40">
  {/* Banner 1: PWA Install Top Banner (Dành riêng cho Mobile chưa cài app) */}
  <PwaInstallBanner />

  {/* Banner 2: Web Push Notification Banner (Dành cho user đã đăng nhập nhưng chưa bật push) */}
  {isAuthenticated && <PushBanner />}
</div>
```

### Phong cách thị giác
- Đồng nhất với ngôn ngữ thiết kế Tailwind CSS & Ant Design hiện có trong [`PushBanner.tsx`](file:///Users/nguyenhuynh/Documents/dut-ai-manager/frontend/src/features/pwa/components/PushBanner.tsx):
  - Chiều cao tối ưu: `h-10` đến `h-11` (khoảng 40px - 44px), `px-3 py-1.5` trên mobile.
  - Phối màu: Nền sáng nhẹ nhàng `bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-indigo-100 text-blue-950`.
  - Icon: Logo ứng dụng thu nhỏ hoặc biểu tượng `DownloadOutlined` sinh động.
  - Thông điệp: *"Cài đặt DUT AI Manager về màn hình chính để mở nhanh và tiện lợi hơn."*
  - Nút bấm: Nút Ant Design Button `type="primary"`, size `small`, bo góc mềm mại `rounded-md`, text *"Cài đặt ngay"* (hoặc *"Tải app"* trên màn hình hẹp < 360px).
  - Không có nút "Để sau" hoặc nút "x" đóng theo đúng chỉ thị người dùng.

---

## 5. Đánh giá Khả năng Kiểm thử (Testability & Verification)
- **Unit Testing**:
  - Dùng Vitest / Jest để kiểm tra hook `usePwaInstall`: mock `window.navigator.userAgent`, mock `matchMedia`, mock `beforeinstallprompt` event.
  - Kiểm tra `PwaInstallBanner`:
    - Khi là Desktop (`isMobile = false`) -> render `null`.
    - Khi đã cài đặt (`isInstalled = true`) -> render `null`.
    - Khi là Mobile Android (`isMobile = true`, `isInstalled = false`, `isIos = false`) -> render banner, bấm nút gọi `promptInstall()`.
    - Khi là Mobile iOS (`isMobile = true`, `isInstalled = false`, `isIos = true`) -> render banner, bấm nút mở modal hướng dẫn Safari.
