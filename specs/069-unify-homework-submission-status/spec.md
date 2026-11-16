# Feature Specification: Đồng bộ và Thống nhất Trạng thái Hoàn thành Bài tập giữa Học viên và Quản lý

**Feature Branch**: `069-unify-homework-submission-status`  
**Created**: 2026-11-15  
**Status**: Draft  
**Input**: User description: "Hiện tại tôi thấy có 1 vấn đề là UI đang my-homework và ui quản lý homework không đồng bộ thống nhất thông tin với nhau, học sinh chưa làm đủ bài tập bên QL bài tập hiển thị đúng nhưng my homework lại báo đủ, hãy kiểm tra lại cả BE và Fe giúp tôi"

---

## Bối cảnh và Vấn đề (Context & Problem Statement)

1. **Sự không nhất quán về trạng thái nộp bài giữa hai giao diện**:
   - Khi một bài học yêu cầu làm nhiều bài tập coding con (ví dụ: có 2 bài tập con $A$ và $B$), học sinh mới chỉ làm và nộp thành công 1 bài (tiến độ 1/2).
   - **Bên Quản lý bài tập (Giảng viên/Admin)**: Hệ thống hiển thị học sinh ở nhóm **"Chưa nộp"** (hoặc "Làm dở / Chưa hoàn thành đủ") vì số bài hoàn thành nhỏ hơn tổng số bài yêu cầu. Đây là logic nghiệp vụ chính xác.
   - **Bên Bài tập của tôi (Giao diện Học viên)**: Trang danh sách thẻ bài tập (`MyHomeworkPage`) lại hiển thị thẻ bài tập màu xanh lá với nhãn **"Đã hoàn thành" / "Đã nộp"**, đưa bài tập vào tab "Đã nộp" và loại bỏ khỏi tab "Chưa nộp". Tuy nhiên, khi học sinh nhấp vào xem chi tiết bài tập đó (`MyHomeworkDetailPage`), bên trong lại báo "Tiến độ 1/2 bài tập con - Chưa hoàn thành".

2. **Nguyên nhân cốt lõi**:
   - **Backend**: Cơ chế đánh giá bài nộp của thực thể bài tập (`evaluate_submissions`) khi trả về danh sách cho học viên (`GetUserHomeworksUseCase`) và danh sách bài chưa nộp (`GetUnsubmittedHomeworksForUserUseCase`, `GetUnsubmittedHomeworkReportUseCase`) chỉ kiểm tra xem học sinh có *bất kỳ* bài nộp coding nào đạt yêu cầu hay không (`any(...)`), thay vì đối chiếu xem học sinh đã hoàn thành *đầy đủ tất cả các bài tập coding con* được giao hay chưa.
   - **Frontend**: Thẻ bài tập (`HomeworkCard`) và bộ lọc danh sách (`MyHomeworkPage`) chỉ dựa vào cờ nhị phân `is_submitted`, chưa hỗ trợ nhận diện và phản ánh trạng thái "Làm dở / Hoàn thành một phần" (`PARTIALLY_SUBMITTED`). Dẫn đến việc thẻ bài tập đánh dấu học sinh đã hoàn thành 100% trong khi thực tế vẫn còn thiếu bài tập con.
   - **Hệ thống nhắc nhở / Cảnh báo trễ hạn**: Do đánh giá sai trạng thái nộp bài, hệ thống quét nhắc nhở cũng có nguy cơ bỏ qua các học sinh đang làm dở, khiến học sinh bị quá hạn mà không được cảnh báo đúng lúc.

---

## User Scenarios & Testing *(Bắt buộc)*

### User Story 1 - Học viên nhìn thấy chính xác trạng thái bài tập đang làm dở (Priority: P1)

Là một học viên, khi tôi mới chỉ hoàn thành một phần số bài tập con được giao (ví dụ hoàn thành 1/2 bài coding, hoặc đã làm coding nhưng chưa làm game trắc nghiệm), tôi muốn thấy bài tập được đánh dấu rõ ràng là "Chưa hoàn thành đủ" kèm theo tiến độ cụ thể trên màn hình "Bài tập của tôi", để tôi không bị lầm tưởng là mình đã làm xong hết bài tập.

