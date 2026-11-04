import { useEffect, useState } from 'react';

export type PwaInstallStrategy = 'native_prompt' | 'ios_safari' | 'android_manual' | 'in_app_browser';

interface BeforeInstallPromptEvent extends Event {
  readonly platforms: string[];
  readonly userChoice: Promise<{
    outcome: 'accepted' | 'dismissed';
    platform: string;
  }>;
  prompt(): Promise<void>;
}

export function usePwaInstall() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [isInstallable, setIsInstallable] = useState(false);
  const [isInstalled, setIsInstalled] = useState(false);
  const [isIos, setIsIos] = useState(false);
  const [isAndroid, setIsAndroid] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [isInAppBrowser, setIsInAppBrowser] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const userAgent = window.navigator.userAgent.toLowerCase();

    // 1. Kiểm tra môi trường hệ điều hành
    const isIosDevice = /iphone|ipad|ipod/.test(userAgent);
    const isAndroidDevice = /android/.test(userAgent);
    setIsIos(isIosDevice);
    setIsAndroid(isAndroidDevice);

    // 2. Kiểm tra in-app browser (Zalo, Facebook, Messenger, Instagram, TikTok...)
    const inApp = /fban|fbav|instagram|messenger|zalo|tiktok|bytedance|line|twitter|micromessenger/.test(userAgent);
    setIsInAppBrowser(inApp);

    // 3. Kiểm tra thiết bị di động toàn diện (Universal Mobile / Tablet Detection)
    const isMobileUA = /android|iphone|ipad|ipod|blackberry|iemobile|opera mini|mobile|silk|kindle|fennec|lumia|samsung|huawei|xiaomi|redmi|oppo|realme|vivo/.test(
      userAgent
    );
    const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    const isMobileViewport = window.matchMedia('(max-width: 1024px)').matches;
    const isMobileDetected = isMobileUA || (hasTouch && isMobileViewport);
    setIsMobile(isMobileDetected);

    // 4. Kiểm tra xem ứng dụng đã ở chế độ Standalone (đã cài đặt) chưa
    const isStandaloneMode =
      window.matchMedia('(display-mode: standalone)').matches ||
      ('standalone' in window.navigator && Boolean((window.navigator as { standalone?: boolean }).standalone)) ||
      document.referrer.includes('android-app://');

    setIsInstalled(isStandaloneMode);

    // 5. Lắng nghe sự kiện beforeinstallprompt (Chrome / Android / Edge / Samsung Internet / Cốc Cốc)
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e as BeforeInstallPromptEvent);
      setIsInstallable(true);
    };

    // 6. Lắng nghe sự kiện appinstalled
    const handleAppInstalled = () => {
      setIsInstalled(true);
      setIsInstallable(false);
      setDeferredPrompt(null);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);

  const promptInstall = async (): Promise<boolean> => {
    if (!deferredPrompt) {
      return false;
    }

    try {
      await deferredPrompt.prompt();
      const choiceResult = await deferredPrompt.userChoice;
      if (choiceResult.outcome === 'accepted') {
        setIsInstalled(true);
        setIsInstallable(false);
        setDeferredPrompt(null);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Lỗi khi kích hoạt cài đặt PWA:', error);
      return false;
    }
  };

  // Xác định chiến lược cài đặt tối ưu
  let installStrategy: PwaInstallStrategy = 'native_prompt';
  if (isInAppBrowser) {
    installStrategy = 'in_app_browser';
  } else if (isIos) {
    installStrategy = 'ios_safari';
  } else if (isAndroid && !isInstallable) {
    installStrategy = 'android_manual';
  }

  return {
    isMobile,
    isIos,
    isAndroid,
    isInAppBrowser,
    isInstallable,
    isInstalled,
    isStandalone: isInstalled,
    installStrategy,
    promptInstall,
  };
}
