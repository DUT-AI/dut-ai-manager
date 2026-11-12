# Feature Specification: Chatbot Trợ Lý Giải Đáp Vi Phạm & Vận Hành Cho Thành Viên và Ban Quản Trị

**Feature Branch**: `062-violation-faq-chatbot`

**Created**: 2026-11-12

**Status**: Draft

**Input**: User description: "Hiện tại tôi muốn thêm làm 1 trang chatbot cho các thành viên có thể đặt câu hỏi, trước mắt sẽ tập trung giải đáp về các lý do vi phạm, tôi nên tiếp cận theo hướng thiết kế như thế nào? Có cần công nghệ mới nhưng harness agent không? Tôi thấy phát triển tính năng dành cho ban quản trị vậy ok đó, hãy phát triển chi tiết hơn"

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Thành viên tra cứu & giải thích lý do vi phạm của chính mình (Priority: P1)

Thành viên sau khi nhận thông báo phạt hoặc thấy điểm phạt tăng lên muốn hiểu rõ nguyên nhân cụ thể: vi phạm xảy ra vào ngày nào, liên quan đến hoạt động nào (ví dụ: vắng buổi họp cụ thể, nộp bài tập muộn qua deadline, hay không điểm danh thiết bị), và quy chế áp dụng ra sao. Thành viên mở khung chat (từ trang riêng `/assistant` hoặc nút nổi ở góc màn hình) và đặt câu hỏi tự nhiên bằng tiếng Việt (ví dụ: "Tại sao tuần này tôi bị ghi nhận 2 vi phạm?", "Giải thích giúp tôi vi phạm ngày 10/11"). Chatbot sẽ trích xuất thông tin vi phạm thực tế của chính thành viên đó để giải thích rõ ràng, minh bạch và lịch sự.

**Why this priority**: Đây là giá trị cốt lõi nhất giải quyết nỗi đau trực tiếp của thành viên (không hiểu tại sao mình bị phạt, nghi ngờ hệ thống tính nhầm) và giảm tải 80% công sức trả lời thủ công của ban quản trị/HR.

**Independent Test**: Thành viên đăng nhập có sẵn ít nhất một bản ghi vi phạm trong hệ thống, mở khung chat, hỏi về vi phạm của mình và nhận được câu trả lời chính xác về thời gian, nội dung vi phạm và lý do tương ứng.

**Acceptance Scenarios**:

1. **Given** thành viên đã đăng nhập có 1 vi phạm do vắng buổi họp ngày 10/11/2026, **When** thành viên hỏi "Hôm trước tôi bị phạt vì lý do gì?", **Then** chatbot nhận diện đúng ngữ cảnh người dùng, trả lời chi tiết về sự kiện vi phạm ngày 10/11 và lý do vắng họp theo quy định.
2. **Given** thành viên chưa có vi phạm nào trong tháng hiện tại, **When** thành viên hỏi "Tôi có vi phạm nào gần đây không?", **Then** chatbot thông báo chúc mừng thành viên vì không có vi phạm nào trong khoảng thời gian được hỏi.
3. **Given** thành viên hỏi về vi phạm của một người khác (ví dụ: "Bạn A bị phạt gì thế?"), **Then** chatbot lịch sự từ chối vì lý do bảo mật và quyền riêng tư, giải thích rằng chỉ có thể hỗ trợ thông tin của chính thành viên đó.

---

### User Story 2 - Ban Quản trị / Mentor / HR tra cứu tổng hợp & giám sát học vụ (Priority: P2)

Người dùng có quyền quản trị (Admin, HR, Mentor, Trainer) cần nắm bắt nhanh bức tranh tổng thể về tình hình chấp hành nội quy và học vụ mà không phải điều hướng qua nhiều bảng dữ liệu và thiết lập các bộ lọc phức tạp. Khi đăng nhập vào chatbot, ban quản trị có thể đặt các câu hỏi tổng hợp như:
- *"Tổng hợp vi phạm tuần này của toàn CLB"*
- *"Liệt kê danh sách các bạn có từ 3 vi phạm trở lên trong tháng này để HR nhắc nhở"*
- *"Bài tập 'FastAPI Core' deadline tối nay còn những ai chưa nộp?"*
- *"Buổi họp hôm qua có những ai vắng không phép?"*

