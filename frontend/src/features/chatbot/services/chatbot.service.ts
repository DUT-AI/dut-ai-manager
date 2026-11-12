import axiosInstance from '@/services/axiosInstance';
import type {
  ChatMessage,
  ChatSession,
  QuickPromptItem,
  SendChatPayload,
} from '../types/chatbot.types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

export interface StreamChatCallbacks {
  onSessionCreated?: (session: { id: string; title: string }) => void;
  onChunk: (delta: string) => void;
  onReasoning?: (delta: string) => void;
  onIterationStep?: (step: { iteration: number; max_iterations: number }) => void;
  onToolCallStart?: (tool: { name: string; iteration: number }) => void;
  onToolCallEnd?: (tool: { name: string; status: string; iteration: number }) => void;
  onDone?: (fullMessage: string) => void;
  onError?: (error: string) => void;
}

export const chatbotService = {
  async getSessions(): Promise<ChatSession[]> {
    const res = await axiosInstance.get<{ is_success: boolean; data: ChatSession[] }>(
      '/chatbot/sessions'
    );
    return res.data.data;
  },

  async getSessionMessages(sessionId: string): Promise<ChatMessage[]> {
    const res = await axiosInstance.get<{ is_success: boolean; data: ChatMessage[] }>(
      `/chatbot/sessions/${sessionId}/messages`
    );
    return res.data.data;
  },

  async deleteSession(sessionId: string): Promise<void> {
    await axiosInstance.delete(`/chatbot/sessions/${sessionId}`);
  },

  async getQuickPrompts(): Promise<QuickPromptItem[]> {
    const res = await axiosInstance.get<{ is_success: boolean; data: QuickPromptItem[] }>(
      '/chatbot/quick-prompts'
    );
    return res.data.data;
  },

  async streamChat(
    payload: SendChatPayload,
    callbacks: StreamChatCallbacks,
    signal?: AbortSignal
  ): Promise<void> {
    const url = `${API_BASE_URL}/chatbot/chat`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(payload),
        signal,
      });

      if (!response.ok) {
        const errorText = await response.text();
        const errMessage = `Lỗi hệ thống (${response.status}): ${errorText}`;
        callbacks.onError?.(errMessage);
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        callbacks.onError?.('Không thể khởi tạo luồng đọc dữ liệu từ máy chủ.');
        return;
      }

      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let accumulatedText = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        // Keep the last partial line in buffer
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;

          if (trimmed.startsWith('data: ')) {
            const jsonStr = trimmed.slice(6).trim();
            if (jsonStr === '[DONE]') {
              callbacks.onDone?.(accumulatedText);
              return;
            }

            try {
              const eventData = JSON.parse(jsonStr);
              if (eventData.type === 'session_created') {
                callbacks.onSessionCreated?.(eventData.data);
              } else if (eventData.type === 'reasoning') {
                callbacks.onReasoning?.(eventData.data);
              } else if (eventData.type === 'iteration_step') {
                callbacks.onIterationStep?.(eventData.data);
              } else if (eventData.type === 'tool_call_start') {
                callbacks.onToolCallStart?.(eventData.data);
              } else if (eventData.type === 'tool_call_end') {
                callbacks.onToolCallEnd?.(eventData.data);
              } else if (eventData.type === 'delta' || eventData.type === 'content') {
                accumulatedText += eventData.data;
                callbacks.onChunk(eventData.data);
              } else if (eventData.type === 'done') {
                callbacks.onDone?.(accumulatedText);
              } else if (eventData.type === 'error') {
                callbacks.onError?.(eventData.data);
              }
            } catch {
              // Ignore non-json chunk or parse error
            }
          }
        }
      }

      callbacks.onDone?.(accumulatedText);
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        return;
      }
      const message = err instanceof Error ? err.message : 'Lỗi kết nối mạng đến máy chủ.';
      callbacks.onError?.(message);
    }
  },
};
