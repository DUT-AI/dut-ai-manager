# Feature Specification: Xây Dựng Lại Hệ Thống Theo Dõi Trạng Thái Hoàn Thành Bài Tập Học Viên

**Feature Branch**: `073-rebuild-homework-tracking`

**Created**: 2026-11-18

**Status**: Draft

**Input**: User description: "Hiện tại User đã làm hết bài tập rồi nhưng các thẻ bài tập ở https://manage.dutai.io.vn/dashboard/my-homeworks cứ hiện là chưa làm đủ, nếu đập đi xây lại phần này thì bạn sẽ làm gì để không bị bug nữa?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Hiển Thị Chính Xác Trạng Thái Hoàn Thành Bài Tập Trên Trang Bài Tập Của Tôi (Priority: P1)

Học viên truy cập trang "Bài tập của tôi" để kiểm tra toàn bộ bài tập được giao, biết chính xác bài nào đã hoàn thành trọn vẹn, bài nào đang làm dở (kèm tiến độ cụ thể từng hạng mục còn thiếu), bài nào chưa nộp, và bài nào đang quá hạn mà chưa làm xong. Khi học viên đã hoàn thành 100% các hạng mục yêu cầu của một bài tập (dù nộp đúng hạn hay nộp sau hạn), thẻ bài tập phải phản ánh trung thực là đã hoàn thành, không còn bị hiển thị sai thành "Chưa nộp" hay "Chưa làm đủ".

**Why this priority**: Đây là nguyên nhân cốt lõi gây mất niềm tin nghiêm trọng nhất hiện tại: học viên đã làm xong toàn bộ bài tập nhưng hệ thống vẫn liên tục báo "Chưa nộp" hoặc "Chưa làm đủ", gây hoang mang và phát sinh nhiều yêu cầu hỗ trợ không đáng có.

**Independent Test**: Có thể kiểm thử độc lập bằng cách giao cho học viên các bài tập với đủ tổ hợp yêu cầu (chỉ có lập trình gồm nhiều bài tập con, chỉ có trò chơi trắc nghiệm, hoặc kết hợp cả hai) và các mốc thời gian nộp (đúng hạn, trễ hạn, làm dở, chưa làm), sau đó mở trang "Bài tập của tôi" để xác minh nhãn trạng thái, tiến độ chi tiết và bộ đếm thống kê khớp 100% với thực tế làm bài.

**Acceptance Scenarios**:

1. **Given** học viên được giao một bài tập yêu cầu 3 bài tập con lập trình và đã nộp đạt cả 3 bài trước hạn nộp cá nhân, **When** học viên mở trang "Bài tập của tôi", **Then** thẻ bài tập hiển thị trạng thái "Đã hoàn thành" kèm dấu hiệu "Đúng hạn", hiển thị tiến độ lập trình 3/3 và không xuất hiện ở bộ lọc "Chưa hoàn thành" hay "Quá hạn".
2. **Given** học viên được giao một bài tập yêu cầu cả lập trình (2 bài tập con) và trò chơi trắc nghiệm, và học viên đã hoàn thành đạt 100% cả hai hạng mục nhưng có ít nhất một hạng mục hoàn thành sau hạn nộp cá nhân, **When** học viên mở trang "Bài tập của tôi", **Then** thẻ bài tập hiển thị trạng thái "Đã hoàn thành" kèm nhãn phụ "Nộp trễ" (không hiển thị là "Chưa nộp" hay "Chưa làm đủ"), và không xuất hiện trong danh sách bài tập chưa nộp.
3. **Given** học viên đã hoàn thành đạt tất cả các bài tập con lập trình trước hạn nộp, nhưng sau hạn nộp học viên tiếp tục nộp lại một bài tập con để cải thiện kết quả, **When** học viên mở trang "Bài tập của tôi", **Then** bài tập vẫn giữ nguyên trạng thái "Đã hoàn thành (Đúng hạn)" dựa trên mốc hoàn thành hợp lệ đầu tiên, không bị chuyển ngược thành "Nộp trễ" hay "Chưa nộp".
4. **Given** học viên chỉ mới nộp đạt 2 trên 3 bài tập con lập trình (hoặc đã xong lập trình nhưng chưa hoàn thành trò chơi trắc nghiệm), **When** học viên mở trang "Bài tập của tôi", **Then** thẻ bài tập hiển thị trạng thái "Đang làm dở" (nếu còn hạn) hoặc "Quá hạn (Làm dở)" (nếu đã qua hạn cá nhân), đồng thời liệt kê rõ hạng mục còn thiếu và số bài tập con đã đạt trên tổng số bài tập con bắt buộc chính thức.