Chatbot nhận diện quyền quản trị của tài khoản, sử dụng bộ công cụ quản trị cấp cao để tổng hợp dữ liệu chính xác từ database và trả về câu trả lời súc tích kèm bảng tóm tắt rõ ràng.

**Why this priority**: Tăng năng suất vận hành của ban quản trị lên nhiều lần, hỗ trợ ra quyết định kịp thời (nhắc nhở trước deadline, rà soát thành viên có nguy cơ vi phạm cao) và giảm công việc tổng hợp báo cáo thủ công.

**Independent Test**: Người dùng đăng nhập bằng tài khoản có quyền quản trị (`violation:read`, `homework:read`), hỏi các câu hỏi tổng hợp và nhận được số liệu thống kê danh sách thành viên vi phạm / chưa nộp bài chính xác theo dữ liệu hệ thống.

**Acceptance Scenarios**:

1. **Given** người dùng có quyền quản trị vi phạm (`violation:read`), **When** người dùng hỏi "Tuần này có bao nhiêu vi phạm và ai bị phạt nhiều nhất?", **Then** chatbot tổng hợp số lượng vi phạm trong tuần và liệt kê danh sách top thành viên vi phạm kèm số lần tương ứng.
2. **Given** người dùng có quyền đào tạo (`homework:read`), **When** người dùng hỏi "Bài tập mới nhất còn những ai chưa nộp?", **Then** chatbot xác định bài tập gần nhất và liệt kê danh sách họ tên thành viên chưa hoàn thành bài tập.
3. **Given** thành viên thông thường (không có quyền quản trị), **When** cố gắng đặt câu hỏi tổng hợp (ví dụ: "Liệt kê danh sách tất cả người bị phạt tuần này"), **Then** hệ thống chặn quyền ở tầng công cụ và từ chối lịch sự, nêu rõ tài khoản không có quyền truy cập dữ liệu quản trị.

---

### User Story 3 - Hỏi đáp chính sách & quy chế vi phạm chung (Priority: P2)

Thành viên (đặc biệt là thành viên mới hoặc người chuẩn bị xin nghỉ/nộp bài muộn) cần tra cứu các điều khoản trong quy chế hoạt động: quy định giờ giấc điểm danh, thời hạn nộp bài tập, cách tính điểm trừ vi phạm, quy định xin phép hợp lệ để không bị tính vi phạm. Thành viên đặt câu hỏi về quy định (ví dụ: "Đến muộn bao nhiêu phút thì bị tính là trễ?", "Quy định xin phép vắng họp trước mấy tiếng?"). Chatbot trích xuất quy chế chuẩn và giải đáp súc tích kèm trích dẫn điều khoản liên quan.

**Why this priority**: Giúp thành viên chủ động nắm rõ quy định trước khi vi phạm xảy ra, thúc đẩy tính tự giác và tuân thủ nội quy chung.

**Independent Test**: Bất kỳ thành viên nào hỏi về chính sách đi trễ / vắng họp / nộp bài muộn đều nhận được trích dẫn chính xác theo quy chế hiện hành của tổ chức.

**Acceptance Scenarios**:

1. **Given** thành viên muốn biết thời gian xin phép vắng họp, **When** thành viên hỏi "Tôi phải xin phép trước bao lâu nếu bận việc đột xuất?", **Then** chatbot trả lời chính xác số giờ quy định tối thiểu cần nộp đơn xin phép trước khi buổi họp diễn ra.
2. **Given** thành viên hỏi về mức phạt khi nộp bài tập trễ, **When** thành viên gửi câu hỏi, **Then** chatbot liệt kê rõ ràng các mốc thời gian trễ và số điểm trừ / hình thức xử lý tương ứng.

---

### User Story 4 - Hướng dẫn liên hệ HR khi có thắc mắc hoặc cần giải trình (Priority: P3)

