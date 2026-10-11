import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { teamService } from '@/features/teams/services/team.service';
import type { TeamCreate, TeamUpdate } from '@/features/teams/types/team.types';

// Query Keys
const teamKeys = {
  all: ['teams'] as const,
  options: ['teams', 'options'] as const,
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

export const useTeamOptions = () => {
  return useQuery({
    queryKey: teamKeys.options,
    queryFn: async () => {
      const response = await teamService.getTeamOptions();
      return response.data ?? [];
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