---

### User Story 2 - Đồng Nhất 100% Trạng Thái Giữa Trang Chủ, Trang Bài Tập Của Tôi, Chi Tiết Bài Tập Và Báo Cáo Quản Trị (Priority: P1)

Khi học viên xem danh sách "Bài tập chưa nộp" ở Trang chủ, danh sách thẻ ở "Bài tập của tôi", trang "Chi tiết bài tập của tôi", hoặc khi quản trị viên xem "Trạng thái nộp bài" và "Báo cáo chưa nộp", mọi màn hình đều phải đọc từ cùng một nguồn đánh giá chính thức duy nhất và hiển thị hoàn toàn nhất quán về trạng thái hoàn thành, hạn nộp cá nhân, số bài tập con bắt buộc và số bài tập con đã đạt.

**Why this priority**: Hiện tại các màn hình đang sử dụng nhiều bộ quy tắc đánh giá và nhiều nguồn danh sách bài tập con khác nhau (nơi loại bỏ bài nộp trễ, nơi không loại bỏ; nơi lấy danh mục từ hệ thống chấm bài ngoài, nơi tự suy diễn từ lịch sử bài nộp), dẫn đến tình trạng cùng một học viên và cùng một bài tập nhưng màn hình chi tiết báo "Đã hoàn thành" còn Trang chủ và thẻ bài tập lại báo "Chưa nộp".

**Independent Test**: Có thể kiểm thử độc lập bằng cách kiểm tra cùng một học viên trên cả 4 góc nhìn (Trang chủ, Bài tập của tôi, Chi tiết bài tập của tôi, và màn hình Quản trị trạng thái nộp bài) cho cùng một tập bài tập và xác minh không có bất kỳ sai lệch nào về trạng thái hoàn thành, tổng số bài yêu cầu, số bài đã đạt, và hạn nộp cá nhân.

**Acceptance Scenarios**:

1. **Given** học viên đã hoàn thành 100% tất cả các bài tập được giao (bao gồm cả bài nộp đúng hạn và bài nộp trễ), **When** học viên mở Trang chủ, **Then** mục "Bài tập chưa nộp" hiển thị danh sách trống với thông báo chúc mừng đã hoàn thành tất cả bài tập.
2. **Given** học viên được gia hạn hạn nộp cá nhân muộn hơn hạn chung của lớp, **When** học viên mở trang "Bài tập của tôi" và bấm vào trang "Chi tiết bài tập của tôi", **Then** cả hai màn hình đều hiển thị chính xác hạn nộp cá nhân của học viên đó và đánh giá đúng hạn/trễ hạn theo đúng hạn cá nhân này.
3. **Given** học viên nộp đạt một bài tập con trên một bài tập có nhiều bài tập con, **When** so sánh tiến độ hiển thị ở thẻ bài tập trên trang "Bài tập của tôi", trang "Chi tiết bài tập của tôi" và bảng theo dõi của quản trị viên, **Then** cả ba nơi đều hiển thị cùng một tỷ lệ hoàn thành (ví dụ: 1/3 bài tập con) và cùng một trạng thái tổng thể.

---

### User Story 3 - Danh Mục Yêu Cầu Bài Tập Chính Thức Và Miễn Nhiễm Với Dữ Liệu Lỗi Hoặc Di Sản (Priority: P2)

Mỗi bài tập phải có một danh mục yêu cầu chính thức và tường minh (gồm các bài tập con lập trình bắt buộc cụ thể và yêu cầu trò chơi trắc nghiệm nếu có) được thiết lập từ nguồn bài tập gốc và được cập nhật rõ ràng khi cấu trúc đề bài thay đổi. Trạng thái hoàn thành của một học viên không bao giờ bị ảnh hưởng bởi bài nộp của học viên khác, các bản ghi nộp bài bị thiếu mã định danh, hoặc các bài tập con cũ đã bị gỡ khỏi đề bài.

