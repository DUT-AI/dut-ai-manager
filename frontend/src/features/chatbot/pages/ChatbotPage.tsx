import React, { useState } from 'react';
import {
  ChatSessionSidebar,
  ChatWindow,
  ChatHeader,
  DeleteSessionDialog,
} from '../components';
import { useChatSessions } from '../hooks/useChatSessions';

export const ChatbotPage: React.FC = () => {
  const { sessions, deleteSession, isDeleting } = useChatSessions();
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);

  // Sidebar collapsible state: default open on desktop
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // Delete session modal state
  const [deletingSessionId, setDeletingSessionId] = useState<string | null>(null);

  const handleRequestDeleteSession = (id: string) => {
    setDeletingSessionId(id);
  };

  const handleConfirmDelete = async () => {
    if (!deletingSessionId) return;
    try {
      await deleteSession(deletingSessionId);
      if (activeSessionId === deletingSessionId) {
        setActiveSessionId(null);
      }
    } catch {
      // error handled in mutation
    } finally {
      setDeletingSessionId(null);
    }
  };

  return (
    <div className="flex h-[calc(100vh-4.5rem)] w-full overflow-hidden bg-background text-foreground rounded-2xl border border-border/80 shadow-xs relative">
      {/* Collapsible Left Sidebar */}
      <ChatSessionSidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        onSelectSession={(id) => {
          setActiveSessionId(id);
          // On mobile, automatically close sidebar after choosing a session
          if (window.innerWidth < 1024) {
            setIsSidebarOpen(false);
          }
        }}
        onNewChat={() => {
          setActiveSessionId(null);
          if (window.innerWidth < 1024) {
            setIsSidebarOpen(false);
          }
        }}
        onRequestDeleteSession={handleRequestDeleteSession}
      />

      {/* Main Chat Orchestration Area */}
      <main className="flex flex-col flex-1 h-full min-w-0 bg-background">
        {/* Top Header */}
        <ChatHeader
          isSidebarOpen={isSidebarOpen}
          onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
          onNewChat={() => setActiveSessionId(null)}
        />

        {/* Chat Window encapsulates its own useChatbot hook */}
        <ChatWindow
          sessionId={activeSessionId}
          onSessionCreated={(newId) => setActiveSessionId(newId)}
        />
      </main>

      {/* shadcn Delete Confirmation Dialog */}
      <DeleteSessionDialog
        isOpen={deletingSessionId !== null}
        onOpenChange={(open) => {
          if (!open) setDeletingSessionId(null);
        }}
        onConfirm={handleConfirmDelete}
        isDeleting={isDeleting}
      />
    </div>
  );
};

export default ChatbotPage;