**Why this priority**: Đây là điểm chạm trực tiếp gây hiểu lầm nghiêm trọng nhất cho sinh viên, khiến sinh viên tưởng đã nộp đủ và bị trễ hạn bài tập.

**Independent Test**:
- Giao cho một học viên bài tập gồm 2 bài coding con.
- Học viên nộp bài và vượt qua bài 1, chưa nộp bài 2.
- Vào trang "Bài tập của tôi" (`/dashboard/my-homeworks`):
  - Thẻ bài tập KHÔNG được hiển thị là "Đã hoàn thành" màu xanh.
  - Thẻ bài tập hiển thị trạng thái "Đang làm dở" (màu cam/cảnh báo) kèm tiến độ `1/2 bài tập coding`.
  - Bài tập nằm trong tab "Chưa hoàn thành / Cần làm" và thống kê vào số bài chưa xong.
  - Khi nhấp vào chi tiết bài tập, thông tin trạng thái khớp hoàn toàn 100% với thẻ bên ngoài.

**Acceptance Scenarios**:
1. **Given** bài tập có $N$ bài tập coding con ($N > 1$) và học sinh mới hoàn thành $K$ bài ($0 < K < N$), **When** học sinh xem danh sách bài tập của tôi, **Then** thẻ bài tập hiển thị trạng thái làm dở kèm tiến độ $K/N$, không được phép hiển thị nhãn "Đã hoàn thành".
2. **Given** bài tập yêu cầu cả bài tập Coding và Trắc nghiệm Game, **When** học sinh mới chỉ hoàn thành 1 trong 2 yêu cầu, **Then** thẻ bài tập hiển thị trạng thái chưa hoàn thành đủ, ghi rõ mục nào còn thiếu trong danh mục chưa nộp.
3. **Given** học sinh đã hoàn thành tất cả các bài tập con và trắc nghiệm game ($N/N$), **When** học sinh kiểm tra danh sách, **Then** thẻ bài tập mới chuyển sang trạng thái "Đã nộp" / "Đã hoàn thành" với tích xanh.

---

### User Story 2 - Thống nhất tiêu chí đánh giá giữa Giao diện Học viên và Giao diện Quản lý (Priority: P2)

Là một Quản trị viên/Giảng viên và Học viên, tôi muốn tiêu chí xác định bài tập "Đã nộp" vs "Chưa nộp" phải hoàn toàn đồng nhất giữa màn hình Quản lý bài tập và màn hình Học viên, để tránh việc giáo viên nhìn thấy học sinh chưa nộp nhưng học sinh lại khẳng định hệ thống báo đã nộp.

**Why this priority**: Đảm bảo sự tin cậy và minh bạch của dữ liệu học tập, tránh tranh chấp giữa giảng viên và học viên về việc hoàn thành bài tập.

**Independent Test**:
- Kiểm tra bài tập có 2 bài coding con với học sinh Đỗ Quảng Giác (mới nộp 1 bài).
- Màn hình Quản lý bài tập (`HomeworkDetailPage`): Học sinh nằm ở danh sách "Chưa hoàn thành coding" với tiến độ 1/2.
- Màn hình Học viên của học sinh đó (`MyHomeworkPage`): Bài tập nằm ở tab "Chưa hoàn thành" với tiến độ 1/2.
- Báo cáo thống kê chưa nộp (`HomeworkReportTab`): Học sinh được tính là chưa hoàn thành bài tập này.

**Acceptance Scenarios**:
1. **Given** một học sinh có tiến độ nộp bài chưa đạt 100%, **When** hệ thống xác định trạng thái bài tập của học sinh đó qua bất kỳ chức năng nào (danh sách học viên, báo cáo quản lý, danh sách cá nhân), **Then** tất cả các nơi đều cho ra cùng một kết quả là chưa hoàn thành.
2. **Given** học sinh lọc tab "Chưa nộp" trên màn hình cá nhân, **When** học sinh có bài tập đang làm dở, **Then** bài tập đó PHẢI xuất hiện trong tab "Chưa nộp", không biến mất khỏi danh sách cần xử lý.

---

### User Story 3 - Hệ thống nhắc nhở và tự động cảnh báo ghi nhận chính xác bài tập làm dở (Priority: P3)

