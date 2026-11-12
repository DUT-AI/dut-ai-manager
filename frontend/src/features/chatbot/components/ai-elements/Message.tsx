import React from "react";
import { Message, MessageContent } from "@/components/ui/message";
import { Bubble, BubbleContent } from "@/components/ui/bubble";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { Reasoning } from "./Reasoning";
import { ToolTrace } from "./ToolTrace";
import type { ChatMessage } from "../../types/chatbot.types";

interface MessageProps {
  message: ChatMessage;
  isStreaming?: boolean;
  streamingReasoning?: string;
  activeTools?: Array<{ name: string; status: string; iteration: number }>;
}

export const MessageItem: React.FC<MessageProps> = ({
  message,
  isStreaming,
  streamingReasoning,
  activeTools,
}) => {
  const isUser = message.role === "user";
  const reasoning = streamingReasoning || message.metadata_info?.reasoning_content;

  if (isUser) {
    return (
      <Message align="end" className="my-2.5">
        <MessageContent className="items-end">
          <Bubble
            align="end"
            variant="muted"
            className="rounded-2xl max-w-[85%] sm:max-w-[75%] bg-muted/80 text-foreground border-none shadow-none"
          >
            <BubbleContent className="px-4 py-2.5 text-sm text-foreground whitespace-pre-wrap break-words leading-relaxed border-none">
              {message.content}
            </BubbleContent>
          </Bubble>
        </MessageContent>
      </Message>
    );
  }

  return (
    <Message align="start" className="my-3.5 w-full">
      <MessageContent className="gap-2.5 max-w-full items-start">
        {/* Reasoning (Chain of Thought Trace) */}
        {reasoning && (
          <Reasoning
            content={reasoning}
            isStreaming={isStreaming && !message.content}
          />
        )}

        {/* Tool Call Trace */}
        {message.metadata_info?.tools_invoked && (
          <ToolTrace tools={message.metadata_info.tools_invoked} />
        )}

        {/* Live Active Streaming Tools Trace */}
        {isStreaming && activeTools && activeTools.length > 0 && (
          <div className="flex flex-col gap-1 w-full">
            {activeTools.map((t, idx) => (
              <ToolTrace
                key={`${t.name}-${t.iteration}-${idx}`}
                tools={[
                  {
                    tool_name: t.name,
                    arguments: {},
                    execution_status: t.status,
                  },
                ]}
                isExecuting={t.status === 'running'}
              />
            ))}
          </div>
        )}

        {/* Main Response Markdown */}
        {message.content ? (
          <div className="w-full text-sm leading-relaxed text-foreground">
            <MarkdownRenderer content={message.content} />
          </div>
        ) : isStreaming ? (
          <div className="flex items-center gap-1.5 py-1 text-muted-foreground text-xs">
            <span className="size-2 rounded-full bg-primary/70 animate-bounce" />
            <span className="size-2 rounded-full bg-primary/70 animate-bounce [animation-delay:0.2s]" />
            <span className="size-2 rounded-full bg-primary/70 animate-bounce [animation-delay:0.4s]" />
          </div>
        ) : null}
      </MessageContent>
    </Message>
  );
};

export { MessageItem as Message };
