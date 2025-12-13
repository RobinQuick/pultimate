"use client";

import React from 'react';
import { Card, CardContent } from '@/components/ui/Card';

interface Finding {
    rule_id: string;
    severity: string;
    message: string;
    suggestion?: string;
}

interface FindingsPanelProps {
    findings: Finding[];
}

export const FindingsPanel: React.FC<FindingsPanelProps> = ({ findings }) => {
    if (findings.length === 0) {
        return (
            <div className="p-8 text-center text-slate-500 bg-slate-50 rounded-lg">
                <div className="text-sm">No issues found on this slide.</div>
                <div className="text-xs mt-1 text-slate-400">Perfect match with the template!</div>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {findings.map((f, i) => (
                <Card key={i} className="border-l-4 border-l-red-500">
                    <CardContent className="p-4">
                        <div className="flex justify-between items-start mb-1">
                            <span className="text-xs font-bold text-slate-500 uppercase tracking-wide">{f.rule_id}</span>
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${f.severity === 'HIGH' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'
                                }`}>
                                {f.severity}
                            </span>
                        </div>
                        <p className="text-sm font-medium text-slate-900">{f.message}</p>
                        {f.suggestion && (
                            <div className="mt-2 text-sm text-slate-600 bg-slate-50 p-2 rounded">
                                <span className="font-semibold text-slate-700">Fix: </span>
                                {f.suggestion}
                            </div>
                        )}
                    </CardContent>
                </Card>
            ))}
        </div>
    );
};