**Why this priority**: Việc suy diễn danh sách bài tập con bắt buộc bằng cách gom tất cả mã bài tập xuất hiện trong lịch sử nộp bài của lớp khiến một bản ghi nộp bài lỗi (hoặc bản ghi di sản) làm tăng ảo số bài tập bắt buộc cho toàn bộ học viên trong lớp, khiến mọi học viên dù làm đủ vẫn vĩnh viễn bị báo "Chưa làm đủ".

**Independent Test**: Có thể kiểm thử độc lập bằng cách tạo một bài tập có đúng 2 bài tập con chính thức, đưa thêm các bản ghi nộp bài lỗi/di sản hoặc bài nộp của học viên khác không thuộc danh mục chính thức vào dữ liệu lịch sử, rồi kiểm tra học viên đã nộp đạt 2 bài tập con chính thức đó vẫn được đánh giá là "Đã hoàn thành" (2/2).

**Acceptance Scenarios**:

1. **Given** một bài tập có danh mục chính thức gồm 2 bài tập con lập trình, và trong lịch sử hệ thống có tồn tại các bản ghi nộp bài cũ không có mã bài tập con chuẩn hoặc thuộc một bài tập con đã bị xóa khỏi đề bài, **When** hệ thống đánh giá một học viên đã nộp đạt đúng 2 bài tập con chính thức, **Then** học viên được đánh giá đạt 2/2 ("Đã hoàn thành") và không bị cộng thêm yêu cầu ảo từ các bản ghi cũ.
2. **Given** một bài tập có 3 bài tập con lập trình và chưa có bất kỳ học viên nào trong lớp nộp bài, **When** học viên đầu tiên nộp đạt 1 bài tập con duy nhất, **Then** hệ thống hiển thị ngay tiến độ 1/3 ("Đang làm dở"), không báo nhầm "Đã hoàn thành" rồi sau đó tự đổi lại thành "Chưa làm đủ" khi học viên khác nộp bài tập con thứ hai.
3. **Given** giảng viên cập nhật hoặc đồng bộ lại bài tập từ hệ thống chấm bài ngoài (ví dụ thêm/bớt bài tập con hoặc bật/tắt yêu cầu trò chơi trắc nghiệm), **When** quá trình cập nhật hoàn tất, **Then** danh mục yêu cầu chính thức của bài tập được cập nhật theo cấu trúc mới nhất và trạng thái hoàn thành của các học viên được phản ánh chính xác ngay lập tức.

---

### User Story 4 - Lọc, Tìm Kiếm, Phân Trang Đầy Đủ Và Đồng Bộ Minh Bạch Trên Trang Bài Tập Của Tôi (Priority: P2)

Học viên có nhiều bài tập (vượt quá một trang hiển thị) vẫn xem được đầy đủ thống kê tổng quan, lọc chính xác theo từng nhóm trạng thái, tìm kiếm theo tên bài tập trên toàn bộ danh sách bài tập của mình, và chủ động yêu cầu đồng bộ lại kết quả mới nhất từ hệ thống chấm bài ngoài (cho từng bài hoặc toàn bộ các bài chưa hoàn thành) kèm phản hồi rõ ràng khi nghi ngờ dữ liệu chưa cập nhật kịp.

**Why this priority**: Hiện tại trang "Bài tập của tôi" chỉ nạp một trang dữ liệu cố định rồi tự đếm thống kê và tự lọc trên trình duyệt, khiến học viên có trên 20 bài tập bị ẩn mất bài tập cũ, số đếm sai lệch, và không biết dữ liệu đã được đồng bộ đến thời điểm nào.

**Independent Test**: Có thể kiểm thử độc lập bằng cách giao cho học viên hơn 25 bài tập thuộc nhiều trạng thái khác nhau, kiểm tra các thẻ thống kê tổng phản ánh đúng toàn bộ số lượng, chuyển đổi các tab lọc và tìm kiếm tìm thấy cả những bài nằm ngoài 20 bài đầu tiên, và bấm đồng bộ để thấy trạng thái cập nhật ngay lập tức.

**Acceptance Scenarios**:

