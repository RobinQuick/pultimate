"use client";

import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { fetchClient } from '@/lib/api';
import { useRouter } from 'next/navigation';

export default function DecksPage() {
    const [isUploading, setIsUploading] = useState(false);
    const router = useRouter();

    const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!e.target.files?.length) return;
        setIsUploading(true);

        try {
            const file = e.target.files[0];
            const formData = new FormData();
            formData.append('file', file);

            const res = await fetchClient<{ id: string }>('/api/v1/decks/upload', {
                method: 'POST',
                body: formData
            });

            // Trigger analysis immediately for UX flow
            await fetchClient(`/api/v1/analysis/${res.id}`, {
                method: 'POST',
                body: JSON.stringify({})
            });

            router.push(`/decks/${res.id}`); // Go to analysis view
        } catch (error) {
            console.error(error);
            alert("Upload failed");
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-slate-800">Decks</h2>
                <label className="cursor-pointer">
                    <span className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 shadow-sm transition-all inline-flex items-center">
                        {isUploading ? 'Uploading...' : '+ Upload Deck'}
                    </span>
                    <input type="file" className="hidden" accept=".pptx" onChange={handleUpload} disabled={isUploading} />
                </label>
            </div>

            {/* Empty State / List */}
            <Card>
                <CardHeader><CardTitle>Recent Uploads</CardTitle></CardHeader>
                <CardContent>
                    <div className="text-center py-12 text-slate-500">
                        No decks found. Upload your first presentation to start auditing.
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
