"use client";

import { useAuth } from '@/lib/auth-context';
import { Card, CardContent } from '@/components/ui/Card';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

export default function DashboardPage() {
    const { user } = useAuth();
    const [counts, setCounts] = useState({ decks: 0, templates: 0, jobs: 0 });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function loadData() {
            try {
                // Parallel fetch for speed
                const [decks, templates] = await Promise.all([
                    api.decks.list(),
                    api.templates.list(),
                    // api.rebuildJobs.list() // Optional, heavy?
                ]);
                setCounts({
                    decks: decks.length,
                    templates: templates.length,
                    jobs: 0 // Placeholder or fetch if needed
                });
            } catch (e) {
                console.error("Dashboard fetch error", e);
            } finally {
                setLoading(false);
            }
        }
        loadData();
    }, []);

    const showOnboarding = counts.templates === 0 || counts.decks === 0;

    if (loading) return <div className="p-8">Loading dashboard...</div>;

    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-bold">Welcome, {user?.email}</h1>

            {showOnboarding ? (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
                    <h2 className="text-xl font-semibold text-blue-900 mb-4">🚀 Let's get started</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Step 1: Template */}
                        <div className={`p-4 rounded-lg check-step ${counts.templates > 0 ? 'bg-green-50 border-green-200 border' : 'bg-white border-blue-200 border shadow-sm'}`}>
                            <div className="flex items-center gap-3 mb-2">
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${counts.templates > 0 ? 'bg-green-500 text-white' : 'bg-blue-600 text-white'}`}>
                                    {counts.templates > 0 ? '✓' : '1'}
                                </div>
                                <h3 className="font-medium">Upload a Master Template</h3>
                            </div>
                            <p className="text-sm text-slate-600 mb-4 ml-11">
                                Your corporate brand guideline file (.potx or .pptx)
                            </p>
                            {counts.templates === 0 && (
                                <Link href="/app/templates" className="ml-11 inline-block px-4 py-2 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700">
                                    Upload Template →
                                </Link>
                            )}
                        </div>

                        {/* Step 2: Deck */}
                        <div className={`p-4 rounded-lg check-step ${counts.decks > 0 ? 'bg-green-50 border-green-200 border' : 'bg-white border-slate-200 border opacity-90'}`}>
                            <div className="flex items-center gap-3 mb-2">
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${counts.decks > 0 ? 'bg-green-500 text-white' : (counts.templates === 0 ? 'bg-slate-300 text-slate-500' : 'bg-blue-600 text-white')}`}>
                                    {counts.decks > 0 ? '✓' : '2'}
                                </div>
                                <h3 className="font-medium">Upload a Presentation</h3>
                            </div>
                            <p className="text-sm text-slate-600 mb-4 ml-11">
                                An existing messy deck to be rebuilt
                            </p>
                            {counts.decks === 0 && counts.templates > 0 && (
                                <Link href="/app/decks" className="ml-11 inline-block px-4 py-2 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700">
                                    Upload Deck →
                                </Link>
                            )}
                        </div>
                    </div>
                </div>
            ) : (
                // Regular Stats
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <Card className="bg-gradient-to-br from-blue-50 to-white border-blue-100">
                        <CardContent className="pt-6">
                            <div className="text-2xl font-bold text-blue-600">{counts.templates}</div>
                            <div className="text-sm text-slate-600 mt-1">Active Templates</div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardContent className="pt-6">
                            <div className="text-2xl font-bold text-slate-800">{counts.decks}</div>
                            <div className="text-sm text-slate-600 mt-1">Source Decks</div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardContent className="pt-6 flex flex-col items-start">
                            <h3 className="text-lg font-medium mb-2">Ready to Rebuild?</h3>
                            <Link href="/app/rebuild" className="px-4 py-2 bg-black text-white rounded hover:bg-slate-800 transition-colors w-full text-center">
                                Start New Job
                            </Link>
                        </CardContent>
                    </Card>
                </div>
            )}

            <h3 className="text-lg font-medium text-slate-900 mt-8">Quick Actions</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Link href="/app/decks" className="p-4 bg-white border rounded-lg hover:border-blue-400 hover:shadow-md transition-all group">
                    <div className="font-medium text-slate-900 group-hover:text-blue-600">New Upload</div>
                    <div className="text-sm text-slate-500 mt-1">Upload and scan a PPTX</div>
                </Link>
                <Link href="/app/rebuild" className="p-4 bg-white border rounded-lg hover:border-blue-400 hover:shadow-md transition-all group">
                    <div className="font-medium text-slate-900 group-hover:text-blue-600">Rebuild Deck</div>
                    <div className="text-sm text-slate-500 mt-1">Apply template to deck</div>
                </Link>
            </div>
        </div>
    );
}