1. **Given** học viên được giao 30 bài tập (gồm 22 bài đã hoàn thành, 5 bài chưa nộp/đang làm dở, 3 bài quá hạn chưa hoàn thành), **When** học viên mở trang "Bài tập của tôi", **Then** các thẻ thống kê tổng hiển thị chính xác 30 / 22 / 5 / 3 và người dùng có thể di chuyển qua các trang để xem đủ cả 30 bài.
2. **Given** học viên đang ở trang 2 hoặc có bài tập nằm ở vị trí thứ 25, **When** học viên chọn tab lọc "Chưa hoàn thành" hoặc nhập từ khóa tìm kiếm tên bài tập đó, **Then** hệ thống trả về đúng bài tập khớp điều kiện từ toàn bộ tập bài tập của học viên và đặt lại vị trí hiển thị về trang đầu tiên.
3. **Given** học viên vừa hoàn thành bài tập trên hệ thống chấm bài ngoài nhưng sự kiện cập nhật tự động bị chậm hoặc thất lạc, **When** học viên nhấn nút đồng bộ trên thẻ bài tập (hoặc nút đồng bộ trên trang "Bài tập của tôi"), **Then** hệ thống kéo lại cấu trúc đề bài và toàn bộ kết quả nộp bài mới nhất từ hệ thống chấm bài ngoài, cập nhật trạng thái ngay trên giao diện và hiển thị thông báo kết quả rõ ràng.

---

### User Story 5 - Bảo Toàn Lịch Sử Nộp Bài Và Quy Tắc Xét Vi Phạm Kỷ Luật Công Bằng (Priority: P3)

Hệ thống phải lưu giữ toàn vẹn các lượt nộp bài riêng biệt (không ghi đè làm mất mốc nộp đúng hạn trước đó) để vừa hiển thị lịch sử làm bài minh bạch cho học viên, vừa đảm bảo cơ chế kiểm tra vi phạm tự động đánh giá chính xác ai thực sự chưa hoàn thành trước hạn và ai đã hoàn thành đúng hạn.

**Why this priority**: Hành vi ghi đè thời gian nộp bài khi học viên nộp lại khiến học viên đã làm xong đúng hạn bị mất dấu mốc đúng hạn và có nguy cơ bị báo chưa nộp hoặc bị ghi nhận vi phạm oan.

**Independent Test**: Có thể kiểm thử độc lập bằng cách mô phỏng một học viên nộp đạt bài tập trước hạn, sau đó nộp thêm một lần đạt (hoặc không đạt) sau hạn, rồi xác minh: (a) cả hai lượt nộp đều được bảo toàn trong lịch sử, (b) bài tập vẫn được tính là hoàn thành đúng hạn, và (c) kiểm tra vi phạm quá hạn không tạo vi phạm cho học viên này.

**Acceptance Scenarios**:

1. **Given** học viên đã nộp đạt một bài tập con trước hạn nộp, **When** học viên nộp lại chính bài tập con đó sau hạn nộp (dù lần nộp lại đạt điểm cao hơn hay không đạt), **Then** lượt nộp mới được ghi nhận là một lần nộp riêng trong lịch sử, không xóa hoặc ghi đè thời gian của lượt nộp đạt trước hạn.
2. **Given** một bài tập đã quá hạn và hệ thống chạy kiểm tra vi phạm kỷ luật, **When** xét hai học viên — Học viên A đã hoàn thành đủ tất cả hạng mục trước hạn rồi nộp lại cải thiện sau hạn, Học viên B chỉ hoàn thành đủ sau hạn, **Then** Học viên A không bị ghi nhận vi phạm; Học viên B vẫn được hiển thị là "Đã hoàn thành (Nộp trễ)" trên giao diện học viên nhưng vẫn bị đánh dấu là chưa hoàn thành đúng hạn khi xét vi phạm theo quy định.

---

### Edge Cases

