import React from "react";
import { MessageItem } from "./Message";
import type { ChatMessage } from "../../types/chatbot.types";
import {
  MessageScrollerProvider,
  MessageScroller,
  MessageScrollerContent,
  MessageScrollerItem,
  MessageScrollerViewport,
  MessageScrollerButton,
} from "@/components/ui/message-scroller";
import { BotIcon } from "lucide-react";

interface ChatProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  streamingText: string;
  streamingReasoning: string;
  activeTools?: Array<{ name: string; status: string; iteration: number }>;
  emptyStateTitle?: string;
  emptyStateSubtitle?: string;
}

export const Chat: React.FC<ChatProps> = ({
  messages,
  isStreaming,
  streamingText,
  streamingReasoning,
  activeTools,
  emptyStateTitle = "DUT AI Assistant",
  emptyStateSubtitle = "Trợ lý nội bộ giải đáp quy chế vi phạm, lịch họp và học vụ. Hãy chọn câu hỏi gợi ý bên dưới hoặc nhập câu hỏi của bạn.",
}) => {
  return (
    <MessageScrollerProvider autoScroll>
      <MessageScroller className="h-full w-full relative">
        <MessageScrollerViewport className="h-full px-4 py-6">
          <MessageScrollerContent className="max-w-3xl mx-auto pb-4">
            {messages.length === 0 && !isStreaming && (
              <div className="flex flex-col items-center justify-center my-auto py-16 text-center">
                <div className="size-12 rounded-2xl bg-primary/10 text-primary flex items-center justify-center mb-4 shadow-2xs border border-primary/20">
                  <BotIcon className="size-6" />
                </div>
                <h3 className="text-lg font-semibold tracking-tight text-foreground">
                  {emptyStateTitle}
                </h3>
                <p className="text-sm max-w-md mt-2 text-muted-foreground leading-relaxed">
                  {emptyStateSubtitle}
                </p>
              </div>
            )}

            {messages.map((msg) => (
              <MessageScrollerItem
                key={msg.id}
                messageId={String(msg.id)}
                scrollAnchor={msg.role === "user"}
              >
                <MessageItem message={msg} />
              </MessageScrollerItem>
            ))}

            {/* Ephemeral streaming turn */}
            {isStreaming && (
              <MessageScrollerItem messageId="streaming" scrollAnchor={false}>
                <MessageItem
                  message={{
                    id: -1,
                    session_id: -1,
                    role: "assistant",
                    content: streamingText || "",
                    metadata_info: {
                      model_name: "ggml-org/gemma-4-e4b-it-GGUF:Q4_0",
                      reasoning_content: streamingReasoning,
                    },
                    created_at: new Date().toISOString(),
                  }}
                  isStreaming={true}
                  streamingReasoning={streamingReasoning}
                  activeTools={activeTools}
                />
              </MessageScrollerItem>
            )}
          </MessageScrollerContent>
        </MessageScrollerViewport>
        <MessageScrollerButton />
      </MessageScroller>
    </MessageScrollerProvider>
  );
};
