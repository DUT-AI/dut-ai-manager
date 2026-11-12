import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { chatbotService } from '../services/chatbot.service';

export const CHAT_SESSIONS_QUERY_KEY = ['chatbot', 'sessions'];

export function useChatSessions() {
  const queryClient = useQueryClient();

  const sessionsQuery = useQuery({
    queryKey: CHAT_SESSIONS_QUERY_KEY,
    queryFn: () => chatbotService.getSessions(),
    staleTime: 1000 * 60 * 2, // 2 minutes
  });

  const deleteSessionMutation = useMutation({
    mutationFn: (sessionId: string) => chatbotService.deleteSession(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CHAT_SESSIONS_QUERY_KEY });
    },
  });

  return {
    sessions: sessionsQuery.data || [],
    isLoading: sessionsQuery.isLoading,
    isError: sessionsQuery.isError,
    refetch: sessionsQuery.refetch,
    deleteSession: deleteSessionMutation.mutateAsync,
    isDeleting: deleteSessionMutation.isPending,
    deleteError: deleteSessionMutation.error,
  };
}
