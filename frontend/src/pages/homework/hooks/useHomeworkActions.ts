import { useReducer, useCallback } from 'react';
import { message } from 'antd';
import { useAuth } from '@/context/AuthContext';
import { 
    useMyHomeworks, 
    useHomeworks, 
    useDeleteHomework,
    useUsers,
    useTeams
} from '@/hooks';
import { homeworkService } from '@/services/api/homework.service';
import type { Homework } from '@/types/homework.types';

type HomeworkModalState = {
    isFormModalOpen: boolean;
    isSubmitModalOpen: boolean;
    isSubmissionsDrawerOpen: boolean;
    selectedHomework: Homework | null;
    editingHomework: Homework | null;
    currentAssignees: number[];
    assigneesLoading: boolean;
};

type HomeworkModalAction =
    | { type: 'OPEN_FORM'; payload?: Homework }
    | { type: 'CLOSE_FORM' }
    | { type: 'OPEN_SUBMIT'; payload: Homework }
    | { type: 'CLOSE_SUBMIT' }
    | { type: 'OPEN_SUBMISSIONS'; payload: Homework }
    | { type: 'CLOSE_SUBMISSIONS' }
    | { type: 'SET_ASSIGNEES'; payload: number[] };

const initialState: HomeworkModalState = {
    isFormModalOpen: false,
    isSubmitModalOpen: false,
    isSubmissionsDrawerOpen: false,
    selectedHomework: null,
    editingHomework: null,
    currentAssignees: [],
    assigneesLoading: false,
};

function homeworkModalReducer(state: HomeworkModalState, action: HomeworkModalAction): HomeworkModalState {
    switch (action.type) {
        case 'OPEN_FORM':
            return { ...state, isFormModalOpen: true, editingHomework: action.payload ?? null, currentAssignees: [], assigneesLoading: !!action.payload };
        case 'CLOSE_FORM':
            return { ...state, isFormModalOpen: false, editingHomework: null };
        case 'OPEN_SUBMIT':
            return { ...state, isSubmitModalOpen: true, selectedHomework: action.payload };
        case 'CLOSE_SUBMIT':
            return { ...state, isSubmitModalOpen: false, selectedHomework: null };
        case 'OPEN_SUBMISSIONS':
            return { ...state, isSubmissionsDrawerOpen: true, selectedHomework: action.payload };
        case 'CLOSE_SUBMISSIONS':
            return { ...state, isSubmissionsDrawerOpen: false, selectedHomework: null };
        case 'SET_ASSIGNEES':
            return { ...state, currentAssignees: action.payload, assigneesLoading: false };
        default:
            return state;
    }
}

export const useHomeworkActions = (activeTab: string) => {
    const { user, hasPermission, isAdminOrLeader } = useAuth();
    const [state, dispatch] = useReducer(homeworkModalReducer, initialState);
    
    const { data: myData, isLoading: myLoading, refetch: refetchMyHomeworks } = useMyHomeworks();
    const { data: allData, isLoading: allLoading, refetch: refetchAllHomeworks } = useHomeworks();
    const { data: usersData = [] } = useUsers();
    const { data: teamsData = [] } = useTeams();
    const deleteHomeworkMutation = useDeleteHomework();

    const refreshData = useCallback(() => {
        if (activeTab === '1') {
            refetchMyHomeworks();
        } else {
            refetchAllHomeworks();
        }
    }, [activeTab, refetchMyHomeworks, refetchAllHomeworks]);

    const handleOpenCreate = () => dispatch({ type: 'OPEN_FORM' });

    const handleOpenEdit = async (homework: Homework) => {
        dispatch({ type: 'OPEN_FORM', payload: homework });
        try {
            const submissions = await homeworkService.getSubmissions(homework.id);
            dispatch({ type: 'SET_ASSIGNEES', payload: submissions?.map((s: any) => s.owner_id) || [] });
        } catch {
            dispatch({ type: 'SET_ASSIGNEES', payload: [] });
        }
    };

    const handleDelete = async (id: number) => {
        try {
            await deleteHomeworkMutation.mutateAsync(id);
            message.success('Xóa bài tập thành công');
        } catch (error: any) {
            message.error(error?.response?.data?.message || 'Xóa bài tập thất bại');
        }
    };

    const handleOpenSubmit = (homework: Homework) => dispatch({ type: 'OPEN_SUBMIT', payload: homework });
    const handleViewSubmissions = (homework: Homework) => dispatch({ type: 'OPEN_SUBMISSIONS', payload: homework });

    const handleFormSuccess = () => {
        dispatch({ type: 'CLOSE_FORM' });
        refreshData();
    };

    const handleSubmitSuccess = () => {
        dispatch({ type: 'CLOSE_SUBMIT' });
        refetchMyHomeworks();
    };

    return {
        state,
        dispatch,
        data: {
            myHomeworks: myData || [],
            allHomeworks: allData || [],
            users: usersData,
            teams: teamsData,
            myLoading,
            allLoading
        },
        user,
        hasPermission,
        isAdminOrLeader,
        handlers: {
            handleOpenCreate,
            handleOpenEdit,
            handleDelete,
            handleOpenSubmit,
            handleViewSubmissions,
            handleFormSuccess,
            handleSubmitSuccess,
            refreshData
        }
    };
};
