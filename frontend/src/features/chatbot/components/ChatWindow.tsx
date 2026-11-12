import React from "react";
import { Chat } from "./ai-elements/Chat";
import { PromptInput } from "./ai-elements/PromptInput";
import { Suggestion } from "./ai-elements/Suggestion";
import type { ChatMessage, QuickPromptItem } from "../types/chatbot.types";
import { AlertCircleIcon } from "lucide-react";

interface ChatWindowProps {
  messages: ChatMessage[];
  input: string;
  onChangeInput: (val: string) => void;
  onSendMessage: (override?: string) => void;
  isStreaming: boolean;
  streamingText?: string;
  streamingReasoning?: string;
  errorMessage?: string | null;
  onClearError?: () => void;
  quickPrompts?: QuickPromptItem[];
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  messages,
  input,
  onChangeInput,
  onSendMessage,
  isStreaming,
  streamingText,
  streamingReasoning,
  errorMessage,
  quickPrompts = [],
}) => {
  return (
    <div className="flex flex-col flex-1 h-full min-h-0 bg-background text-foreground">
      {/* Messages Scroll Viewport */}
      <div className="flex-1 min-h-0 overflow-hidden relative">
        <Chat
          messages={messages}
          isStreaming={isStreaming}
          streamingText={streamingText || ""}
          streamingReasoning={streamingReasoning || ""}
        />
      </div>

      {/* Bottom Input Area: Suggestions & Prompt Input */}
      <div className="p-4 bg-background/95 backdrop-blur-sm shrink-0 border-t border-border/40">
        <div className="max-w-3xl w-full mx-auto flex flex-col gap-2.5">
          {/* Inline Error Message */}
          {errorMessage && (
            <div className="flex items-center gap-2 rounded-xl bg-destructive/10 border border-destructive/20 px-3.5 py-2 text-xs text-destructive">
              <AlertCircleIcon className="size-4 shrink-0" />
              <span className="flex-1">{errorMessage}</span>
            </div>
          )}

          {/* Role-Adaptive Quick Suggestions */}
          {messages.length <= 2 && quickPrompts.length > 0 && (
            <Suggestion
              prompts={quickPrompts}
              onSelectPrompt={(text) => onSendMessage(text)}
              disabled={isStreaming}
            />
          )}

          {/* Agentic Prompt Input */}
          <PromptInput
            value={input}
            onChange={onChangeInput}
            onSubmit={() => onSendMessage()}
            isLoading={isStreaming}
          />
        </div>
      </div>
    </div>
  );
};
