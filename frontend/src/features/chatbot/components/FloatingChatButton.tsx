import React, { useState } from 'react';
import { BotIcon, XIcon, Maximize2Icon } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { ChatWindow } from './ChatWindow';
import { useChatbot } from '../hooks/useChatbot';

export const FloatingChatButton: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const navigate = useNavigate();

  const {
    messages,
    input,
    setInput,
    isStreaming,
    streamingText,
    streamingReasoning,
    errorMessage,
    setErrorMessage,
    quickPrompts,
    sendMessage,
  } = useChatbot();

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {/* Floating Popover Chat Window */}
      {isOpen && (
        <div className="mb-3 w-[92vw] sm:w-[420px] h-[560px] max-h-[82vh] bg-background text-foreground rounded-3xl border border-border shadow-2xl flex flex-col overflow-hidden animate-in fade-in slide-in-from-bottom-5 duration-200">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 bg-primary text-primary-foreground shrink-0 shadow-2xs">
            <div className="flex items-center gap-2.5">
              <div className="flex h-7 w-7 items-center justify-center rounded-xl bg-primary-foreground/20 text-primary-foreground">
                <BotIcon className="size-4" />
              </div>
              <div>
                <h3 className="text-xs font-semibold leading-tight">DUT AI Assistant</h3>
                <span className="text-[10px] text-primary-foreground/80">Trợ lý giải đáp học vụ</span>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => {
                  setIsOpen(false);
                  navigate('/dashboard/assistant');
                }}
                className="p-1.5 hover:bg-primary-foreground/15 rounded-lg text-primary-foreground transition-colors cursor-pointer"
                title="Mở toàn màn hình"
              >
                <Maximize2Icon className="size-3.5" />
              </button>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="p-1.5 hover:bg-primary-foreground/15 rounded-lg text-primary-foreground transition-colors cursor-pointer"
                title="Đóng khung chat"
              >
                <XIcon className="size-3.5" />
              </button>
            </div>
          </div>

          {/* Chat Window content */}
          <div className="flex-1 flex flex-col min-h-0">
            <ChatWindow
              messages={messages}
              input={input}
              onChangeInput={setInput}
              onSendMessage={sendMessage}
              isStreaming={isStreaming}
              streamingText={streamingText}
              streamingReasoning={streamingReasoning}
              errorMessage={errorMessage}
              onClearError={() => setErrorMessage(null)}
              quickPrompts={quickPrompts}
            />
          </div>
        </div>
      )}

      {/* Floating Action Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="group relative flex h-14 w-14 items-center justify-center rounded-full bg-primary hover:bg-primary/95 text-primary-foreground shadow-xl hover:shadow-primary/25 hover:scale-105 active:scale-95 transition-all duration-200 cursor-pointer"
        title="Trợ lý DUT AI"
      >
        {isOpen ? (
          <XIcon className="size-6" />
        ) : (
          <>
            <BotIcon className="size-6" />
            <span className="absolute -top-1 -right-1 flex h-4 w-4">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-4 w-4 bg-emerald-500" />
            </span>
          </>
        )}
      </button>
    </div>
  );
};