- **Bài tập không có danh mục bài tập con từ hệ thống chấm bài ngoài**: Xảy ra khi bài tập không liên kết với hệ thống chấm bài ngoài, liên kết sai định dạng, hoặc bài tập chỉ yêu cầu trò chơi trắc nghiệm. Hệ thống phải phân biệt rõ giữa "không yêu cầu lập trình" (không đòi hỏi bài tập con lập trình) và "có yêu cầu lập trình nhưng danh mục chưa có bài tập con nào" (chỉ cần có ít nhất một lượt nộp lập trình đạt hợp lệ, đồng thời cảnh báo quản trị viên nếu bài tập thiếu liên kết/danh mục).
- **Bài tập tắt cả hai tùy chọn yêu cầu (không lập trình, không trò chơi)**: Hệ thống phải ngăn chặn ngay từ lúc tạo/cập nhật bài tập rằng mỗi bài tập phải có ít nhất một hạng mục yêu cầu hợp lệ; với dữ liệu cũ đã lỡ tồn tại thì áp dụng quy tắc mặc định thống nhất là yêu cầu lập trình trên mọi màn hình.
- **Lượt nộp bài thất bại sau khi đã đạt**: Nếu học viên đã nộp đạt một bài tập con (hoặc đã hoàn thành trò chơi trắc nghiệm) rồi nộp thêm một lượt mới không đạt, trạng thái hoàn thành của hạng mục đó không bị hạ xuống "Chưa đạt".
- **Trò chơi trắc nghiệm bị lỗi điểm hoặc chưa hoàn tất phiên chơi**: Chỉ các lượt chơi được ghi nhận hoàn thành đạt mới tính là đã xong phần trò chơi; các lượt chơi bỏ dở giữa chừng vẫn có thể xem trong lịch sử nhưng không được tính là đã hoàn thành.
- **Hệ thống chấm bài ngoài tạm thời gián đoạn hoặc phản hồi chậm**: Khi học viên truy cập Trang chủ hoặc trang "Bài tập của tôi", hệ thống phải đọc hoàn toàn từ dữ liệu đã được đồng bộ và lưu trữ chính thức trong hệ thống (không bị treo hoặc biến bài đã nộp thành chưa nộp khi hệ thống ngoài mất kết nối). Khi học viên chủ động bấm đồng bộ lúc hệ thống ngoài gặp sự cố, hệ thống giữ nguyên dữ liệu hiện có và hiển thị thông báo lỗi thân thiện.
- **Thay đổi danh mục bài tập con sau khi học viên đã nộp**: Nếu giảng viên gỡ bỏ một bài tập con khỏi đề bài và đồng bộ lại, học viên đã hoàn thành tất cả các bài tập con còn lại phải được cập nhật ngay thành "Đã hoàn thành". Nếu giảng viên thêm một bài tập con mới bắt buộc, học viên chưa làm bài mới sẽ chuyển sang "Đang làm dở" kèm chỉ rõ đúng tên bài tập con mới còn thiếu.
- **Hạn nộp cá nhân bị thay đổi (gia hạn)**: Khi học viên được duyệt xin gia hạn bài tập, toàn bộ trạng thái đúng hạn / nộp trễ / quá hạn phải lập tức phản ánh theo hạn nộp cá nhân mới (ví dụ: bài trước đó bị đánh dấu "Nộp trễ" hoặc "Quá hạn" nhưng thực tế đã nộp trước hạn mới phải chuyển thành "Đã hoàn thành (Đúng hạn)").
- **Bài tập đã bị xóa (xóa mềm) hoặc học viên bị gỡ khỏi danh sách được giao**: Không xuất hiện trong danh sách bài tập của học viên, bộ đếm thống kê và mục "Bài tập chưa nộp" ở Trang chủ.
- **Đồng bộ lặp lại nhiều lần hoặc nhận sự kiện trùng lặp**: Nếu hệ thống nhận cùng một lượt nộp nhiều lần từ sự kiện tự động và đồng bộ thủ công, hệ thống phải tự động khử trùng lặp chính xác, không tạo ra nhiều bản ghi giống hệt nhau và không làm sai lệch số lượng bài đã đạt.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI tách bạch hoàn toàn hai khái niệm độc lập khi đánh giá bài tập của mỗi học viên:
  1. **Trạng thái hoàn thành**: `Chưa bắt đầu`, `Đang làm dở`, hoặc `Đã hoàn thành` (dựa trên việc học viên đã đạt đủ 100% các hạng mục bắt buộc hay chưa, không loại bỏ bài nộp chỉ vì nộp sau hạn).
  2. **Trạng thái đúng hạn**: `Đúng hạn` (đạt đủ 100% hạng mục với mốc đạt đầu tiên của từng hạng mục đều không vượt quá hạn nộp cá nhân), `Nộp trễ` (đã đạt đủ 100% hạng mục nhưng có ít nhất một hạng mục có mốc đạt đầu tiên sau hạn nộp cá nhân), `Còn hạn` (chưa đạt đủ 100% và thời điểm hiện tại chưa vượt quá hạn nộp cá nhân), hoặc `Quá hạn` (chưa đạt đủ 100% và thời điểm hiện tại đã vượt quá hạn nộp cá nhân).

