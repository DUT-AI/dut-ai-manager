# Feature Specification: PWA Mobile Install Top Banner

**Feature Branch**: `048-pwa-install-banner`

**Created**: 2026-11-04

**Status**: Ready for Planning

**Input**: User description: "Tôi muốn có 1 popup hiển thị nút tải xuống app pwa ở trên này như nút bật thông báo khi người dùng truy cập vào nhưng chưa tải app bằng web trên điện thoại", kèm ảnh banner top bar của thông báo push. Người dùng xác nhận: Hỗ trợ tất cả các dòng điện thoại phổ biến (iPhone/iPad mọi đời, Samsung, Xiaomi, Oppo, Vivo, Pixel, v.v.), chỉ hiển thị trên điện thoại di động (Mobile/Tablet), xếp tầng cùng lúc với thanh Bật thông báo, và người dùng chỉ có duy nhất lựa chọn tải về (không có nút "Để sau").

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Thanh Banner cài đặt PWA trên đầu trang cho Android / Chromium Mobile (Priority: P1)

Khi người dùng mở hệ thống DUT AI Manager bằng trình duyệt web trên điện thoại di động hoặc máy tính bảng (như Chrome, Samsung Internet, Edge trên Android) mà chưa cài đặt ứng dụng PWA, một thanh banner xuất hiện ở vị trí trên cùng của màn hình (tương tự kiểu dáng của thanh Bật thông báo đẩy hiện tại). Thanh banner chứa icon ứng dụng, thông điệp hướng dẫn cài đặt và duy nhất nút hành động nổi bật "Cài đặt ngay" (hoặc "Tải app"). Không có nút "Để sau", banner hiển thị cố định nhằm khuyến khích 100% người dùng di động cài đặt app. Khi người dùng chạm vào "Cài đặt ngay", trình duyệt kích hoạt hộp thoại cài đặt PWA gốc của hệ điều hành. Sau khi cài đặt thành công, banner tự động biến mất.

**Why this priority**: Đảm bảo người dùng di động cài đặt ứng dụng vào màn hình chính để tối ưu hóa hiệu năng, nhận diện thương hiệu và nhận thông báo mượt mà.

**Independent Test**: Mở trình duyệt web trên thiết bị di động Android ở chế độ chưa cài app, xác nhận thanh banner hiển thị trên cùng với duy nhất nút tải về. Bấm "Cài đặt ngay", hộp thoại cài đặt của trình duyệt xuất hiện. Sau khi cài đặt xong, banner tự động ẩn vĩnh viễn.

**Acceptance Scenarios**:

1. **Given** người dùng truy cập hệ thống từ trình duyệt di động Android và chưa cài đặt PWA, **When** trang tải xong, **Then** thanh banner cài đặt PWA xuất hiện ở đầu trang với duy nhất nút hành động "Cài đặt ngay".
2. **Given** thanh banner đang hiển thị, **When** người dùng chạm vào nút "Cài đặt ngay", **Then** trình duyệt kích hoạt hộp thoại xác nhận cài đặt PWA chuẩn.
3. **Given** người dùng xác nhận cài đặt trong hộp thoại, **When** ứng dụng được cài thành công vào màn hình chính, **Then** thanh banner lập tức biến mất vĩnh viễn trên thiết bị đó.

---

### User Story 2 - Hướng dẫn cài đặt trực quan cho người dùng iOS Safari Mobile (Priority: P1)

Trên hệ điều hành iOS (iPhone/iPad), trình duyệt Safari không hỗ trợ API kích hoạt hộp thoại cài đặt tự động. Khi người dùng truy cập bằng Safari trên điện thoại di động iOS và thấy thanh banner cài đặt PWA trên cùng, chạm vào nút "Cài đặt ngay", hệ thống sẽ mở một popup/modal hướng dẫn ngắn gọn, trực quan (gồm biểu tượng nút Chia sẻ và dòng chữ "Thêm vào Màn hình chính").

**Why this priority**: Người dùng iPhone chiếm tỷ lệ lớn, việc cung cấp hướng dẫn trực quan là cách duy nhất giúp người dùng iOS đưa ứng dụng ra màn hình chính và nhận thông báo đẩy Web Push đầy đủ.

**Independent Test**: Truy cập bằng Safari trên iPhone chưa cài đặt PWA, bấm nút "Cài đặt ngay" trên thanh banner, một popup hướng dẫn 2 bước (Chia sẻ -> Thêm vào MH chính) xuất hiện rõ ràng.

