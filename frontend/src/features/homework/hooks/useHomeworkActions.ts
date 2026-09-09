import { useReducer, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { message } from 'antd';

import { useAuth } from '@/features/auth';
import {
    useHomeworks,
    useDeleteHomework
} from './useHomeworks';

import { useUsers } from '@/features/users';
import { useTeams } from '@/features/teams';
import { homeworkService } from '@/features/homework/services/homework.service';
import type { Homework } from '@/features/homework/types/homework.types';

type HomeworkModalState = {
    isFormModalOpen: boolean;
    selectedHomework: Homework | null;
    editingHomework: Homework | null;
};

type HomeworkModalAction =
    | { type: 'OPEN_FORM'; payload?: Homework }
    | { type: 'CLOSE_FORM' };

const initialState: HomeworkModalState = {
    isFormModalOpen: false,
    selectedHomework: null,
    editingHomework: null,
};

function homeworkModalReducer(state: HomeworkModalState, action: HomeworkModalAction): HomeworkModalState {
    switch (action.type) {
        case 'OPEN_FORM':
            return { ...state, isFormModalOpen: true, editingHomework: action.payload ?? null };
        case 'CLOSE_FORM':
            return { ...state, isFormModalOpen: false, editingHomework: null };
        default:
            return state;
    }
}

export const useHomeworkActions = (activeTab: string) => {
    const { user, hasPermission, isAdminOrLeader } = useAuth();
    const [state, dispatch] = useReducer(homeworkModalReducer, initialState);


    const { data: allData, isLoading: allLoading, refetch: refetchAllHomeworks } = useHomeworks();
    const { data: usersData = [] } = useUsers();
    const { data: teamsData } = useTeams();
    const deleteHomeworkMutation = useDeleteHomework();

    const refreshData = useCallback(() => {
        refetchAllHomeworks();
    }, [refetchAllHomeworks]);

    const handleOpenCreate = () => dispatch({ type: 'OPEN_FORM' });

    const handleOpenEdit = async (homework: Homework) => {
        dispatch({ type: 'OPEN_FORM', payload: homework });
    };

    const handleDelete = async (id: number) => {
        try {
            await deleteHomeworkMutation.mutateAsync(id);
            message.success('Xóa bài tập thành công');
        } catch (error: unknown) {
            const err = error as { response?: { data?: { message?: string } } };
            message.error(err?.response?.data?.message || 'Xóa bài tập thất bại');
        }
    };



    const handleFormSuccess = () => {
        dispatch({ type: 'CLOSE_FORM' });
        refreshData();
    };




    return {
        state,
        dispatch,
        data: {
            allHomeworks: allData || [],
            users: usersData,
            teams: teamsData ?? [],
            allLoading
        },
        user,
        hasPermission,
        isAdminOrLeader,
        handlers: {
            handleOpenCreate,
            handleOpenEdit,
            handleDelete,
            handleFormSuccess,
            refreshData
        }
    };
};