Sau khi được giải đáp lý do vi phạm, nếu thành viên nhận thấy có sự nhầm lẫn (ví dụ: đã được duyệt đơn xin phép nhưng hệ thống vẫn ghi nhận vi phạm, hoặc có lý do bất khả kháng), chatbot giữ vai trò cố vấn chỉ đọc (Read-only Advisor) và chủ động hướng dẫn thành viên liên hệ trực tiếp với bộ phận Quản lý nhân sự (HR) / Ban quản trị để được hỗ trợ kiểm tra và điều chỉnh.

**Why this priority**: Đóng kín chu trình hỗ trợ người dùng, phân định rõ ràng giữa vai trò giải đáp tự động của bot và quyền hạn xử lý khiếu nại của con người (HR), tránh việc bot tự ý sửa đổi hoặc hứa hẹn trái thẩm quyền.

**Independent Test**: Khi người dùng bày tỏ không đồng ý hoặc cho rằng vi phạm bị tính sai, chatbot hướng dẫn rõ ràng việc liên hệ với HR mà không tự động sửa đổi dữ liệu hay điều hướng phức tạp.

**Acceptance Scenarios**:

1. **Given** thành viên cho rằng vi phạm bị tính sai, **When** thành viên phản hồi "Tôi có nộp đơn xin phép rồi mà, sao vẫn bị phạt?", **Then** chatbot giải thích thông tin ghi nhận trong hệ thống và hướng dẫn thành viên liên hệ trực tiếp với bộ phận HR để được rà soát và hỗ trợ điều chỉnh.

---

### User Story 5 - Thành viên truy vấn sâu & đối soát chéo lý do vi phạm (Meeting, Homework, Đơn xin phép) (Priority: P1)

Khi thành viên đọc lý do vi phạm (ví dụ: *"Chưa hoàn tất đánh giá tổng thể buổi học 'Sinh hoạt gen 1' ngày 29/10/2026"* hoặc *"Nộp bài tập trễ hạn"*), thành viên thường có nhu cầu truy vấn bối cảnh gốc để kiểm tra xem hệ thống có tính nhầm hay không:
- Buổi học đó diễn ra khi nào? Kết thúc lúc mấy giờ?
- Hạn chót đánh giá buổi học (Evaluation Deadline) theo quy chế 24h là bao giờ?
- Hệ thống đã ghi nhận đánh giá của thành viên đó vào thời điểm nào chưa?
- Bài tập đó có deadline cá nhân là bao giờ? Thành viên nộp bài lúc mấy giờ?
- Thành viên có nộp đơn xin phép (vắng, trễ, gia hạn) hợp lệ cho sự kiện đó không?

Chatbot sử dụng **Công cụ Khảo sát Thực thể Tham số hóa Hợp nhất (Parameterized Unified Entity Explorer)** để tra cứu chéo và tổng hợp đầy đủ hồ sơ liên quan (buổi học, trạng thái check-in, lịch sử đánh giá, hạn nộp, lịch sử nộp bài, đơn từ liên quan) và trả lời đối soát tường tận từng mốc thời gian, giúp thành viên tâm phục khẩu phục hoặc biết chính xác lý do để trình bày với HR.

**Why this priority**: Giải quyết dứt điểm rào cản "tool fix cứng", cho phép Agent tự do truy vấn bất kỳ thực thể nào trong hệ sinh thái của người dùng để trả lời những câu hỏi giải trình phức tạp nhất.

**Independent Test**: Thành viên hỏi *"Hãy giải thích về vi phạm Chưa hoàn tất đánh giá tổng thể buổi học 'Sinh hoạt gen 1' (ngày 29/10/2026) của tôi"*. Chatbot tự động truy vấn thông tin buổi học `Sinh hoạt gen 1`, xác định thời gian kết thúc, deadline đánh giá 24h sau buổi học, trạng thái đánh giá của user, và so sánh đối chiếu thời gian để trả lời rõ ràng.

**Acceptance Scenarios**:

1. **Given** thành viên bị phạt vì chưa hoàn thành đánh giá buổi học ngày 29/10/2026, **When** thành viên hỏi giải thích chi tiết, **Then** chatbot tra cứu thực thể `meeting` và `evaluation`, chỉ ra rõ thời gian buổi học, mốc deadline 24h và thời điểm hệ thống ghi nhận.
2. **Given** thành viên hỏi về bài tập bị phạt nộp muộn, **When** thành viên yêu cầu kiểm tra, **Then** chatbot tra cứu thực thể `homework`, so sánh mốc deadline của thành viên với thời điểm nộp bài đầu tiên/cuối cùng để giải thích chênh lệch thời gian.
3. **Given** thành viên thắc mắc dù đã có đơn xin phép, **When** thành viên hỏi "Tôi có gửi đơn xin phép vắng buổi họp đó rồi mà sao vẫn bị phạt?", **Then** chatbot tra cứu thực thể `permission_request` của thành viên liên kết với buổi họp đó, kiểm tra nội dung đơn và ghi chú để giải thích cụ thể.

---

### Edge Cases

- **Người dùng đặt câu hỏi không liên quan đến quy chế hoặc hệ thống** (ví dụ: hỏi về thời tiết, giải toán, lập trình ngoài phạm vi): Chatbot lịch sự nhắc nhở phạm vi chuyên môn của mình là hỗ trợ quy chế và giải đáp vi phạm của tổ chức.
- **Dữ liệu vi phạm có chứa thông tin nhạy cảm hoặc ghi chú nội bộ**: Chatbot chỉ hiển thị các thông tin công khai hợp lệ cho người vi phạm biết, không làm lộ các đánh giá nội bộ của ban quản trị nếu người hỏi không có quyền quản trị tương ứng.
- **Lượng câu hỏi liên tục / Spam**: Giới hạn tốc độ gửi tin nhắn (rate-limiting) để bảo vệ hệ sinh thái và tài nguyên tính toán.
- **Mất kết nối mạng giữa chừng khi đang nhận phản hồi**: Giao diện hiển thị trạng thái ngắt kết nối thân thiện và cho phép gửi lại câu hỏi mà không làm mất lịch sử trước đó.
- **Vượt quá số phiên lưu trữ tối đa**: Khi số phiên hội thoại vượt quá 5, hệ thống tự động xóa phiên cũ nhất (FIFO) để luôn duy trì đúng 5 phiên gần nhất cho người dùng.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI cung cấp một giao diện trò chuyện chuyên dụng cho phép thành viên nhập câu hỏi văn bản và nhận câu trả lời dạng đối thoại tự nhiên bằng tiếng Việt.
- **FR-002**: Hệ thống PHẢI xác thực danh tính người dùng và CHỈ cho phép thành viên thông thường truy vấn thông tin vi phạm của chính tài khoản đang đăng nhập, nghiêm cấm truy xuất dữ liệu cá nhân của thành viên khác.
- **FR-003**: Chatbot PHẢI có khả năng tra cứu các bản ghi vi phạm trong hệ thống (thời gian, loại vi phạm: trễ, vắng, vi phạm bài tập, lý do hệ thống ghi nhận) để giải thích cho người dùng.
- **FR-004**: Chatbot PHẢI chứa cơ sở tri thức chính thức về quy chế hoạt động (quy định điểm danh, thời hạn nộp bài, thủ tục xin phép, quy tắc cộng/trừ điểm thưởng phạt) để giải đáp các thắc mắc chính sách chung.
- **FR-005**: Chatbot PHẢI cung cấp các câu hỏi gợi ý nhanh (Quick Prompts) thích ứng theo vai trò (Role-adaptive):
  - Thành viên thông thường: gợi ý tra cứu cá nhân ("Vi phạm tháng này của tôi", "Quy định xin nghỉ meeting", "Cách tính điểm phạt").
  - Ban Quản trị / Mentor: gợi ý quản lý tổng hợp ("Tổng hợp vi phạm tuần này", "Ai có từ 3 vi phạm trở lên?", "Ai chưa nộp bài tập mới nhất?", "Danh sách vắng họp hôm qua").
