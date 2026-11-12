import { useReducer, useState, useEffect, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { chatbotService } from '../services/chatbot.service';
import { CHAT_SESSIONS_QUERY_KEY } from './useChatSessions';
import type { ActiveStreamingTool, ChatMessage, QuickPromptItem } from '../types/chatbot.types';

export interface ChatbotState {
  sessionId: string | null;
  messages: ChatMessage[];
  isStreaming: boolean;
  streamingText: string;
  streamingReasoning: string;
  activeTools: ActiveStreamingTool[];
  currentIteration: number;
  errorMessage: string | null;
  quickPrompts: QuickPromptItem[];
}

export type ChatbotAction =
  | { type: 'SET_QUICK_PROMPTS'; payload: QuickPromptItem[] }
  | { type: 'SYNC_SESSION_ID'; payload: string | null }
  | { type: 'LOAD_MESSAGES_SUCCESS'; payload: { sessionId: string; messages: ChatMessage[] } }
  | { type: 'LOAD_MESSAGES_ERROR'; payload: string }
  | { type: 'START_NEW_CHAT' }
  | { type: 'SELECT_SESSION'; payload: string }
  | { type: 'SEND_MESSAGE_START'; payload: { userMessage: ChatMessage } }
  | { type: 'SESSION_CREATED'; payload: string }
  | { type: 'ITERATION_STEP'; payload: number }
  | { type: 'TOOL_CALL_START'; payload: { name: string; iteration: number } }
  | {
      type: 'TOOL_CALL_END';
      payload: { name: string; iteration: number; status: ActiveStreamingTool['status'] };
    }
  | { type: 'APPEND_REASONING'; payload: string }
  | { type: 'APPEND_CHUNK'; payload: string }
  | {
      type: 'STREAMING_DONE';
      payload: { messages?: ChatMessage[]; fallbackMessage?: ChatMessage };
    }
  | { type: 'STREAMING_ERROR'; payload: string }
  | { type: 'SET_ERROR_MESSAGE'; payload: string | null };

export function chatbotReducer(state: ChatbotState, action: ChatbotAction): ChatbotState {
  switch (action.type) {
    case 'SET_QUICK_PROMPTS':
      return {
        ...state,
        quickPrompts: action.payload,
      };

    case 'SYNC_SESSION_ID':
      if (state.sessionId === action.payload) return state;
      // Do NOT wipe messages if we just received a new session ID during active streaming
      return {
        ...state,
        sessionId: action.payload,
        messages: state.isStreaming
          ? state.messages
          : action.payload === null
            ? []
            : state.messages,
        streamingText: state.isStreaming ? state.streamingText : '',
        streamingReasoning: state.isStreaming ? state.streamingReasoning : '',
        activeTools: state.isStreaming ? state.activeTools : [],
        currentIteration: state.isStreaming ? state.currentIteration : 0,
        errorMessage: null,
        isStreaming: state.isStreaming,
      };

    case 'LOAD_MESSAGES_SUCCESS':
      if (state.sessionId !== action.payload.sessionId) return state;
      return {
        ...state,
        messages: action.payload.messages,
        errorMessage: null,
      };

    case 'LOAD_MESSAGES_ERROR':
      return {
        ...state,
        errorMessage: action.payload,
      };

    case 'START_NEW_CHAT':
      return {
        ...state,
        sessionId: null,
        messages: [],
        streamingText: '',
        streamingReasoning: '',
        activeTools: [],
        currentIteration: 0,
        errorMessage: null,
        isStreaming: false,
      };

    case 'SELECT_SESSION':
      return {
        ...state,
        sessionId: action.payload,
        streamingText: '',
        streamingReasoning: '',
        activeTools: [],
        currentIteration: 0,
        errorMessage: null,
        isStreaming: false,
      };

    case 'SEND_MESSAGE_START':
      return {
        ...state,
        messages: [...state.messages, action.payload.userMessage],
        isStreaming: true,
        streamingText: '',
        streamingReasoning: '',
        activeTools: [],
        currentIteration: 0,
        errorMessage: null,
      };

    case 'SESSION_CREATED':
      return {
        ...state,
        sessionId: action.payload,
      };

    case 'ITERATION_STEP':
      return {
        ...state,
        currentIteration: action.payload,
      };

    case 'TOOL_CALL_START':
      return {
        ...state,
        activeTools: [
          ...state.activeTools,
          {
            name: action.payload.name,
            status: 'running',
            iteration: action.payload.iteration,
          },
        ],
      };

    case 'TOOL_CALL_END':
      return {
        ...state,
        activeTools: state.activeTools.map((t) =>
          t.name === action.payload.name && t.iteration === action.payload.iteration
            ? { ...t, status: action.payload.status }
            : t
        ),
      };

    case 'APPEND_REASONING':
      return {
        ...state,
        streamingReasoning: state.streamingReasoning + action.payload,
      };

    case 'APPEND_CHUNK':
      return {
        ...state,
        streamingText: state.streamingText + action.payload,
      };

    case 'STREAMING_DONE':
      return {
        ...state,
        isStreaming: false,
        streamingText: '',
        streamingReasoning: '',
        activeTools: [],
        currentIteration: 0,
        messages:
          action.payload.messages !== undefined
            ? action.payload.messages
            : action.payload.fallbackMessage
              ? [...state.messages, action.payload.fallbackMessage]
              : state.messages,
      };

    case 'STREAMING_ERROR':
      return {
        ...state,
        isStreaming: false,
        errorMessage: action.payload,
      };

    case 'SET_ERROR_MESSAGE':
      return {
        ...state,
        errorMessage: action.payload,
      };

    default:
      return state;
  }
}

export interface UseChatbotOptions {
  sessionId?: string | null;
  onSessionCreated?: (sessionId: string) => void;
}

export function useChatbot(options: UseChatbotOptions = {}) {
  const { sessionId: externalSessionId = null, onSessionCreated } = options;
  const queryClient = useQueryClient();
  const [input, setInput] = useState('');
  const abortControllerRef = useRef<AbortController | null>(null);

  const [state, dispatch] = useReducer(chatbotReducer, {
    sessionId: externalSessionId,
    messages: [],
    isStreaming: false,
    streamingText: '',
    streamingReasoning: '',
    activeTools: [],
    currentIteration: 0,
    errorMessage: null,
    quickPrompts: [],
  });

  // Sync state if external sessionId changes (e.g. from Sidebar selection or Start New Chat)
  useEffect(() => {
    dispatch({ type: 'SYNC_SESSION_ID', payload: externalSessionId });
  }, [externalSessionId]);

  // Fetch quick prompts on mount
  useEffect(() => {
    chatbotService
      .getQuickPrompts()
      .then((data) => dispatch({ type: 'SET_QUICK_PROMPTS', payload: data }))
      .catch(() => {});
  }, []);

  // Fetch session history when sessionId changes, but only when not currently streaming a new conversation
  useEffect(() => {
    if (!state.sessionId || state.isStreaming) return;
    let isCancelled = false;
    const currentId = state.sessionId;

    chatbotService
      .getSessionMessages(currentId)
      .then((msgs) => {
        if (!isCancelled) {
          dispatch({
            type: 'LOAD_MESSAGES_SUCCESS',
            payload: { sessionId: currentId, messages: msgs },
          });
        }
      })
      .catch(() => {
        if (!isCancelled) {
          dispatch({
            type: 'LOAD_MESSAGES_ERROR',
            payload: 'Không thể tải lịch sử trò chuyện.',
          });
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [state.sessionId, state.isStreaming]);

  const startNewChat = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    dispatch({ type: 'START_NEW_CHAT' });
  }, []);

  const selectSession = useCallback((id: string) => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    dispatch({ type: 'SELECT_SESSION', payload: id });
  }, []);

  const setErrorMessage = useCallback((msg: string | null) => {
    dispatch({ type: 'SET_ERROR_MESSAGE', payload: msg });
  }, []);

  const sendMessage = useCallback(
    async (promptOverride?: string) => {
      const text = (promptOverride || input).trim();
      if (!text || state.isStreaming) return;

      // Optimistically add user message with client UUID
      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        session_id: state.sessionId || '00000000-0000-0000-0000-000000000000',
        role: 'user',
        content: text,
        metadata_info: {
          model_name: 'ggml-org/gemma-4-e4b-it-GGUF:Q4_0',
        },
        created_at: new Date().toISOString(),
      };

      setInput('');
      dispatch({ type: 'SEND_MESSAGE_START', payload: { userMessage } });

      const controller = new AbortController();
      abortControllerRef.current = controller;

      let currentSessionId = state.sessionId;

      await chatbotService.streamChat(
        {
          message: text,
          session_id: currentSessionId,
        },
        {
          onSessionCreated: (newSess) => {
            currentSessionId = newSess.id;
            dispatch({ type: 'SESSION_CREATED', payload: newSess.id });
            if (onSessionCreated) {
              onSessionCreated(newSess.id);
            }
            queryClient.invalidateQueries({ queryKey: CHAT_SESSIONS_QUERY_KEY });
          },
          onIterationStep: (step) => {
            dispatch({ type: 'ITERATION_STEP', payload: step.iteration });
          },
          onToolCallStart: (tool) => {
            dispatch({
              type: 'TOOL_CALL_START',
              payload: { name: tool.name, iteration: tool.iteration },
            });
          },
          onToolCallEnd: (tool) => {
            dispatch({
              type: 'TOOL_CALL_END',
              payload: {
                name: tool.name,
                iteration: tool.iteration,
                status: tool.status as ActiveStreamingTool['status'],
              },
            });
          },
          onReasoning: (chunk) => {
            dispatch({ type: 'APPEND_REASONING', payload: chunk });
          },
          onChunk: (chunk) => {
            dispatch({ type: 'APPEND_CHUNK', payload: chunk });
          },
          onDone: (fullText) => {
            if (currentSessionId) {
              chatbotService.getSessionMessages(currentSessionId).then((serverMsgs) => {
                dispatch({
                  type: 'STREAMING_DONE',
                  payload: { messages: serverMsgs },
                });
              });
              queryClient.invalidateQueries({ queryKey: CHAT_SESSIONS_QUERY_KEY });
            } else {
              const fallback: ChatMessage = {
                id: crypto.randomUUID(),
                session_id: '00000000-0000-0000-0000-000000000000',
                role: 'assistant',
                content: fullText,
                metadata_info: {
                  model_name: 'ggml-org/gemma-4-e4b-it-GGUF:Q4_0',
                },
                created_at: new Date().toISOString(),
              };
              dispatch({
                type: 'STREAMING_DONE',
                payload: { fallbackMessage: fallback },
              });
            }
          },
          onError: (err) => {
            dispatch({
              type: 'STREAMING_ERROR',
              payload: err || 'Đã có lỗi xảy ra trong quá trình nhận phản hồi.',
            });
          },
        },
        controller.signal
      );
    },
    [input, state.isStreaming, state.sessionId, onSessionCreated, queryClient]
  );

  return {
    sessionId: state.sessionId,
    messages: state.messages,
    input,
    setInput,
    isStreaming: state.isStreaming,
    streamingText: state.streamingText,
    streamingReasoning: state.streamingReasoning,
    activeTools: state.activeTools,
    currentIteration: state.currentIteration,
    errorMessage: state.errorMessage,
    setErrorMessage,
    quickPrompts: state.quickPrompts,
    sendMessage,
    startNewChat,
    selectSession,
  };
}
