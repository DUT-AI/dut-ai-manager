/**
 * Assistant UI Component Contracts & Event Specifications
 * Feature Branch: 063-rebuild-assistant-ui
 * 
 * Strict type contracts for all rebuilt shadcn AI Elements components
 * following DUT AI Manager Constitution Principle VIII & XIII.
 */

import type {
  ChatMessage,
  ChatSession,
  QuickPromptItem,
  ToolCallRecord,
} from '@/features/chatbot/types/chatbot.types';

// ============================================================================
// 1. Core AI Elements Component Contracts
// ============================================================================

export interface ChatProps {
  /** Danh sách các tin nhắn đã gửi/nhận */
  messages: ChatMessage[];
  /** Trạng thái AI đang sinh câu trả lời */
  isStreaming: boolean;
  /** Nội dung văn bản đang được stream từng phần */
  streamingText: string;
  /** Nội dung chuỗi suy luận đang được stream */
  streamingReasoning: string;
  /** Tiêu đề hiển thị khi chưa có tin nhắn nào */
  emptyStateTitle?: string;
  /** Phụ đề hướng dẫn khi chưa có tin nhắn nào */
  emptyStateSubtitle?: string;
}

export interface MessageProps {
  /** Dữ liệu lượt tin nhắn */
  message: ChatMessage;
  /** Đang trong trạng thái stream cho tin nhắn này */
  isStreaming?: boolean;
  /** Nội dung chuỗi suy luận đang streaming */
  streamingReasoning?: string;
}

export interface PromptInputProps {
  /** Giá trị câu hỏi đang nhập */
  value: string;
  /** Hàm callback khi thay đổi văn bản */
  onChange: (val: string) => void;
  /** Hàm callback khi người dùng bấm gửi hoặc nhấn Enter */
  onSubmit: () => void;
  /** Đang tải / AI đang phản hồi (nút gửi chuyển thành spinner và bị disable) */
  isLoading: boolean;
  /** Chữ giữ chỗ gợi ý trong ô nhập */
  placeholder?: string;
}

export interface ReasoningProps {
  /** Toàn bộ văn bản chuỗi suy luận (Chain of Thought) */
  content: string;
  /** Trạng thái đang sinh tư duy (hiển thị spinner 'Thinking...') */
  isStreaming?: boolean;
}

export interface ToolTraceProps {
  /** Danh sách các bước gọi công cụ được ghi nhận */
  tools?: ToolCallRecord[];
  /** Trạng thái công cụ đang được thực thi ngầm */
  isExecuting?: boolean;
}

export interface SuggestionProps {
  /** Danh sách các câu hỏi gợi ý nhanh phù hợp với vai trò người dùng */
  prompts: QuickPromptItem[];
  /** Callback khi người dùng nhấp chọn một gợi ý để gửi ngay */
  onSelectPrompt: (promptText: string) => void;
  /** Vô hiệu hóa nhấp chọn khi đang streaming */
  disabled?: boolean;
}

// ============================================================================
// 2. Navigation & Sidebar Contracts
// ============================================================================

export interface ChatSessionSidebarProps {
  /** Danh sách tối đa 5 phiên hội thoại gần nhất */
  sessions: ChatSession[];
  /** ID phiên hiện tại đang kích hoạt */
  activeSessionId: number | null;
  /** Trạng thái mở/đóng thanh bên trên Desktop/Mobile */
  isOpen: boolean;
  /** Callback đóng thanh bên */
  onClose: () => void;
  /** Callback chọn một phiên trò chuyện */
  onSelectSession: (id: number) => void;
  /** Callback bắt đầu phiên trò chuyện mới */
  onNewChat: () => void;
  /** Callback yêu cầu mở modal xác nhận xóa phiên */
  onRequestDeleteSession: (id: number) => void;
}

export interface DeleteSessionDialogProps {
  /** Trạng thái mở/đóng của hộp thoại */
  isOpen: boolean;
  /** Callback khi đóng hoặc hủy hộp thoại */
  onOpenChange: (open: boolean) => void;
  /** Callback xác nhận xóa phiên */
  onConfirm: () => void;
  /** Đang trong quá trình gọi API xóa */
  isDeleting: boolean;
}

export interface ChatHeaderProps {
  /** Trạng thái thanh bên đang mở hay đóng */
  isSidebarOpen: boolean;
  /** Callback toggle trạng thái thanh bên */
  onToggleSidebar: () => void;
  /** Callback bắt đầu phiên trò chuyện mới */
  onNewChat: () => void;
}

// ============================================================================
// 3. SSE Streaming Event Contracts (Backend to Frontend)
// ============================================================================

export type ChatStreamEventType =
  | 'session'     // Khởi tạo phiên mới thành công
  | 'reasoning'   // Chunk nội dung suy luận tư duy
  | 'chunk'       // Chunk nội dung câu trả lời chính
  | 'tool_start'  // Bắt đầu gọi một công cụ
  | 'tool_done'   // Hoàn tất gọi công cụ
  | 'done'        // Hoàn tất lượt trả lời
  | 'error';      // Gặp lỗi trong quá trình xử lý

export interface StreamSessionEvent {
  event: 'session';
  data: ChatSession;
}

export interface StreamReasoningEvent {
  event: 'reasoning';
  data: { delta: string };
}

export interface StreamChunkEvent {
  event: 'chunk';
  data: { delta: string };
}

export interface StreamToolStartEvent {
  event: 'tool_start';
  data: { tool_name: string; arguments?: Record<string, unknown> };
}

export interface StreamToolDoneEvent {
  event: 'tool_done';
  data: { tool_name: string; execution_status: 'success' | 'failed' };
}

export interface StreamDoneEvent {
  event: 'done';
  data: { full_content: string };
}

export interface StreamErrorEvent {
  event: 'error';
  data: { message: string };
}
