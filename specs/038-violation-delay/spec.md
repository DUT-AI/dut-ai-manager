# Feature Specification: Lùi thời điểm quét vi phạm thêm 2 ngày (038-violation-delay)

**Feature Branch**: `038-violation-delay`  
**Created**: 2026-10-31  
**Status**: Ready for Planning  
**Input**: "Tôi muốn các job check để tạo vi phạm tăng thêm 2 ngày nữa so với hiện tại" + "tôi muốn làm rõ là không có gia hạn cho việc thực hiện trễ deadline, tạo vi phạm cho những task trễ so với deadline nhé"

---

## 1. Bối cảnh & Nguyên tắc Nghiệp vụ Bất biến

Hiện tại, hệ thống `dut-ai-manager` chạy các tác vụ nền định kỳ (background jobs) để tự động quét và tạo vi phạm (violation):
- **Bài tập (Homework)**: Quét vào 23:59 ngày deadline (`today`).
- **Điểm danh sinh hoạt (Meeting Attendance)**: Quét vào 23:59 ngày diễn ra buổi họp (`today`).
- **Trực nhật phòng Lab (Duty)**: Quét vào 23:59 ngày ca trực (`today`).
- **Đánh giá buổi học (Meeting Evaluation)**: Quét các buổi học đã kết thúc quá 24h.

### ⚠️ NGUYÊN TẮC BẤT BIẾN (Core Business Rule):
1. **TUYỆT ĐỐI KHÔNG GIA HẠN THỜI HẠN HOÀN THÀNH (NO EXTENSION FOR LATE SUBMISSION)**:
   - Mốc deadline ban đầu là mốc chốt (cut-off) duy nhất và tuyệt đối.
   - Bất kỳ thành viên nào thực hiện nhiệm vụ **TRỄ SO VỚI DEADLINE** (hoặc chưa hoàn thành trước deadline) **ĐỀU BỊ COI LÀ VI PHẠM VÀ PHẢI TẠO VI PHẠM**.
   - Nếu học viên nộp bài sau deadline (ví dụ: deadline ngày $T$, nộp vào ngày $T+1$), thì khi job quét, học viên đó **VẪN BỊ PHẠT VI PHẠM VÌ NỘP TRỄ DEADLINE**.
2. **Ý NGHĨA CỦA VIỆC TĂNG 2 NGÀY (JOB EXECUTION DELAY)**:
   - Tăng thêm 2 ngày ở đây **CHỈ LÀ ĐỘ TRỄ THỜI ĐIỂM CHẠY JOB QUÉT CỦA HỆ THỐNG** (System Scanning Delay / Cooldown Period), hoàn toàn không phải là ân hạn cho người dùng nộp bù.
   - Lý do kỹ thuật & vận hành: Để hệ thống có thời gian hoàn tất đồng bộ dữ liệu, ban quản trị đối soát, duyệt các đơn xin phép gửi trước đó; tránh việc vừa chạm mốc 23:59 là bot tự động phạt ngay lập tức trong đêm.
   - Khi job chạy vào ngày $T+2$, hệ thống quay lại kiểm tra tình trạng của ngày $T$ đối chiếu với đúng mốc deadline ngày $T$.

---

## 2. Kịch bản Người dùng & Kiểm thử (User Stories & Acceptance Scenarios)

### User Story 1 - Quét vi phạm bài tập trễ 2 ngày nhưng phạt toàn bộ task trễ deadline (Priority: P1)
Là ban quản trị, tôi muốn job quét bài tập chạy vào ngày $T+2$ đối với các bài tập có deadline là ngày $T$, và xử phạt nghiêm ngặt tất cả những ai chưa nộp hoặc nộp sau deadline $T$.

- **Độc lập kiểm thử**: 
  - Bài tập có deadline là 23:59 ngày $T$.
  - Job chạy vào 23:59 ngày $T$: KHÔNG quét bài tập hạn $T$ (chờ đến $T+2$).
  - Job chạy vào 23:59 ngày $T+2$: Quét bài tập hạn $T$. Những ai nộp sau deadline $T$ hoặc chưa nộp đều bị tạo vi phạm.