- **FR-002**: Hệ thống PHẢI duy trì một **danh mục hạng mục yêu cầu chính thức** thuộc sở hữu trực tiếp của từng bài tập (bao gồm danh sách các bài tập con lập trình bắt buộc có mã định danh và tiêu đề rõ ràng, cùng cờ yêu cầu trò chơi trắc nghiệm). Danh mục này được khởi tạo khi tạo bài tập và cập nhật tường minh khi chỉnh sửa hoặc đồng bộ bài tập từ hệ thống chấm bài ngoài.

- **FR-003**: Hệ thống KHÔNG ĐƯỢC tự suy diễn danh sách bài tập con bắt buộc bằng cách tổng hợp các mã bài tập xuất hiện trong bảng lịch sử nộp bài của học viên. Các bản ghi nộp bài cũ, thiếu mã bài tập con chuẩn hoặc thuộc bài tập con không còn nằm trong danh mục chính thức KHÔNG ĐƯỢC làm tăng số lượng bài tập bắt buộc của bài tập.

- **FR-004**: Hệ thống PHẢI bảo toàn đầy đủ từng lượt nộp bài theo dạng lịch sử chỉ ghi thêm, không ghi đè làm mất mốc thời gian hợp lệ (kèm cơ chế chống trùng lặp theo mã định danh của lượt nộp). Khi một hạng mục có nhiều lượt nộp, hệ thống PHẢI xác định:
  - Hạng mục đã hoàn thành nếu tồn tại **ít nhất một** lượt nộp đạt yêu cầu.
  - Mốc hoàn thành để xét đúng hạn là **thời điểm sớm nhất** trong số các lượt nộp đạt của hạng mục đó (nộp lại sau hạn để cải thiện hoặc thử nghiệm không bao giờ làm mất trạng thái "Đúng hạn" đã đạt được trước đó).

- **FR-005**: Hệ thống PHẢI áp dụng **một bộ quy tắc đánh giá thống nhất duy nhất** tại hệ thống trung tâm và cung cấp trực tiếp kết quả đã đánh giá (trạng thái hoàn thành, trạng thái đúng hạn, tiến độ chi tiết từng bài tập con và trò chơi, danh sách hạng mục còn thiếu, hạn nộp cá nhân) cho toàn bộ các điểm hiển thị:
  - Mục "Bài tập chưa nộp" và bộ đếm ở Trang chủ.
  - Danh sách thẻ bài tập và thống kê ở trang "Bài tập của tôi".
  - Trang "Chi tiết bài tập của tôi".
  - Màn hình quản trị trạng thái nộp bài và báo cáo tổng hợp.

- **FR-006**: Giao diện học viên KHÔNG ĐƯỢC tự tính toán lại hay suy diễn chắp vá trạng thái hoàn thành, trạng thái quá hạn, hoặc kết hợp thủ công nhiều danh sách riêng lẻ để đoán bài nào đã nộp/chưa nộp. Mọi nhãn trạng thái, số đếm và tiến độ hiển thị phải lấy trực tiếp từ kết quả đánh giá thống nhất do hệ thống trung tâm cung cấp.

- **FR-007**: Mục "Bài tập chưa nộp" ở Trang chủ và bộ lọc "Chưa hoàn thành" ở trang "Bài tập của tôi" CHỈ hiển thị các bài tập có trạng thái hoàn thành là `Chưa bắt đầu` hoặc `Đang làm dở`. Bài tập đã đạt trạng thái `Đã hoàn thành` (bao gồm cả `Đã hoàn thành - Nộp trễ`) PHẢI được loại khỏi danh sách "Chưa nộp" và xuất hiện trong nhóm "Đã hoàn thành" kèm nhãn phân biệt "Đúng hạn" hoặc "Nộp trễ".

- **FR-008**: Hệ thống kiểm tra vi phạm quá hạn tự động PHẢI tiếp tục đánh giá nghiêm ngặt theo **mốc hoàn thành đúng hạn** (sử dụng cùng nguồn đánh giá thống nhất: nếu bài tập chưa đạt trạng thái `Đã hoàn thành - Đúng hạn` sau khi hết hạn nộp cá nhân thì mới ghi nhận vi phạm nộp thiếu/nộp trễ theo quy định kỷ luật).

