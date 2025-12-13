"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { fetchClient } from '@/lib/api';

interface User {
    id: string;
    email: string;
    tenant_id: string;
}

interface AuthContextType {
    user: User | null;
    login: (token: string, refresh: string) => void;
    logout: () => void;
    isLoading: boolean;
    isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const router = useRouter();
    const pathname = usePathname();

    useEffect(() => {
        // Init from localStorage
        const token = localStorage.getItem('access_token');
        if (token) {
            // In real app, verify token or fetch /me
            // For demo, we just assume validity until 401
            // Or decode token to get basic user info if stored
            setUser({ id: 'stub', email: 'user@example.com', tenant_id: 'stub' });
        }
        setIsLoading(false);
    }, []);

    const login = (accessToken: string, refreshToken: string) => {
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
        setUser({ id: 'stub', email: 'user@example.com', tenant_id: 'stub' });
        router.push('/dashboard');
    };

    const logout = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setUser(null);
        router.push('/login');
    };

    // Protected Route Logic
    useEffect(() => {
        const publicPaths = ['/login', '/register'];
        if (!isLoading && !user && !publicPaths.includes(pathname)) {
            router.push('/login');
        }
    }, [user, isLoading, pathname, router]);

    return (
        <AuthContext.Provider value={{ user, login, logout, isLoading, isAuthenticated: !!user }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
