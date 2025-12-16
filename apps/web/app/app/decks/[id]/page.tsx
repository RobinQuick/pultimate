"use client";

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { fetchClient } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { SlideThumbnail } from '@/components/decks/SlideThumbnail';
import { FindingsPanel } from '@/components/decks/FindingsPanel';
import { DiffViewer } from '@/components/decks/DiffViewer';

interface DeckAnalysis {
    id: string;
    filename: string;
    status: string;
    rendering_enabled: boolean; // Field from API
    slides: {
        index: number;
        findings: any[];
    }[];
}

export default function AnalysisPage() {
    const { id } = useParams();
    const [data, setData] = useState<DeckAnalysis | null>(null);
    const [selectedSlide, setSelectedSlide] = useState(0);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        fetchClient<DeckAnalysis>(`/api/v1/analysis/${id}`)
            .then(res => {
                if (!res.slides) res.slides = [];
                setData(res);
            })
            .catch(console.error)
            .finally(() => setIsLoading(false));
    }, [id]);

    if (isLoading) return <div className="p-12 text-center">Loading Analysis...</div>;
    if (!data) return <div className="p-12 text-center text-red-500">Failed to load analysis</div>;

    const currentSlide = data.slides[selectedSlide];

    return (
        <div className="flex h-[calc(100vh-6rem)] -m-8">
            {/* Left: Slide List */}
            <div className="w-64 border-r bg-white overflow-y-auto p-4 space-y-4">
                {/* ... existing thumbnail list ... */}
                {data.slides.map((slide) => (
                    <SlideThumbnail
                        key={slide.index}
                        index={slide.index}
                        isActive={slide.index === selectedSlide}
                        issuesCount={slide.findings.length}
                        onClick={() => setSelectedSlide(slide.index)}
                    />
                ))}
            </div>

            {/* Middle: Preview/Diff */}
            <div className="flex-1 bg-slate-100 flex flex-col items-center justify-center p-4">
                {data.rendering_enabled ? (
                    <DiffViewer ssimScore={0.92} />
                ) : (
                    <div className="text-center text-slate-500 bg-white p-8 rounded shadow-sm border">
                        <div className="text-xl font-semibold mb-2">Visual Preview Disabled</div>
                        <p className="text-sm">Rendering pipeline is active is turned off in settings.</p>
                        <p className="text-xs text-slate-400 mt-4">Feature Flag: RENDERING_ENABLED=False</p>
                    </div>
                )}
            </div>

            {/* Right: Findings */}
            <div className="w-96 border-l bg-white overflow-y-auto flex flex-col">
                <div className="p-6 border-b">
                    <h2 className="text-lg font-bold text-slate-800">Findings</h2>
                    {currentSlide && (
                        <div className="text-sm text-slate-500 mt-1">
                            Slide {selectedSlide + 1} • {currentSlide.findings.length} Issues
                        </div>
                    )}
                </div>
                <div className="flex-1 p-6">
                    {currentSlide && <FindingsPanel findings={currentSlide.findings} />}
                </div>
            </div>
        </div>
    );
}
