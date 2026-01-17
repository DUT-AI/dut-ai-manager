import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { teamService } from '@/services/api/team.service';
import type { TeamCreate, TeamUpdate } from '@/types/team.types';

// Query Keys
export const teamKeys = {
  all: ['teams'] as const,
  detail: (id: number) => ['teams', id] as const,
};

// Queries
export const useTeams = () => {
  return useQuery({
    queryKey: teamKeys.all,
    queryFn: async () => {
      const response = await teamService.getTeams();
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useTeam = (id: number) => {
  return useQuery({
    queryKey: teamKeys.detail(id),
    queryFn: async () => {
      const response = await teamService.getTeam(id);
      return response.data;
    },
    enabled: !!id,
  });
};

// Mutations
export const useCreateTeam = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: TeamCreate) => teamService.createTeam(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: teamKeys.all });
    },
  });
};

export const useUpdateTeam = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: TeamUpdate }) => 
      teamService.updateTeam(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: teamKeys.all });
    },
  });
};

export const useDeleteTeam = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: number) => teamService.deleteTeam(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: teamKeys.all });
    },
  });
};
