/**
 * Service Worker: DUT AI Manager PWA
 * Quản lý vòng đời cài đặt, nhận Web Push và điều hướng khi người dùng chạm thông báo.
 */

self.addEventListener('install', (event) => {
  // Kích hoạt ngay Service Worker mới mà không cần đợi đóng tab cũ
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  // Giành quyền kiểm soát ngay lập tức mọi clients/tabs đang mở
  event.waitUntil(self.clients.claim());
});

self.addEventListener('push', (event) => {
  let data = {
    title: 'DUT AI Manager',
    body: 'Bạn có thông báo mới từ hệ thống.',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/icon-192x192.png',
    tag: 'dutai-notification',
    data: { url: '/dashboard/notifications' },
  };

  if (event.data) {
    try {
      const parsedData = event.data.json();
      data = { ...data, ...parsedData };
    } catch (e) {
      console.warn('Lỗi parse JSON payload từ push event, dùng text thô:', e);
      data.body = event.data.text() || data.body;
    }
  }

  console.log('[Service Worker] Đã nhận sự kiện push, đang hiển thị thông báo:', data);

  const options = {
    body: data.body,
    icon: data.icon || '/icons/icon-192x192.png',
    badge: data.badge || '/icons/icon-192x192.png',
    tag: data.tag || 'general-notification',
    renotify: true,
    requireInteraction: true,
    data: data.data || { url: '/dashboard/notifications' },
  };

  // Gửi thông điệp tới tất cả các tab đang mở để hiển thị in-app và log ra Console chính
  const notifyClientsPromise = self.clients
    .matchAll({ type: 'window', includeUncontrolled: true })
    .then((clients) => {
      clients.forEach((client) => {
        client.postMessage({
          type: 'PUSH_NOTIFICATION_RECEIVED',
          data: data,
        });
      });
    });

  const showNotificationPromise = self.registration
    .showNotification(data.title, options)
    .then(() => {
      console.log('[Service Worker] showNotification thành công!');
    })
    .catch((err) => {
      console.error('[Service Worker] showNotification thất bại:', err);
    });

  event.waitUntil(Promise.all([showNotificationPromise, notifyClientsPromise]));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  const targetUrl = event.notification.data && event.notification.data.url
    ? event.notification.data.url
    : '/dashboard/notifications';

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      // 1. Nếu đã có tab/cửa sổ đang mở, focus vào tab đó và điều hướng
      for (const client of clientList) {
        if ('focus' in client) {
          client.focus();
          if ('navigate' in client) {
            return client.navigate(targetUrl);
          }
          return;
        }
      }
      // 2. Nếu chưa có tab nào mở, mở cửa sổ mới
      if (self.clients.openWindow) {
        return self.clients.openWindow(targetUrl);
      }
    })
  );
});