- **Kịch bản nghiệm thu**:
  1. **Given** bài tập có deadline 23:59 ngày 2026-10-25. Học viên A nộp vào lúc 08:00 ngày 2026-10-26 (nộp sau deadline).
     **When** job chạy vào 23:59 ngày 2026-10-27 (ngày $T+2$).
     **Then** hệ thống XÁC ĐỊNH học viên A vi phạm vì nộp trễ so với deadline và TẠO VI PHẠM.
  2. **Given** bài tập có deadline 23:59 ngày 2026-10-25. Học viên B nộp vào lúc 20:00 ngày 2026-10-25 (trước deadline).
     **When** job chạy vào 23:59 ngày 2026-10-27.
     **Then** hệ thống KHÔNG tạo vi phạm cho học viên B.
  3. **Given** bài tập có deadline hôm nay ($T$).
     **When** job chạy vào đêm hôm nay ($T$).
     **Then** hệ thống CHƯA quét bài tập hôm nay (đợi 2 ngày sau mới quét).

---

### User Story 2 - Quét vi phạm điểm danh cuộc họp trễ 2 ngày (Priority: P1)
Là ban quản trị, tôi muốn job quét điểm danh họp ngày $T$ được kích hoạt vào ngày $T+2$ để có đủ thời gian đối soát dữ liệu và đơn xin phép, nhưng vẫn phạt những ai không check-in hoặc check-in trễ mà không có phép tại buổi họp ngày $T$.

- **Độc lập kiểm thử**: Cuộc họp diễn ra ngày $T$. Job ngày $T+2$ quét lại cuộc họp ngày $T$. Ai vắng không phép hoặc trễ không phép trong buổi họp ngày $T$ đều bị tạo vi phạm.
- **Kịch bản nghiệm thu**:
  1. **Given** buổi họp diễn ra ngày 2026-10-25 có yêu cầu điểm danh. Thành viên không check-in và không có đơn xin vắng được duyệt.
     **When** job chạy vào 23:59 ngày 2026-10-27.
     **Then** hệ thống tạo vi phạm vắng sinh hoạt cho thành viên.
  2. **Given** buổi họp diễn ra ngày 2026-10-27 (hôm nay).
     **When** job chạy vào đêm 2026-10-27.
     **Then** hệ thống chưa quét buổi họp hôm nay.

---

### User Story 3 - Quét vi phạm trực nhật phòng Lab trễ 2 ngày (Priority: P1)
Là ban quản lý phòng Lab, tôi muốn ca trực nhật ngày $T$ được quét và chốt phạt vào ngày $T+2$. Nếu đến hạn 22:00 ngày $T$ ca trực không hoàn thành thì ca trực đó vẫn bị phạt, không chấp nhận nộp bù vào ngày $T+1$ hay $T+2$.

- **Độc lập kiểm thử**: Ca trực ngày $T$ có hạn 22:00 ngày $T$. Đến 22:00 ngày $T$ không nộp minh chứng. Dù ngày $T+1$ mới nộp thì ca trực đã quá hạn và khi job chạy ngày $T+2$ vẫn tạo vi phạm.
- **Kịch bản nghiệm thu**:
  1. **Given** ca trực nhật ngày 2026-10-25 không nộp minh chứng trước 22:00 ngày 2026-10-25.
     **When** job chạy vào ngày 2026-10-27.
     **Then** hệ thống tạo vi phạm cho các thành viên có mặt nhưng không hoàn thành trực nhật, và chuyển ca trực sang VIOLATED.
  2. **Given** ca trực nhật ngày hôm nay (2026-10-27).
     **When** job chạy vào 23:59 ngày hôm nay.
     **Then** hệ thống chưa xử lý phạt ca trực hôm nay.

---

### User Story 4 - Quét vi phạm đánh giá cuộc họp sau 72h (Priority: P2)
Là ban điều hành, thời điểm job quét phạt đánh giá cuộc họp được dời từ sau 24h thành sau 72h (tăng 2 ngày = 48h) tính từ lúc buổi học kết thúc. Khi quét, ai chưa hoàn thành đánh giá đều bị tạo vi phạm.

