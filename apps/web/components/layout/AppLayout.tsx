"use client";

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';

export default function AppLayout({ children }: { children: React.ReactNode }) {
    const { user, logout } = useAuth();
    const pathname = usePathname();

    // If simple layout (login), usually handled differently, but here we can conditionally render sidebar
    if (!user) {
        return <div className="min-h-screen bg-gray-50">{children}</div>;
    }

    const navItems = [
        { label: 'Dashboard', href: '/dashboard', icon: 'Home' },
        { label: 'Decks', href: '/decks', icon: 'Files' },
        { label: 'Templates', href: '/templates', icon: 'Layout' },
    ];

    return (
        <div className="flex h-screen bg-gray-50">
            {/* Sidebar */}
            <aside className="w-64 bg-slate-900 text-white flex flex-col">
                <div className="p-6 border-b border-slate-800">
                    <div className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-500">
                        Pultimate
                    </div>
                    <div className="text-xs text-slate-400 mt-1">AI-Powered Deck Audits</div>
                </div>

                <nav className="flex-1 p-4 space-y-1">
                    {navItems.map((item) => (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={`flex items-center px-4 py-3 rounded-md text-sm font-medium transition-colors ${pathname.startsWith(item.href)
                                    ? 'bg-blue-600 text-white'
                                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                                }`}
                        >
                            {item.label}
                        </Link>
                    ))}
                </nav>

                <div className="p-4 border-t border-slate-800">
                    <div className="flex items-center justify-between">
                        <div className="text-sm">
                            <div className="font-medium text-white">My Workspace</div>
                            <div className="text-xs text-slate-500">Free Plan</div>
                        </div>
                        <button onClick={logout} className="text-slate-400 hover:text-white">
                            Logout
                        </button>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-auto">
                <header className="bg-white border-b px-8 py-4 flex justify-between items-center sticky top-0 z-10">
                    <h1 className="text-xl font-semibold text-slate-800">
                        {navItems.find(i => pathname.startsWith(i.href))?.label || 'Overview'}
                    </h1>
                    <div className="flex items-center space-x-4">
                        <button className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 shadow-sm transition-all">
                            + New Audit
                        </button>
                    </div>
                </header>
                <div className="p-8">
                    {children}
                </div>
            </main>
        </div>
    );
}
