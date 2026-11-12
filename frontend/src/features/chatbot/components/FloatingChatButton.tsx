import React, { useState } from 'react';
import { BotIcon, XIcon, Maximize2Icon } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { ChatWindow } from './ChatWindow';

export const FloatingChatButton: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const navigate = useNavigate();

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
            <ChatWindow />
          </div>
        </div>
      )}

      {/* Floating Action Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex size-14 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-xl hover:bg-primary/90 hover:scale-105 active:scale-95 transition-all duration-200 cursor-pointer group focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
        aria-label={isOpen ? 'Đóng cửa sổ trò chuyện' : 'Mở trợ lý ảo'}
      >
        {isOpen ? (
          <XIcon className="size-6 transition-transform group-hover:rotate-90 duration-200" />
        ) : (
          <BotIcon className="size-6 animate-pulse" />
        )}
      </button>
    </div>
  );
};