- **FR-006**: Hệ thống PHẢI hỗ trợ hiển thị phản hồi dạng luồng (streaming) để người dùng nhận được nội dung câu trả lời từng phần mà không phải chờ đợi toàn bộ văn bản sinh ra.
- **FR-007**: Hệ thống PHẢI cung cấp giao diện linh hoạt bao gồm cả một trang độc lập riêng biệt (`/assistant` hoặc `/chatbot`) trong hệ thống điều hướng chính và một nút biểu tượng nổi (Floating Action Icon) ở góc phải dưới màn hình trên toàn bộ ứng dụng web, cho phép người dùng mở nhanh khung popover chat ở bất kỳ trang nào.
- **FR-008**: Hệ thống PHẢI lưu trữ tối đa 5 phiên hội thoại gần nhất của mỗi thành viên trong cơ sở dữ liệu, cho phép người dùng xem lại lịch sử các câu hỏi và câu trả lời trước đó qua các lần đăng nhập.
- **FR-009**: Chatbot đóng vai trò cố vấn chỉ đọc (Read-only Advisor); khi thành viên có thắc mắc hoặc muốn khiếu nại về vi phạm, chatbot PHẢI hướng dẫn thành viên liên hệ trực tiếp với bộ phận Quản lý nhân sự (HR) / Ban quản trị để được hỗ trợ giải quyết, không thực hiện hành vi gửi đơn tự động hay chèn đường dẫn phức tạp.
- **FR-010**: Hệ thống PHẢI áp dụng cơ chế phân quyền chặt chẽ trên danh mục công cụ (Tool Registry RBAC): các công cụ tra cứu tổng hợp dữ liệu thành viên, báo cáo vi phạm toàn hệ thống và theo dõi tiến độ bài tập toàn khóa CHỈ được kích hoạt khi tài khoản người dùng sở hữu quyền tương ứng (`violation:read`, `homework:read`, `meeting:read`).
- **FR-011**: Chatbot PHẢI hỗ trợ Ban Quản trị truy vấn danh sách thành viên vi phạm vượt ngưỡng (ví dụ: >= 3 lần/tháng), thống kê vi phạm theo tuần/tháng, và phân loại theo dạng vi phạm (vắng họp, đi trễ, nộp bài trễ).
- **FR-012**: Chatbot PHẢI hỗ trợ Mentor/Trainer tra cứu danh sách người chưa nộp bài tập theo từng bài tập cụ thể hoặc kiểm tra tiến độ học vụ của một học viên cụ thể bằng tên hoặc mã sinh viên.
- **FR-013**: Chatbot PHẢI trang bị Công cụ Khảo sát Thực thể Tham số hóa Hợp nhất (`inspect_entity_records`) cho phép tra cứu linh hoạt các loại thực thể nghiệp vụ của người dùng (`meeting`, `homework`, `evaluation`, `permission_request`, `violation`) kèm các bộ lọc tham số (tên/tiêu đề, mốc thời gian, loại liên kết).
- **FR-014**: Khi tra cứu thực thể buổi học (`meeting`), hệ thống PHẢI cung cấp đầy đủ: thời gian diễn ra, trạng thái check-in của user, vai trò (TRAINER/TRAINEE), hạn chót đánh giá tổng thể (24h), và lịch sử các bản ghi đánh giá cá nhân / tổng thể đã nộp.
- **FR-015**: Khi tra cứu thực thể bài tập (`homework`), hệ thống PHẢI cung cấp đầy đủ: hạn nộp cá nhân (`deadline`), trạng thái đã nộp (`is_passed`, `score`), và danh sách các lần nộp bài (`submitted_at`).
- **FR-016**: Khi tra cứu thực thể đơn từ (`permission_request`), hệ thống PHẢI cung cấp: loại đơn (vắng, trễ, đổi ca, hoãn bài tập), nội dung lý do, và liên kết tới buổi họp/bài tập cụ thể.
- **FR-017**: Mọi truy vấn từ `inspect_entity_records` PHẢI áp dụng kiểm tra IDOR tuyệt đối ở tầng cơ sở dữ liệu: thành viên thông thường không bao giờ truy vấn được dữ liệu buổi học cá nhân, bài tập hay đơn từ của thành viên khác.