**Acceptance Scenarios**:

1. **Given** người dùng truy cập bằng Safari trên thiết bị iOS chưa ở chế độ màn hình chính, **When** xem trang web, **Then** thanh banner PWA hiển thị ở đầu trang với nút "Cài đặt ngay".
2. **Given** người dùng chạm vào "Cài đặt ngay" trên iOS, **When** sự kiện bấm diễn ra, **Then** hệ thống mở popup hướng dẫn minh họa cụ thể cách nhấn nút "Chia sẻ" và "Thêm vào MH chính".
3. **Given** popup hướng dẫn đang mở, **When** người dùng đóng popup sau khi tham khảo, **Then** thanh banner trên đầu trang vẫn tiếp tục hiển thị để người dùng có thể mở lại hướng dẫn bất cứ lúc nào cho đến khi cài app thành công.

---

### User Story 3 - Xếp tầng hiển thị đồng thời cùng Push Notification Banner (Priority: P2)

Khi người dùng di động vừa chưa cài đặt app PWA vừa chưa bật thông báo đẩy Web Push, hệ thống sẽ xếp tầng hiển thị cả 2 thanh banner trên cùng màn hình (thanh PWA Install Banner và thanh PushBanner). Cả 2 banner được thiết kế đồng điệu về phong cách thị giác, bố cục gọn gàng, không che khuất thanh tiêu đề hay nội dung chính của ứng dụng.

**Why this priority**: Người dùng có thể tiếp cận cả 2 tính năng quan trọng (cài app và nhận thông báo) cùng lúc ngay từ đầu trang.

**Independent Test**: Đăng nhập tài khoản trên thiết bị di động mới (chưa cài app và chưa bật push), xác nhận cả 2 thanh banner hiển thị xếp tầng gọn gàng trên cùng trang web.

**Acceptance Scenarios**:

1. **Given** người dùng di động chưa cài PWA và chưa bật thông báo đẩy, **When** vào trang web, **Then** cả 2 thanh banner xuất hiện xếp tầng trên cùng một cách mượt mà và trực quan.
2. **Given** người dùng thực hiện bật thông báo thành công hoặc cài PWA thành công, **When** trạng thái tương ứng hoàn tất, **Then** chỉ thanh banner đó biến mất, thanh còn lại tiếp tục giữ vị trí chuẩn.

---

### User Story 4 - Tự động ẩn trên máy tính (Desktop) và khi ứng dụng đã được cài đặt (Priority: P3)

Thanh banner cài đặt PWA chỉ dành riêng cho điện thoại di động / máy tính bảng (Mobile/Tablet). Khi người dùng truy cập từ máy tính (Desktop/Laptop) hoặc khi đang mở ứng dụng từ màn hình chính ở chế độ PWA Standalone, thanh banner cài đặt PWA sẽ tự động ẩn hoàn toàn.

**Why this priority**: Tránh làm phiền người dùng máy tính và không hiển thị thừa thãi khi người dùng đã đang sử dụng app PWA độc lập.

**Independent Test**: Mở ứng dụng trên trình duyệt máy tính để bàn (Desktop), xác nhận không có banner cài đặt PWA nào xuất hiện.

**Acceptance Scenarios**:

1. **Given** người dùng truy cập từ trình duyệt máy tính (Desktop/Laptop), **When** duyệt bất kỳ trang nào, **Then** thanh banner cài đặt PWA không bao giờ hiển thị.
2. **Given** người dùng mở ứng dụng từ màn hình chính (ở chế độ Standalone PWA), **When** sử dụng ứng dụng, **Then** thanh banner cài đặt PWA không hiển thị.

---

### Edge Cases

