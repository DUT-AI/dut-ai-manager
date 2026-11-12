import React, { useMemo } from "react";
import { Button } from "@/components/ui/button";
import {
  PlusIcon,
  MessageSquareIcon,
  Trash2Icon,
  XIcon,
} from "lucide-react";
import type { ChatSession, ChatSessionGroup, SessionDateGroupKey } from "../types/chatbot.types";

interface ChatSessionSidebarProps {
  sessions: ChatSession[];
  activeSessionId: number | null;
  isOpen: boolean;
  onClose: () => void;
  onSelectSession: (id: number) => void;
  onNewChat: () => void;
  onRequestDeleteSession: (id: number) => void;
}

export const ChatSessionSidebar: React.FC<ChatSessionSidebarProps> = ({
  sessions,
  activeSessionId,
  isOpen,
  onClose,
  onSelectSession,
  onNewChat,
  onRequestDeleteSession,
}) => {
  // Group sessions by date
  const groupedSessions = useMemo<ChatSessionGroup[]>(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    const sevenDaysAgo = new Date(today);
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

    const groups: Record<string, ChatSession[]> = {
      "Hôm nay": [],
      "Hôm qua": [],
      "7 ngày trước": [],
      "Cũ hơn": [],
    };

    sessions.forEach((session) => {
      const sessionDate = new Date(session.created_at);
      sessionDate.setHours(0, 0, 0, 0);

      if (sessionDate.getTime() >= today.getTime()) {
        groups["Hôm nay"].push(session);
      } else if (sessionDate.getTime() >= yesterday.getTime()) {
        groups["Hôm qua"].push(session);
      } else if (sessionDate.getTime() >= sevenDaysAgo.getTime()) {
        groups["7 ngày trước"].push(session);
      } else {
        groups["Cũ hơn"].push(session);
      }
    });

    return (Object.keys(groups) as Array<keyof typeof groups>)
      .filter((label) => groups[label].length > 0)
      .map((label) => ({
        groupLabel: label as SessionDateGroupKey,
        sessions: groups[label],
      }));
  }, [sessions]);

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/30 backdrop-blur-xs lg:hidden transition-opacity"
          onClick={onClose}
        />
      )}

      {/* Sidebar Panel */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex flex-col bg-sidebar/80 dark:bg-slate-900 border-r border-border/50 transition-all duration-300 ease-in-out shrink-0 ${
          isOpen ? "w-64 translate-x-0" : "-translate-x-full lg:translate-x-0 lg:w-0 lg:opacity-0 pointer-events-none"
        } lg:relative lg:z-0 lg:pointer-events-auto`}
      >
        {/* Top Action Header */}
        <div className="p-3 border-b border-border/40 flex items-center gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={onNewChat}
            className="flex-1 justify-start gap-2 bg-background hover:bg-muted text-foreground text-xs font-medium border-border/60 shadow-2xs rounded-xl h-9 px-3"
          >
            <PlusIcon className="size-4 text-muted-foreground" />
            <span>Đoạn chat mới</span>
          </Button>

          {/* Close button for Mobile */}
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="size-8 rounded-lg lg:hidden text-muted-foreground hover:text-foreground"
          >
            <XIcon className="size-4" />
          </Button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-4 scrollbar-thin">
          {sessions.length === 0 ? (
            <div className="text-center py-10 px-3 text-xs text-muted-foreground/60">
              Chưa có lịch sử hội thoại
            </div>
          ) : (
            groupedSessions.map((group) => (
              <div key={group.groupLabel} className="space-y-0.5">
                <div className="px-2.5 py-1 text-[11px] font-medium tracking-wider text-muted-foreground/60 uppercase">
                  {group.groupLabel}
                </div>

                {group.sessions.map((session) => {
                  const isActive = session.id === activeSessionId;
                  return (
                    <div
                      key={session.id}
                      onClick={() => onSelectSession(session.id)}
                      className={`group relative flex items-center justify-between px-2.5 py-2 rounded-xl text-xs font-medium cursor-pointer transition-colors ${
                        isActive
                          ? "bg-accent text-accent-foreground font-semibold"
                          : "text-muted-foreground hover:text-foreground hover:bg-muted/60"
                      }`}
                    >
                      <div className="flex items-center gap-2 min-w-0 flex-1 pr-1.5">
                        <MessageSquareIcon
                          className={`size-3.5 shrink-0 ${
                            isActive ? "text-foreground" : "text-muted-foreground/60"
                          }`}
                        />
                        <span className="truncate leading-tight">
                          {session.title || "Cuộc trò chuyện mới"}
                        </span>
                      </div>

                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onRequestDeleteSession(session.id);
                        }}
                        className="opacity-0 group-hover:opacity-100 hover:text-destructive text-muted-foreground/60 p-1 rounded-md hover:bg-background/80 transition-all shrink-0 cursor-pointer"
                        title="Xóa phiên"
                      >
                        <Trash2Icon className="size-3.5" />
                      </button>
                    </div>
                  );
                })}
              </div>
            ))
          )}
        </div>

        {/* Footer Info */}
        <div className="p-3 border-t border-border/40 text-[11px] text-muted-foreground/60 text-center select-none">
          Lưu tối đa 5 phiên gần nhất
        </div>
      </aside>
    </>
  );
};