---

### Key Entities *(include if feature involves data)*

- **ChatSession**: Đại diện cho một phiên hội thoại giữa người dùng và trợ lý ảo (tối đa 5 phiên gần nhất/user). Chứa thông tin định danh phiên, mã thành viên sở hữu, thời điểm bắt đầu, thời điểm cập nhật gần nhất và tiêu đề cuộc trò chuyện.
- **ChatMessage**: Bản ghi tin nhắn trong một phiên. Chứa thông tin người gửi (người dùng hoặc trợ lý ảo), nội dung văn bản, danh sách trích dẫn/dữ liệu tham chiếu (nếu có), thời gian gửi.
- **ViolationContext**: Đối tượng ngữ cảnh trích xuất từ dữ liệu vi phạm của thành viên (danh sách vi phạm gần nhất, trạng thái đơn xin phép liên quan, tóm tắt tổng điểm phạt) được cung cấp an toàn cho bộ máy trả lời câu hỏi.
- **AdminAnalyticsContext**: Đối tượng ngữ cảnh chứa các số liệu tổng hợp về vi phạm, tỷ lệ vắng họp, danh sách bài tập chưa nộp được cung cấp an toàn cho các truy vấn của Ban Quản trị.
- **PolicyDocument**: Tài liệu tri thức chứa nội dung quy định, điều lệ xử lý vi phạm, hướng dẫn thủ tục đã được biên tập chuẩn hóa của tổ chức.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 90% câu hỏi tra cứu lý do vi phạm của thành viên được giải đáp chính xác theo đúng dữ liệu hệ thống mà không cần sự can thiệp của ban quản trị.
- **SC-002**: Thời gian bắt đầu hiển thị phản hồi đầu tiên cho người dùng sau khi gửi câu hỏi đạt dưới 2 giây.
- **SC-003**: 100% dữ liệu vi phạm cá nhân được bảo vệ nghiêm ngặt: không có bất kỳ trường hợp nào người dùng thông thường có thể tra cứu thông tin vi phạm của thành viên khác qua chatbot.
- **SC-004**: Tỷ lệ thành viên hài lòng với câu trả lời giải đáp vi phạm đạt từ 80% trở lên qua phản hồi đánh giá nhanh (thích/không thích).
- **SC-005**: Số lượng phiên hội thoại lưu trữ được giới hạn chính xác tối đa 5 phiên gần nhất cho mỗi người dùng, tự động dọn dẹp các phiên cũ hơn.
- **SC-006**: Ban Quản trị và Mentor giảm ít nhất 70% thời gian tra cứu và thống kê thủ công dữ liệu vi phạm và bài tập tồn đọng thông qua các câu lệnh chat nhanh.
- **SC-007**: 100% các câu hỏi truy vấn dữ liệu thành viên khác từ tài khoản không có quyền quản trị đều bị từ chối truy cập ngay tại tầng phân quyền công cụ.

---

## Assumptions

- Người dùng truy cập chatbot là thành viên đã đăng nhập thành công vào hệ thống web.
- Dữ liệu vi phạm đã được ghi nhận trong cơ sở dữ liệu hiện tại (thông qua các tính năng chấm điểm danh, kiểm tra bài tập, điểm danh thiết bị).
- Nội dung quy chế xử phạt và quy định tổ chức đã có văn bản hoặc tài liệu nội bộ chính thức để đưa vào cơ sở tri thức của chatbot.
- Giai đoạn đầu tập trung vào hỗ trợ giải đáp văn bản (tiếng Việt), chưa bao gồm nhận dạng giọng nói hoặc tin nhắn âm thanh.
- Chatbot là Read-only Advisor, hướng dẫn liên hệ HR khi có khiếu nại.
- Công nghệ điều phối là LLM Tool/Function Calling định hướng theo vai trò (Role-adaptive Tool Calling), không sử dụng Agent Harness tự trị phức tạp.
