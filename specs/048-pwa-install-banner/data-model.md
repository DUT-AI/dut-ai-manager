# Data Model: PWA Mobile Install Top Banner

## 1. Entities & UI State Models

Tính năng này hoàn toàn nằm ở tầng Frontend Presentation & Device Capabilities (Client-side), không yêu cầu database backend hay API endpoints lưu trữ trên máy chủ.

### PwaInstallState (State của hook `usePwaInstall`)

```typescript
export interface PwaInstallState {
  /**
   * Thiết bị có phải là điện thoại hoặc máy tính bảng (Mobile / Tablet) hay không.
   * Tính toán dựa trên User Agent regex và tính năng cảm ứng + viewport.
   */
  isMobile: boolean;

  /**
   * Thiết bị chạy hệ điều hành iOS (iPhone / iPad / iPod) hay không.
   */
  isIos: boolean;

  /**
   * Thiết bị chạy hệ điều hành Android (Samsung, Xiaomi, Oppo, Vivo, v.v.) hay không.
   */
  isAndroid: boolean;

  /**
   * Thiết bị đang mở trong In-App Browser (Zalo, Facebook, Messenger...).
   */
  isInAppBrowser: boolean;

  /**
   * Trình duyệt đã sẵn sàng cho sự kiện cài đặt native (Chromium beforeinstallprompt).
   */
  isInstallable: boolean;

  /**
   * Ứng dụng đã được cài đặt vào màn hình chính hoặc đang mở ở chế độ Standalone.
   */
  isInstalled: boolean;

  /**
   * Ứng dụng đang hiển thị toàn màn hình độc lập (Standalone PWA).
   */
  isStandalone: boolean;

  /**
   * Chiến lược cài đặt tối ưu cho thiết bị hiện tại:
   * - 'native_prompt': Android Chrome/Samsung Internet có beforeinstallprompt
   * - 'ios_safari': iPhone/iPad Safari (hướng dẫn nút Share)
   * - 'android_manual': Android không có beforeinstallprompt (hướng dẫn menu 3 chấm)
   * - 'in_app_browser': Mở trong Zalo/Facebook (hướng dẫn mở bằng Safari/Chrome)
   */
  installStrategy: 'native_prompt' | 'ios_safari' | 'android_manual' | 'in_app_browser';

  /**
   * Hàm kích hoạt hộp thoại cài đặt của trình duyệt (trên Chromium).
   */
  promptInstall: () => Promise<boolean>;
}
```

---

## 2. BeforeInstallPromptEvent (Browser Interface)

```typescript
export interface BeforeInstallPromptEvent extends Event {
  readonly platforms: string[];
  readonly userChoice: Promise<{
    outcome: 'accepted' | 'dismissed';
    platform: string;
  }>;
  prompt(): Promise<void>;
}
```

---

## 3. UI Component State (`PwaInstallBanner`)

```typescript
export interface PwaInstallBannerProps {
  className?: string;
}

export interface PwaInstallBannerInternalState {
  /**
   * Trạng thái mở/đóng modal hướng dẫn dành cho iOS Safari.
   */
  showIosModal: boolean;

  /**
   * Trạng thái đang kích hoạt prompt cài đặt (loading spinner).
   */
  isPrompting: boolean;
}
```

---

## 4. State Transition Matrix (Ma trận chuyển trạng thái hiển thị)

| Điều kiện Môi trường | `isMobile` | `isInstalled` | Trạng thái hiển thị Banner |
|---|---|---|---|
| Desktop (PC / Laptop Windows / macOS) | `false` | Bất kỳ | **ẨN (render null)** |
| Mobile đã cài app (Standalone mode) | `true` | `true` | **ẨN (render null)** |
| Mobile Android / Chrome chưa cài | `true` | `false` | **HIỂN THỊ** (Bấm gọi `promptInstall()`) |
| Mobile iOS / Safari chưa cài | `true` | `false` | **HIỂN THỊ** (Bấm mở Modal hướng dẫn iOS) |
| Sau khi Android user bấm đồng ý cài đặt | `true` | `true` | **TỰ ĐỘNG ẨN** sau event `appinstalled` |