- **FR-009**: Trang "Bài tập của tôi" PHẢI hỗ trợ thống kê tổng quan chính xác trên **toàn bộ** bài tập được giao cho học viên (không bị giới hạn bởi kích thước một trang hiển thị), đồng thời hỗ trợ lọc theo trạng thái (`Tất cả`, `Chưa hoàn thành`, `Đã hoàn thành`, `Quá hạn`), tìm kiếm theo tên bài tập và phân trang đầy đủ trên toàn bộ tập dữ liệu của học viên.

- **FR-010**: Trang "Chi tiết bài tập của tôi" PHẢI hiển thị đúng **hạn nộp cá nhân** của học viên đang đăng nhập (không dùng hạn nộp chung hay hạn sớm nhất của học viên khác), kèm danh sách từng bài tập con bắt buộc và trạng thái riêng của từng bài con (chưa nộp / đạt đúng hạn / đạt trễ hạn / chưa đạt) cùng toàn bộ lịch sử các lần nộp.

- **FR-011**: Học viên PHẢI có thể kích hoạt đồng bộ kết quả từ hệ thống chấm bài ngoài trên từng bài tập chưa hoàn thành (hoặc đồng bộ nhanh các bài chưa hoàn thành trên trang "Bài tập của tôi"), và hệ thống phải cập nhật đồng thời cả danh mục yêu cầu bài tập mới nhất lẫn các lượt nộp bài mới nhất, kèm phản hồi rõ ràng về số bản ghi cập nhật hoặc lý do nếu đồng bộ thất bại.

- **FR-012**: Khi hệ thống cập nhật dữ liệu từ hệ thống chấm bài ngoài (qua sự kiện tự động hoặc đồng bộ thủ công), hệ thống PHẢI tôn trọng kết quả đạt/không đạt thực tế từ hệ thống chấm bài ngoài (không tự động đánh dấu tất cả các lượt nộp lập trình là đạt nếu thực tế lượt nộp đó chưa vượt qua kiểm thử/chưa đạt tiêu chuẩn).

- **FR-013**: Hệ thống PHẢI lưu trữ và hiển thị mốc thời gian đồng bộ gần nhất của bài tập (nếu có) để học viên và quản trị viên nhận biết độ mới của dữ liệu.

- **FR-014**: Hệ thống PHẢI cung cấp cơ chế chuyển đổi và làm sạch dữ liệu hiện có một lần để đồng bộ danh mục bài tập con chính thức cho toàn bộ các bài tập đang hoạt động và chuẩn hóa lại các bản ghi nộp bài hiện có, đảm bảo ngay sau khi triển khai lại thì các bài tập học viên đã làm xong trước đó lập tức hiển thị chính xác.

### Key Entities