Là một học viên, khi hạn chót bài tập sắp đến mà tôi vẫn chưa làm đủ toàn bộ các bài con yêu cầu, tôi muốn nhận được thông báo nhắc nhở làm nốt các bài còn thiếu, thay vì bị hệ thống bỏ quên do tưởng tôi đã nộp đủ.

**Why this priority**: Đảm bảo học viên được hỗ trợ tối đa về mặt kỷ luật học tập và không bị phạt vi phạm do thiếu sót bài tập.

**Independent Test**:
- Cấu hình một bài tập có deadline trong vòng 24 giờ tới, gồm 2 bài coding.
- Học viên mới hoàn thành 1 bài.
- Kích hoạt trình quét nhắc nhở (`HomeworkTaskScanner`).
- Hệ thống phải phát hiện bài tập này chưa hoàn thành trọn vẹn và tạo công việc nhắc nhở cho học viên với thông tin còn thiếu bài con.

**Acceptance Scenarios**:
1. **Given** bài tập sắp đến hạn mà học sinh chưa hoàn thành đủ 100% yêu cầu, **When** trình quét nhắc nhở chạy, **Then** hệ thống xác định đây là công việc chưa hoàn thành và tạo thông báo nhắc nhở tương ứng.

---

### Edge Cases

- **Bài tập dạng cũ hoặc không chia bài con** (không có danh mục bài tập con từ hệ thống Quiz): Nếu học sinh có bài nộp coding đạt (`is_passed = True`), hệ thống tính là hoàn thành coding.
- **Bài tập không yêu cầu Coding mà chỉ yêu cầu Game**: Trạng thái hoàn thành chỉ phụ thuộc vào kết quả Game Quiz (`game_is_submitted = True`).
- **Học sinh nộp nhiều lần cho một bài tập con**: Điểm số và trạng thái đạt của bài con đó được lấy theo lần nộp cao nhất/hợp lệ, không tính trùng lặp số lượng bài hoàn thành.
- **Bài tập vừa quá hạn vừa làm dở**: Bài tập phải hiển thị trạng thái "Quá hạn (Làm dở K/N)" với cảnh báo mức độ cao, giúp học viên và giáo viên nhận biết bài nộp trễ.
- **Danh sách bài con thay đổi từ phía Quiz**: Nếu một bài học được bổ sung thêm bài tập con mới trên Quiz, khi đồng bộ, hệ thống tự động cập nhật lại tổng số bài yêu cầu và điều chỉnh trạng thái hoàn thành của học sinh tương ứng.

---

## Requirements *(Bắt buộc)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI áp dụng một quy tắc đánh giá hoàn thành bài tập thống nhất cho mọi điểm truy cập (giao diện học viên, quản trị viên, báo cáo, và bot thông báo):
  - Bài tập yêu cầu Coding: Chỉ được coi là hoàn thành Coding khi học sinh vượt qua TẤT CẢ các bài tập coding con được yêu cầu. Nếu chỉ hoàn thành một phần ($0 < K < N$), trạng thái Coding là `PARTIALLY_SUBMITTED`.
  - Bài tập yêu cầu Game: Hoàn thành khi học sinh hoàn thành phiên chơi game đạt yêu cầu.
  - Bài tập chỉ được tính là `is_submitted = True` khi TẤT CẢ các thành phần bắt buộc (Coding và Game) đều đã hoàn thành 100%.
- **FR-002**: API danh sách bài tập của học viên (`GET /api/v1/homework/my-homeworks`) PHẢI cung cấp đầy đủ thông tin về tiến độ chi tiết của bài tập:
  - Tổng số bài coding con yêu cầu (`total_coding_required`).
  - Số bài coding con học sinh đã hoàn thành (`total_coding_completed`).
  - Trạng thái coding (`coding_status`: `COMPLETED`, `PARTIALLY_SUBMITTED`, `NOT_SUBMITTED`).
  - Danh sách các hạng mục chưa hoàn thành (`uncompleted_items`).
