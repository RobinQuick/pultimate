"use client";

import React from 'react';
import Image from 'next/image';

interface SlideThumbnailProps {
    index: number;
    isActive: boolean;
    issuesCount: number;
    onClick: () => void;
    imageUrl?: string; // Optional (if pre-rendered)
}

export const SlideThumbnail: React.FC<SlideThumbnailProps> = ({
    index,
    isActive,
    issuesCount,
    onClick,
    imageUrl
}) => {
    return (
        <div
            onClick={onClick}
            className={`cursor-pointer group relative flex flex-col items-center p-2 rounded-lg transition-all ${isActive ? 'bg-blue-50 ring-2 ring-blue-500' : 'hover:bg-slate-100'
                }`}
        >
            <div className="relative aspect-video w-full bg-slate-200 rounded overflow-hidden border border-slate-300">
                {imageUrl ? (
                    <div className="w-full h-full bg-cover bg-center" style={{ backgroundImage: `url(${imageUrl})` }} />
                ) : (
                    <div className="flex items-center justify-center h-full text-slate-400 text-xs">
                        Slide {index + 1}
                    </div>
                )}
            </div>

            <div className="mt-2 w-full flex justify-between items-center px-1">
                <span className={`text-xs font-medium ${isActive ? 'text-blue-700' : 'text-slate-600'}`}>
                    Slide {index + 1}
                </span>
                {issuesCount > 0 && (
                    <span className="flex items-center justify-center min-w-[1.25rem] h-5 px-1 bg-red-100 text-red-600 text-[10px] font-bold rounded-full border border-red-200">
                        {issuesCount}
                    </span>
                )}
            </div>
        </div>
    );
};
