import React from "react";
import { Button } from "@/components/ui/button";
import {
  BotIcon,
  PanelLeftCloseIcon,
  PanelLeftIcon,
  PlusIcon,
} from "lucide-react";

interface ChatHeaderProps {
  isSidebarOpen: boolean;
  onToggleSidebar: () => void;
  onNewChat: () => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  isSidebarOpen,
  onToggleSidebar,
  onNewChat,
}) => {
  return (
    <header className="flex items-center justify-between px-4 py-2.5 border-b border-border/50 bg-background/95 backdrop-blur-sm shrink-0">
      <div className="flex items-center gap-3">
        {/* Toggle Sidebar Button */}
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={onToggleSidebar}
          className="size-8 rounded-lg text-muted-foreground hover:text-foreground"
          title={isSidebarOpen ? "Thu gọn thanh bên" : "Mở rộng thanh bên"}
        >
          {isSidebarOpen ? (
            <PanelLeftCloseIcon className="size-4" />
          ) : (
            <PanelLeftIcon className="size-4" />
          )}
        </Button>

        {/* Brand & Assistant Info */}
        <div className="flex items-center gap-2.5">
          <div className="flex size-7 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold shadow-2xs">
            <BotIcon className="size-4" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-foreground leading-none">
              DUT AI Assistant
            </h2>
            <p className="text-[11px] text-muted-foreground mt-0.5">
              Giải đáp quy chế & điều hành học vụ nội bộ
            </p>
          </div>
        </div>
      </div>

      {/* Right Action */}
      <div className="flex items-center gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={onNewChat}
          className="gap-1.5 text-xs rounded-xl h-8 px-3 border-border/60 shadow-none hover:bg-muted text-foreground"
        >
          <PlusIcon className="size-3.5 text-muted-foreground" />
          <span className="hidden sm:inline">Đoạn chat mới</span>
        </Button>
      </div>
    </header>
  );
};
