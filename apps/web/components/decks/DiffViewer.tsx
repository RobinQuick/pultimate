"use client";

import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';

interface DiffViewerProps {
    originalUrl?: string; // e.g. /api/v1/render/slide/...
    fixedUrl?: string;
    ssimScore?: number;
}

export const DiffViewer: React.FC<DiffViewerProps> = ({ originalUrl, fixedUrl, ssimScore }) => {
    const [viewMode, setViewMode] = useState<'ORIGINAL' | 'FIXED' | 'DIFF'>('ORIGINAL');

    return (
        <div className="flex flex-col h-full">
            <div className="flex justify-between items-center mb-4 px-4 pt-4">
                <div className="bg-slate-100 p-1 rounded-md flex space-x-1">
                    <button
                        onClick={() => setViewMode('ORIGINAL')}
                        className={`px-3 py-1 rounded text-sm font-medium transition-all ${viewMode === 'ORIGINAL' ? 'bg-white shadow text-slate-900' : 'text-slate-500 hover:text-slate-900'
                            }`}
                    >
                        Original
                    </button>
                    <button
                        onClick={() => setViewMode('FIXED')}
                        className={`px-3 py-1 rounded text-sm font-medium transition-all ${viewMode === 'FIXED' ? 'bg-white shadow text-slate-900' : 'text-slate-500 hover:text-slate-900'
                            }`}
                    >
                        Preview Fix
                    </button>
                </div>

                {ssimScore !== undefined && (
                    <div className="text-sm text-slate-600">
                        SSIM Score: <span className="font-bold text-slate-900">{ssimScore.toFixed(2)}</span>
                    </div>
                )}
            </div>

            <div className="flex-1 bg-slate-200 relative overflow-hidden flex items-center justify-center">
                {/* Placeholder for Image - in real app would use next/image with proper sizing */}
                <div className="bg-white shadow-lg w-[80%] aspect-video flex items-center justify-center text-slate-400">
                    {viewMode === 'ORIGINAL' && "Original Slide Image Placeholder"}
                    {viewMode === 'FIXED' && "Fixed Slide Image Placeholder (Simulated)"}
                </div>
            </div>

            <div className="p-4 bg-white border-t text-xs text-slate-500 text-center">
                Use the toggle above to verify changes before applying.
            </div>
        </div>
    );
};
