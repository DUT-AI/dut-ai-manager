import React, { useState } from 'react';
import {
  ChatSessionSidebar,
  ChatWindow,
  ChatHeader,
  DeleteSessionDialog,
} from '../components';
import { useChatSessions } from '../hooks/useChatSessions';
import { useChatbot } from '../hooks/useChatbot';

export const ChatbotPage: React.FC = () => {
  const { sessions, deleteSession, isDeleting } = useChatSessions();
  const {
    sessionId,
    messages,
    input,
    setInput,
    isStreaming,
    streamingText,
    streamingReasoning,
    activeTools,
    errorMessage,
    setErrorMessage,
    quickPrompts,
    sendMessage,
    startNewChat,
    selectSession,
  } = useChatbot();

  // Sidebar collapsible state: default open on desktop
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // Delete session modal state
  const [deletingSessionId, setDeletingSessionId] = useState<number | null>(null);

  const handleRequestDeleteSession = (id: number) => {
    setDeletingSessionId(id);
  };

  const handleConfirmDelete = async () => {
    if (!deletingSessionId) return;
    try {
      await deleteSession(deletingSessionId);
      if (sessionId === deletingSessionId) {
        startNewChat();
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
        activeSessionId={sessionId}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        onSelectSession={(id) => {
          selectSession(id);
          // On mobile, automatically close sidebar after choosing a session
          if (window.innerWidth < 1024) {
            setIsSidebarOpen(false);
          }
        }}
        onNewChat={() => {
          startNewChat();
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
          onNewChat={startNewChat}
        />

        {/* Chat Window */}
        <ChatWindow
          messages={messages}
          input={input}
          onChangeInput={setInput}
          onSendMessage={sendMessage}
          isStreaming={isStreaming}
          streamingText={streamingText}
          streamingReasoning={streamingReasoning}
          activeTools={activeTools}
          errorMessage={errorMessage}
          onClearError={() => setErrorMessage(null)}
          quickPrompts={quickPrompts}
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