- **Chế độ ẩn danh (Incognito/Private)**: Trình duyệt có thể hạn chế quyền cài PWA; nút "Cài đặt ngay" vẫn xử lý an toàn và không gây crash ứng dụng.
- **Người dùng mở link trong ứng dụng (In-App WebView như Zalo, Facebook Messenger trên iOS/Android)**: Trình duyệt nhúng không hỗ trợ Add to Home Screen trực tiếp; modal hướng dẫn trên iOS sẽ phát hiện và hướng dẫn thêm bước *"Bấm menu (•••) ở góc trên và chọn 'Mở bằng Safari / Trình duyệt' để cài đặt"*.
- **Người dùng bấm "Hủy" trong hộp thoại cài đặt của Android**: Hộp thoại đóng lại, banner PWA trên đầu trang vẫn tiếp tục hiển thị để người dùng có thể bấm cài đặt lại khi sẵn sàng.
- **Màn hình di động có kích thước nhỏ (Small Mobile Screens 320px - 375px)**: Văn bản và nút bấm trên thanh banner tự động co giãn linh hoạt hoặc rút gọn nhãn (ví dụ: "Tải app") để không bị tràn dòng hay vỡ giao diện.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI phát hiện chính xác tất cả các dòng điện thoại di động phổ biến (Apple iPhone/iPad mọi thế hệ; Android: Samsung Galaxy, Xiaomi/Redmi, OPPO, Vivo, Realme, Google Pixel, v.v.) và trạng thái PWA (đã cài đặt / đang ở chế độ Standalone hay đang chạy web).
- **FR-002**: Hệ thống PHẢI CHỈ hiển thị thanh banner cài đặt PWA trên các thiết bị di động (Mobile/Tablet) chưa cài đặt PWA; TUYỆT ĐỐI KHÔNG hiển thị trên máy tính (Desktop).
- **FR-003**: Thanh banner PHẢI được đặt ở vị trí trên cùng của ứng dụng (Top Banner), có phong cách thị giác tương đồng với thanh Bật thông báo đẩy hiện tại ([PushBanner](file:///Users/nguyenhuynh/Documents/dut-ai-manager/frontend/src/features/pwa/components/PushBanner.tsx)).
- **FR-004**: Thanh banner PHẢI chứa icon ứng dụng/tải xuống, thông điệp kêu gọi cài đặt ứng dụng, và DUY NHẤT một nút hành động chính "Cài đặt ngay" (hoặc "Tải app"); KHÔNG CÓ nút "Để sau" hay nút đóng (X).
- **FR-005**: Trên trình duyệt Chromium di động (Android Chrome, Edge, Samsung Internet, Cốc Cốc, Opera), khi người dùng nhấn "Cài đặt ngay", hệ thống PHẢI kích hoạt hộp thoại cài đặt native `beforeinstallprompt.prompt()`.
- **FR-006**: Trên trình duyệt iOS Safari di động, khi người dùng nhấn "Cài đặt ngay", hệ thống PHẢI hiển thị popup/modal hướng dẫn trực quan cách thêm vào màn hình chính (Chia sẻ -> Thêm vào Màn hình chính).
- **FR-007**: Nếu người dùng sử dụng trình duyệt Android không có sự kiện `beforeinstallprompt` (Firefox Mobile, Mi Browser nội địa) hoặc mở trong ứng dụng mạng xã hội (Zalo In-App WebView, Messenger, Facebook), hệ thống PHẢI có hướng dẫn fallback tương ứng để người dùng mở bằng Safari/Chrome hoặc thao tác menu 3 chấm.
- **FR-008**: Hệ thống PHẢI hỗ trợ hiển thị xếp tầng cùng lúc cả 2 thanh (PWA Install Banner và Push Notification Banner) trên đầu trang khi cả 2 điều kiện đều thỏa mãn.
- **FR-009**: Thanh banner PWA PHẢI duy trì hiển thị liên tục cho đến khi ứng dụng được cài đặt thành công hoặc đang chạy ở chế độ Standalone.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% người dùng truy cập web trên điện thoại chưa cài app đều nhìn thấy thanh banner cài đặt ở trên cùng màn hình.
- **SC-002**: 0% trường hợp thanh banner hiển thị trên máy tính (Desktop) hoặc trên app PWA đã cài đặt (Standalone Mode).
- **SC-003**: Người dùng có thể mở hộp thoại cài đặt hoặc xem hướng dẫn chỉ với 1 lần chạm vào nút "Cài đặt ngay".
- **SC-004**: Chiều cao thanh banner không vượt quá 48px trên màn hình di động tiêu chuẩn, đảm bảo tính thẩm mỹ và không gây cản trở trải nghiệm người dùng.

---

## Assumptions

- Ứng dụng đã có cấu hình `manifest.json` và Service Worker hợp lệ phục vụ PWA.
- Thiết bị di động được nhận diện dựa trên User Agent di động hoặc tính năng màn hình cảm ứng kết hợp viewport width (`max-width: 1024px`).
- Người dùng chỉ có duy nhất lựa chọn tải về để khuyến khích tối đa việc chuyển đổi sang app di động.