- **FR-003**: API danh sách bài tập chưa nộp của học viên (`GET /api/v1/homework/unsubmitted`) và báo cáo tổng hợp chưa nộp (`GET /api/v1/homework/reports/unsubmitted`) PHẢI bao gồm cả các bài tập đang ở trạng thái làm dở (`PARTIALLY_SUBMITTED`).
- **FR-004**: Giao diện thẻ bài tập (`HomeworkCard`) trên màn hình học viên PHẢI hiển thị trực quan 3 trạng thái rõ ràng:
  - **Đã hoàn thành** (Màu xanh / CheckCircle): Khi đã hoàn thành 100% tất cả yêu cầu.
  - **Đang làm dở / Chưa hoàn thành đủ** (Màu cam / Warning): Khi đã hoàn thành một phần (ví dụ $1/2$ bài coding, hoặc mới làm coding nhưng chưa làm game), hiển thị thanh tiến độ hoặc tag tiến độ (ví dụ: `1/2 bài coding`).
  - **Chưa nộp** (Màu trung tính hoặc Đỏ nếu quá hạn): Khi chưa nộp bất kỳ bài nào.
- **FR-005**: Màn hình "Bài tập của tôi" (`MyHomeworkPage`) PHẢI phân loại tab bộ lọc chính xác:
  - Tab "Chưa nộp": Chứa các bài chưa làm và các bài làm dở.
  - Tab "Đã nộp": Chỉ chứa các bài đã hoàn thành đầy đủ 100%.
  - Bộ đếm thống kê tổng quan (Thống kê số lượng bài) phải phản ánh đúng theo quy tắc này.
- **FR-006**: Trình quét nhắc nhở công việc (`HomeworkTaskScanner`) PHẢI áp dụng logic kiểm tra hoàn thành nghiêm ngặt, chỉ bỏ qua nhắc nhở khi học sinh đã hoàn thành 100% cả Coding và Game.

---

### Key Entities *(Dữ liệu liên quan)*

- **Homework (Bài tập)**: Thực thể chứa yêu cầu đề bài (tiêu đề, hạn nộp cá nhân, cờ yêu cầu coding, cờ yêu cầu game, danh mục các bài coding con).
- **HomeworkSubmission (Bài nộp bài tập)**: Bản ghi bài nộp của học sinh, gắn liền với mã bài tập con (`exercise_id`), loại bài nộp (`CODING` hoặc `GAME`), trạng thái đạt (`is_passed`) và điểm số.
- **SubmissionEvaluation (Kết quả đánh giá nộp bài)**: Đối tượng giá trị phản ánh tổng thể tiến độ nộp bài của một học viên cho một bài tập: `is_submitted`, `is_overdue`, `coding_status`, `total_coding_completed`, `total_coding_required`, `game_submitted`, `uncompleted_items`.

---

## Success Criteria *(Bắt buộc)*

### Measurable Outcomes

- **SC-001**: 100% các bài tập mà học sinh mới làm một phần ($K/N$ bài coding con với $K < N$) được hiển thị nhất quán ở trạng thái "Chưa hoàn thành / Làm dở" trên cả giao diện Học viên (`MyHomeworkPage`), Chi tiết học viên (`MyHomeworkDetailPage`) và Quản lý bài tập (`HomeworkDetailPage`).
- **SC-002**: Giảm 0% trường hợp mâu thuẫn dữ liệu: Không còn bất kỳ bài tập nào mà bên Quản lý báo "Chưa nộp" nhưng bên Học viên lại báo "Đã hoàn thành".
- **SC-003**: 100% bài tập làm dở được đưa vào danh mục "Chưa nộp" trong các bộ lọc và số liệu báo cáo của học viên và quản trị viên.
- **SC-004**: Thời gian phản hồi API danh sách bài tập của học viên không bị suy giảm (độ trễ dưới 200ms cho phân trang 20 bài tập) nhờ tối ưu hóa truy vấn gộp bài tập con và bài nộp từ cơ sở dữ liệu.

---

## Assumptions

- Danh mục bài tập coding con của bài học đã được đồng bộ và lưu trữ trong cơ sở dữ liệu hoặc có thể truy xuất từ các bài nộp đã ghi nhận của bài tập đó.
- Tiêu chí hoàn thành của Game Quiz vẫn giữ nguyên: Học sinh hoàn thành phiên chơi game (`is_completed = true` / `is_passed = true`) là đạt yêu cầu phần Game.
- Quy định hoàn thành Coding: Toàn bộ bài tập coding con chính thức của bài học phải đạt trạng thái `is_passed = True` thì phần Coding mới được tính là `COMPLETED`.
