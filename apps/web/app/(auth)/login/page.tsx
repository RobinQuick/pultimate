"use client";

import React, { useState } from 'react';
import { useAuth } from '@/lib/auth-context';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { fetchClient } from '@/lib/api';

export default function LoginPage() {
    const { login } = useAuth();
    const [email, setEmail] = useState('user@decklint.com');
    const [password, setPassword] = useState('password');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        try {
            // Use FormData for OAuth2 password flow
            const formData = new FormData();
            formData.append('username', email); // OAuth2 expects username
            formData.append('password', password);

            const res = await fetchClient<{ access_token: string, token_type: string }>('/api/v1/auth/token', {
                method: 'POST',
                body: formData
            });

            login(res.access_token, "");
        } catch (err: any) {
            setError(err.message || 'Login failed');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
            <Card className="w-full max-w-md shadow-lg">
                <CardHeader className="text-center border-b-0 pb-2">
                    <div className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600 mb-2">
                        Pultimate
                    </div>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        {error && (
                            <div className="bg-red-50 text-red-600 p-3 rounded text-sm border border-red-100">
                                {error}
                            </div>
                        )}
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-700">Email</label>
                            <input
                                type="text"
                                className="w-full h-10 px-3 rounded-md border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-700">Password</label>
                            <input
                                type="password"
                                className="w-full h-10 px-3 rounded-md border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                        </div>
                        <Button type="submit" className="w-full" disabled={isLoading}>
                            {isLoading ? 'Signing In...' : 'Sign In'}
                        </Button>
                    </form>
                    <div className="mt-4 text-center text-xs text-slate-400">
                        Demo Creds: user@decklint.com / password
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
