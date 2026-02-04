import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/api/auth.service';
import type { UserResponse } from '../types/user.types';

interface AuthContextType {
    user: UserResponse | null;
    loading: boolean;
    isAuthenticated: boolean;
    login: () => Promise<void>;
    logout: () => Promise<void>;
    hasPermission: (permission: string) => boolean;
    isAdminOrLeader: () => boolean;
    refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<UserResponse | null>(null);
    const [loading, setLoading] = useState(true);

    const fetchUser = async () => {
        try {
            const response = await authService.getMe();
            if (response.is_success && response.data) {
                setUser(response.data);
            } else {
                setUser(null);
            }
        } catch (error) {
            console.error('Failed to fetch user:', error);
            setUser(null);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUser();
    }, []);

    const login = async () => {
        await fetchUser();
    };

    const logout = async () => {
        try {
            await authService.logout();
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            setUser(null);
        }
    };

    const hasPermission = (permission: string): boolean => {
        if (!user) return false;
        const role = user.role_name?.toLowerCase();
        if (role === 'admin') return true;
        return user.permissions?.includes(permission) || false;
    };

    const isAdminOrLeader = (): boolean => {
        if (!user) return false;
        const role = user.role_name?.toLowerCase();
        return role === 'admin' || role === 'leader';
    };

    const value = {
        user,
        loading,
        isAuthenticated: !!user,
        login,
        logout,
        hasPermission,
        isAdminOrLeader,
        refreshUser: fetchUser,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