- **Bài tập (Homework)**: Đại diện cho một nhiệm vụ bài tập được giao, chứa thông tin chung (tiêu đề, liên kết/định danh trên hệ thống chấm bài ngoài, yêu cầu lập trình, yêu cầu trò chơi trắc nghiệm, mốc đồng bộ gần nhất) và sở hữu trực tiếp danh mục bài tập con bắt buộc chính thức.
- **Bài tập con bắt buộc (Required Coding Exercise)**: Thành phần trực thuộc một Bài tập, định nghĩa chính thức từng bài lập trình cần hoàn thành (mã định danh chuẩn từ hệ thống ngoài, tiêu đề, thứ tự hiển thị, trạng thái đang hiệu lực). Đây là nguồn chân lý duy nhất để tính tổng số bài lập trình bắt buộc.
- **Phân công bài tập cá nhân (Homework Assignment)**: Liên kết giữa một Bài tập và một Học viên cụ thể, sở hữu **hạn nộp cá nhân** (có thể được điều chỉnh riêng khi học viên xin gia hạn).
- **Lượt nộp bài (Submission Attempt)**: Bản ghi lịch sử bất biến về một lần nộp bài lập trình (gắn với mã bài tập con cụ thể) hoặc một phiên hoàn thành trò chơi trắc nghiệm của học viên, gồm định danh lượt nộp từ hệ thống ngoài (để chống trùng lặp), thời điểm nộp, kết quả đạt/không đạt, điểm số và chi tiết kết quả.
- **Kết quả đánh giá bài tập của học viên (Student Homework Evaluation)**: Kết quả tổng hợp duy nhất cho cặp (Học viên, Bài tập), chứa: trạng thái hoàn thành (`Chưa bắt đầu` / `Đang làm dở` / `Đã hoàn thành`), trạng thái đúng hạn (`Đúng hạn` / `Nộp trễ` / `Còn hạn` / `Quá hạn`), mốc hoàn thành hợp lệ đầu tiên, tiến độ từng bài tập con bắt buộc, trạng thái trò chơi trắc nghiệm và danh sách hạng mục còn thiếu.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% bài tập mà học viên đã hoàn thành đạt tất cả các hạng mục bắt buộc (cả nộp đúng hạn lẫn nộp trễ) đều hiển thị trạng thái "Đã hoàn thành" (kèm nhãn "Đúng hạn" hoặc "Nộp trễ" tương ứng) và không còn xuất hiện trong mục "Bài tập chưa nộp" ở Trang chủ hay bộ lọc "Chưa hoàn thành" ở trang "Bài tập của tôi".
- **SC-002**: 0% sai lệch (đồng nhất tuyệt đối 100%) về trạng thái hoàn thành, số bài tập con đã đạt trên tổng số bài yêu cầu, và hạn nộp cá nhân giữa 4 khu vực: Trang chủ, trang "Bài tập của tôi", trang "Chi tiết bài tập của tôi", và màn hình Quản trị trạng thái nộp bài.
- **SC-003**: 0 trường hợp học viên đã hoàn thành đúng hạn bị chuyển ngược thành "Nộp trễ", "Chưa nộp" hoặc bị ghi nhận vi phạm oan khi nộp lại bài sau hạn.
- **SC-004**: 0 trường hợp số lượng bài tập con bắt buộc của một bài tập bị tăng ảo bởi các bản ghi nộp bài lỗi, bản ghi di sản hoặc bài nộp của học viên khác.
- **SC-005**: 100% bài tập của học viên có trên 20 bài tập được hiển thị đầy đủ qua phân trang, với bộ đếm thống kê và kết quả lọc/tìm kiếm phản ánh chính xác trên toàn bộ dữ liệu thay vì chỉ một trang cục bộ.
- **SC-006**: Thời gian tải danh sách trang "Bài tập của tôi" dưới 1 giây trong điều kiện sử dụng thông thường (vì không phụ thuộc vào lời gọi thời gian thực tới hệ thống chấm bài ngoài khi chỉ xem danh sách), và giảm ít nhất 90% phản hồi báo lỗi sai trạng thái nộp bài từ học viên sau khi phát hành.

## Assumptions

- **Chính sách đối với bài nộp trễ nhưng đã làm đủ**: Theo chuẩn phổ biến của các hệ thống quản lý học tập (LMS), bài tập đã hoàn thành 100% sau hạn được phân loại là **"Đã hoàn thành (Nộp trễ)"** và rời khỏi danh sách "Chưa nộp" trên giao diện học viên để học viên biết mình đã xong bài; trong khi đó quy trình kiểm tra kỷ luật/vi phạm vẫn căn cứ vào tiêu chí **"hoàn thành đúng hạn"** để giữ nguyên tính công bằng của nội quy lớp học.
- **Phạm vi đồng nhất**: Dù vấn đề biểu hiện rõ nhất ở trang "Bài tập của tôi" và Trang chủ, việc xây dựng lại quy tắc đánh giá và danh mục bài tập con chính thức được áp dụng thống nhất cho toàn bộ phân hệ Bài tập (bao gồm cả Chi tiết bài tập, Báo cáo chưa nộp, Trạng thái nộp bài quản trị và Kiểm tra vi phạm tự động) để triệt tiêu hoàn toàn nguyên nhân lệch trạng thái giữa các màn hình.
- **Hệ thống chấm bài ngoài (Quiz)**: Hệ thống chấm bài ngoài có khả năng cung cấp danh sách bài tập con chính thức của một bài học cũng như kết quả đạt/không đạt, mã lượt nộp và mốc thời gian nộp của từng học viên.
- **Dữ liệu hiện hữu**: Cần chạy một bước đồng bộ chuẩn hóa một lần cho các bài tập đang hoạt động sau khi triển khai phiên bản mới để điền đầy đủ danh mục bài tập con chính thức và loại bỏ ảnh hưởng của các bản ghi di sản trước đó.
- **Quyền hạn người dùng**: Học viên chỉ xem và đồng bộ được các bài tập được giao cho chính mình; quản trị viên/giảng viên giữ nguyên quyền xem báo cáo tổng hợp và đồng bộ cho toàn bộ bài tập.
