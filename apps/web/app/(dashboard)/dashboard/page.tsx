"use client";

import { useAuth } from '@/lib/auth-context';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import Link from 'next/link';

export default function DashboardPage() {
    const { user } = useAuth();

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card className="bg-gradient-to-br from-blue-50 to-white border-blue-100">
                    <CardContent className="pt-6">
                        <div className="text-2xl font-bold text-blue-600">85%</div>
                        <div className="text-sm text-slate-600 mt-1">Avg Compliance Score</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="text-2xl font-bold text-slate-800">12</div>
                        <div className="text-sm text-slate-600 mt-1">Decks Audited (This Week)</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="text-2xl font-bold text-green-600">340</div>
                        <div className="text-sm text-slate-600 mt-1">Hours Saved (Est.)</div>
                    </CardContent>
                </Card>
            </div>

            <h3 className="text-lg font-medium text-slate-900">Quick Actions</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Link href="/decks" className="p-4 bg-white border rounded-lg hover:border-blue-400 hover:shadow-md transition-all group">
                    <div className="font-medium text-slate-900 group-hover:text-blue-600">New Audit</div>
                    <div className="text-sm text-slate-500 mt-1">Upload and scan a PPTX</div>
                </Link>
                <Link href="/templates" className="p-4 bg-white border rounded-lg hover:border-blue-400 hover:shadow-md transition-all group">
                    <div className="font-medium text-slate-900 group-hover:text-blue-600">Manage Templates</div>
                    <div className="text-sm text-slate-500 mt-1">Update corporate assets</div>
                </Link>
            </div>
        </div>
    );
}
