/**
 * Chatbot Domain & DTO types re-exported directly from OpenAPI generated types.
 * Single source of truth with the backend contracts.
 */
import type { components } from '@/types/api.generated';

export type MessageRole = components['schemas']['MessageRole'];
export type ToolCallRecord = components['schemas']['ToolCallRecord'];
export type ChatMessageMetadata = components['schemas']['ChatMessageMetadata'];
export type ChatMessage = components['schemas']['ChatMessageDto'];
export type ChatSession = components['schemas']['ChatSessionDto'];
export type QuickPromptItem = components['schemas']['QuickPromptItem'];
export type SendChatPayload = components['schemas']['SendChatRequest'];

/**
 * UI Grouping model for categorizing chat sessions by relative date.
 */
export type SessionDateGroupKey = 'Hôm nay' | 'Hôm qua' | '7 ngày trước' | 'Cũ hơn';

export interface ChatSessionGroup {
  groupLabel: SessionDateGroupKey;
  sessions: ChatSession[];
}

export interface ActiveStreamingTool {
  name: string;
  status: 'running' | 'success' | 'error' | 'duplicate_skipped';
  iteration: number;
}
