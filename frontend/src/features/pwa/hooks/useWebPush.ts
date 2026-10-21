import { useEffect, useState } from 'react';
import { pushService } from '../services/pushService';

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export function useWebPush() {
  const [permission, setPermission] = useState<NotificationPermission>('default');
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // 1. Kiểm tra tính năng Web Push có được hỗ trợ trên trình duyệt hay không
    const supported =
      typeof window !== 'undefined' &&
      'serviceWorker' in navigator &&
      'PushManager' in window &&
      'Notification' in window;

    setIsSupported(supported);

    if (supported) {
      setPermission(Notification.permission);
      checkExistingSubscription();
    }
  }, []);

  const checkExistingSubscription = async () => {
    try {
      if (!('serviceWorker' in navigator)) return;
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      setIsSubscribed(Boolean(subscription));
    } catch (err) {
      console.warn('Lỗi kiểm tra subscription hiện tại:', err);
    }
  };

  const subscribeToPush = async (): Promise<boolean> => {
    if (!isSupported) {
      return false;
    }

    setIsLoading(true);
    try {
      // 1. Yêu cầu cấp quyền thông báo từ người dùng
      const permResult = await Notification.requestPermission();
      setPermission(permResult);

      if (permResult !== 'granted') {
        setIsLoading(false);
        return false;
      }

      // 2. Lấy VAPID public key từ server
      const keyRes = await pushService.getPushPublicKey();
      if (!keyRes.is_success || !keyRes.data?.public_key) {
        throw new Error('Không lấy được VAPID public key từ server');
      }

      const convertedVapidKey = urlBase64ToUint8Array(keyRes.data.public_key);

      // 3. Đăng ký qua Service Worker PushManager
      const registration = await navigator.serviceWorker.ready;
      let subscription = await registration.pushManager.getSubscription();

      if (!subscription) {
        subscription = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: convertedVapidKey,
        });
      }

      // 4. Trích xuất p256dh và auth secret
      const subJson = subscription.toJSON();
      if (!subJson.endpoint || !subJson.keys?.p256dh || !subJson.keys?.auth) {
        throw new Error('Dữ liệu Push Subscription từ trình duyệt không hợp lệ');
      }

      // 5. Lưu subscription lên máy chủ
      await pushService.registerSubscription({
        endpoint: subJson.endpoint,
        keys: {
          p256dh: subJson.keys.p256dh,
          auth: subJson.keys.auth,
        },
        user_agent: window.navigator.userAgent,
      });

      setIsSubscribed(true);
      return true;
    } catch (error) {
      console.error('Lỗi khi đăng ký nhận Web Push:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const unsubscribeFromPush = async (): Promise<boolean> => {
    if (!isSupported) return false;

    setIsLoading(true);
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      if (subscription) {
        const endpoint = subscription.endpoint;
        await subscription.unsubscribe();
        await pushService.unregisterSubscription(endpoint);
      }
      setIsSubscribed(false);
      return true;
    } catch (error) {
      console.error('Lỗi khi hủy đăng ký Web Push:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    permission,
    isSubscribed,
    isSupported,
    isLoading,
    subscribeToPush,
    unsubscribeFromPush,
  };
}
