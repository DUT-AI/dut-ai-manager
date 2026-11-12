import { useState, useEffect, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { chatbotService } from '../services/chatbot.service';
import { CHAT_SESSIONS_QUERY_KEY } from './useChatSessions';
import type { ActiveStreamingTool, ChatMessage, QuickPromptItem } from '../types/chatbot.types';

export function useChatbot(initialSessionId?: number | null) {
  const queryClient = useQueryClient();
  const [sessionId, setSessionId] = useState<number | null>(initialSessionId || null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const [streamingReasoning, setStreamingReasoning] = useState('');
  const [activeTools, setActiveTools] = useState<ActiveStreamingTool[]>([]);
  const [currentIteration, setCurrentIteration] = useState<number>(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [quickPrompts, setQuickPrompts] = useState<QuickPromptItem[]>([]);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Fetch quick prompts on mount
  useEffect(() => {
    chatbotService
      .getQuickPrompts()
      .then((data) => setQuickPrompts(data))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!sessionId) return;
    let isCancelled = false;
    chatbotService
      .getSessionMessages(sessionId)
      .then((msgs) => {
        if (!isCancelled) {
          setMessages(msgs);
          setErrorMessage(null);
        }
      })
      .catch(() => {
        if (!isCancelled) {
          setErrorMessage('Không thể tải lịch sử trò chuyện.');
        }
      });
    return () => {
      isCancelled = true;
    };
  }, [sessionId]);

  const startNewChat = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setSessionId(null);
    setMessages([]);
    setStreamingText('');
    setStreamingReasoning('');
    setActiveTools([]);
    setCurrentIteration(0);
    setErrorMessage(null);
    setIsStreaming(false);
  }, []);

  const selectSession = useCallback((id: number) => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setSessionId(id);
    setStreamingText('');
    setStreamingReasoning('');
    setActiveTools([]);
    setCurrentIteration(0);
    setErrorMessage(null);
    setIsStreaming(false);
  }, []);

  const sendMessage = useCallback(
    async (promptOverride?: string) => {
      const text = (promptOverride || input).trim();
      if (!text || isStreaming) return;

      setErrorMessage(null);

      // Optimistically add user message
      const userMessage: ChatMessage = {
        id: Date.now(),
        session_id: sessionId || 0,
        role: 'user',
        content: text,
        metadata_info: {
          model_name: 'ggml-org/gemma-4-e4b-it-GGUF:Q4_0',
        },
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setInput('');
      setIsStreaming(true);
      setStreamingText('');
      setStreamingReasoning('');
      setActiveTools([]);
      setCurrentIteration(0);

      const controller = new AbortController();
      abortControllerRef.current = controller;

      let currentSessionId = sessionId;

      await chatbotService.streamChat(
        {
          message: text,
          session_id: currentSessionId,
        },
        {
          onSessionCreated: (newSess) => {
            currentSessionId = newSess.id;
            setSessionId(newSess.id);
            queryClient.invalidateQueries({ queryKey: CHAT_SESSIONS_QUERY_KEY });
          },
          onIterationStep: (step) => {
            setCurrentIteration(step.iteration);
          },
          onToolCallStart: (tool) => {
            setActiveTools((prev) => [
              ...prev,
              { name: tool.name, status: 'running', iteration: tool.iteration },
            ]);
          },
          onToolCallEnd: (tool) => {
            setActiveTools((prev) =>
              prev.map((t) =>
                t.name === tool.name && t.iteration === tool.iteration
                  ? { ...t, status: tool.status as ActiveStreamingTool['status'] }
                  : t
              )
            );
          },
          onReasoning: (chunk) => {
            setStreamingReasoning((prev) => prev + chunk);
          },
          onChunk: (chunk) => {
            setStreamingText((prev) => prev + chunk);
          },
          onDone: (fullText) => {
            setIsStreaming(false);
            setStreamingText('');
            setStreamingReasoning('');
            setActiveTools([]);
            setCurrentIteration(0);
            // Reload canonical persisted messages from server to sync metadata and IDs
            if (currentSessionId) {
              chatbotService.getSessionMessages(currentSessionId).then((serverMsgs) => {
                setMessages(serverMsgs);
              });
              queryClient.invalidateQueries({ queryKey: CHAT_SESSIONS_QUERY_KEY });
            } else {
              setMessages((prev) => [
                ...prev,
                {
                  id: Date.now() + 1,
                  session_id: 0,
                  role: 'assistant',
                  content: fullText,
                  metadata_info: {
                    model_name: 'ggml-org/gemma-4-e4b-it-GGUF:Q4_0',
                  },
                  created_at: new Date().toISOString(),
                },
              ]);
            }
          },
          onError: (err) => {
            setIsStreaming(false);
            setErrorMessage(err || 'Đã có lỗi xảy ra trong quá trình nhận phản hồi.');
          },
        },
        controller.signal
      );
    },
    [input, isStreaming, sessionId, queryClient]
  );

  return {
    sessionId,
    messages,
    input,
    setInput,
    isStreaming,
    streamingText,
    streamingReasoning,
    activeTools,
    currentIteration,
    errorMessage,
    setErrorMessage,
    quickPrompts,
    sendMessage,
    startNewChat,
    selectSession,
  };
}