- **Độc lập kiểm thử**: Buổi họp kết thúc cách đây 48 tiếng: chưa bị quét phạt. Buổi họp kết thúc cách đây 73 tiếng: quét và tạo vi phạm cho Trainer/Trainee chưa hoàn tất đánh giá.
- **Kịch bản nghiệm thu**:
  1. **Given** buổi họp kết thúc lúc 10:00 ngày 2026-10-24 (cách hiện tại > 72h) và Trainee chưa nộp đánh giá Trainer.
     **When** job chạy vào 11:00 ngày 2026-10-27.
     **Then** hệ thống tạo vi phạm cho Trainee vì chưa hoàn thành đánh giá trong vòng 72h.
  2. **Given** buổi họp kết thúc lúc 10:00 ngày 2026-10-26 (cách hiện tại 25h).
     **When** job chạy vào 11:00 ngày 2026-10-27.
     **Then** hệ thống KHÔNG tạo vi phạm vì chưa đạt mốc 72h.

---

## 3. Các trường hợp biên (Edge Cases)

1. **Nộp bài tập sau deadline (Late Submissions)**:
   - Nếu học viên nộp bài sau deadline của bài tập: Trong cơ sở dữ liệu `HomeworkSubmissionModel.submitted_at > homework.deadline`.
   - Use Case `CheckOverdueHomeworkUseCase` PHẢI đảm bảo kiểm tra điều kiện `submitted_at <= homework.deadline`.
   - Nếu chỉ dựa vào Quiz API `completed-members` (vốn không có timestamp), một học viên nộp sau deadline có thể bị tính nhầm là hoàn thành. Do đó hệ thống phải kiểm tra thời gian nộp hoặc đối soát chính xác `submitted_at <= deadline`.
2. **Chạy thủ công với tham số `target_date`**:
   - Khi gọi `execute(target_date=date(2026, 10, 25))`, hệ thống quét chính xác ngày `2026-10-25` (không trừ thêm 2 ngày).
   - Chỉ khi `target_date is None` (chạy cron tự động), hệ thống mới lấy `target_date = today_vn - timedelta(days=2)`.
3. **Đơn xin hoãn / Đơn xin phép**:
   - Chỉ những đơn xin phép được gửi và có hiệu lực bao trùm thời điểm diễn ra sự kiện/deadline ban đầu mới được tính là có phép.

---

## 4. Yêu cầu Hệ thống (Requirements)

- **FR-001**: Hệ thống PHẢI định nghĩa hằng số độ trễ chạy job kiểm tra vi phạm `VIOLATION_CHECK_DELAY_DAYS = 2` và thời hạn đánh giá buổi học `MEETING_EVALUATION_DEADLINE_HOURS = 72`.
- **FR-002**: Job kiểm tra bài tập (`CheckOverdueHomeworkUseCase`) khi chạy tự động PHẢI quét các bài tập có deadline là `today - 2 ngày`. Chỉ những bài nộp có `submitted_at <= deadline` mới được công nhận là hợp lệ; nộp sau deadline vẫn bị coi là vi phạm.
- **FR-003**: Job kiểm tra điểm danh họp (`CheckMeetingAttendanceUseCase`) khi chạy tự động PHẢI quét các buổi họp diễn ra vào `today - 2 ngày`.
- **FR-004**: Job kiểm tra trực nhật (`CheckOverdueDutiesUseCase`) khi chạy tự động PHẢI quét các ca trực của `today - 2 ngày` và phạt nếu chưa hoàn thành trước 22:00 ngày trực.
- **FR-005**: Job kiểm tra đánh giá buổi học (`CheckEvaluationDeadlineJobUseCase`) PHẢI quét các buổi học đã kết thúc quá 72 giờ (`now - timedelta(hours=72)`).
- **FR-006**: Nội dung lý do vi phạm của đánh giá họp PHẢI được cập nhật thành "trong vòng 72h".

---

## 5. Tiêu chí Thành công (Success Criteria)

- **SC-001**: 100% các task hoàn thành sau deadline hoặc chưa hoàn thành tính đến mốc deadline ban đầu ĐỀU BỊ PHẠT khi job quét chạy ở ngày $T+2$.
- **SC-002**: Không có bất kỳ cơ chế gia hạn nộp bài hay tha phạt cho việc nộp trễ deadline nào được đưa vào hệ thống.
- **SC-003**: 100% automated tests pass (`backend/.venv/bin/pytest`).
