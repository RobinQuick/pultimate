"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { AlertTriangle, CheckCircle, XCircle, Download, FileText, Image as ImageIcon } from "lucide-react";

export default function JobDashboard({ params }: { params: { id: string } }) {
    const [job, setJob] = useState<any>(null);
    const [activeTab, setActiveTab] = useState<"overview" | "proof" | "deliver">("overview");

    useEffect(() => {
        // Poll for job status
        const interval = setInterval(async () => {
            try {
                const data = await api.getJob(params.id);
                setJob(data);
                if (data.status === "COMPLETED" || data.status === "FAILED") {
                    clearInterval(interval);
                }
            } catch (e) {
                console.error(e);
            }
        }, 2000);
        return () => clearInterval(interval);
    }, [params.id]);

    if (!job) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-900 text-white">
                <div className="flex items-center space-x-3 text-blue-400 animate-pulse">
                    <span className="text-2xl font-bold">Loading Job...</span>
                </div>
            </div>
        );
    }

    const renderStatusBadge = (status: string) => {
        const styles: any = {
            CLEAN: "bg-green-500/10 text-green-400 border-green-500/20",
            REVIEW: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
            REBUILD: "bg-red-500/10 text-red-400 border-red-500/20",
        };
        return (
            <span className={`px-2 py-1 rounded border text-xs font-bold ${styles[status] || ""}`}>
                {status}
            </span>
        );
    };

    return (
        <div className="min-h-screen bg-slate-900 text-slate-200">
            {/* Header */}
            <header className="border-b border-slate-700 bg-slate-800/50 backdrop-blur-md sticky top-0 z-50">
                <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                        <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-500">
                            DeckLint
                        </h1>
                        <span className="text-slate-600">/</span>
                        <span className="text-sm text-slate-400">{job.id.substring(0, 8)}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                        <span className="text-xs text-slate-500 uppercase font-tracking-wider">Status:</span>
                        <span className="font-mono text-sm font-bold text-blue-400">{job.status}</span>
                    </div>
                </div>
            </header>

            <main className="max-w-6xl mx-auto px-6 py-8">
                {/* Tabs */}
                <div className="flex items-center space-x-1 mb-8 bg-slate-800 p-1 rounded-lg w-fit">
                    {["overview", "proof", "deliver"].map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab as any)}
                            className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab === tab
                                    ? "bg-slate-700 text-white shadow-sm"
                                    : "text-slate-400 hover:text-slate-200"
                                }`}
                        >
                            {tab.charAt(0).toUpperCase() + tab.slice(1)}
                        </button>
                    ))}
                </div>

                {/* Overview Tab */}
                {activeTab === "overview" && (
                    <div className="space-y-6">
                        <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
                            <table className="w-full text-left font-sm">
                                <thead className="bg-slate-800 text-slate-400 uppercase text-xs">
                                    <tr>
                                        <th className="p-4">Slide</th>
                                        <th className="p-4">Status</th>
                                        <th className="p-4">Issues</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-700">
                                    {job.summary?.map((slide: any) => (
                                        <tr key={slide.index} className="hover:bg-slate-800/30 transition-colors">
                                            <td className="p-4 font-mono text-slate-500">#{slide.index + 1}</td>
                                            <td className="p-4">{renderStatusBadge(slide.status)}</td>
                                            <td className="p-4">
                                                {slide.issues.length === 0 ? (
                                                    <span className="text-slate-600 italic">No issues found</span>
                                                ) : (
                                                    <div className="space-y-1">
                                                        {slide.issues.map((issue: any, idx: number) => (
                                                            <div key={idx} className="flex items-start space-x-2 text-sm">
                                                                {issue.severity === "ERROR" ? (
                                                                    <AlertTriangle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
                                                                ) : (
                                                                    <AlertTriangle className="w-4 h-4 text-yellow-500 shrink-0 mt-0.5" />
                                                                )}
                                                                <span>{issue.message}</span>
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* Proof Tab */}
                {activeTab === "proof" && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {/* Placeholder content since we don't have real rendering yet */}
                        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-8 flex flex-col items-center justify-center text-center space-y-4">
                            <div className="w-full aspect-video bg-slate-800 border-2 border-dashed border-slate-700 rounded-lg flex items-center justify-center">
                                <ImageIcon className="w-12 h-12 text-slate-600" />
                            </div>
                            <p className="text-slate-400">Before / After Diff</p>
                        </div>
                        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-8">
                            <h3 className="text-lg font-bold mb-4">Verification Results</h3>
                            <p className="text-slate-400 mb-4">
                                Automated verification passed. No regressions detected in clean slides.
                            </p>
                            {/* Mock data */}
                            <div className="flex items-center space-x-4">
                                <div className="bg-green-500/10 text-green-400 px-3 py-1 rounded border border-green-500/20 text-sm">
                                    Score: 1.0
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Deliver Tab */}
                {activeTab === "deliver" && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 hover:border-blue-500/50 transition-colors group cursor-pointer">
                            <div className="bg-blue-500/10 w-12 h-12 rounded-lg flex items-center justify-center mb-4 group-hover:bg-blue-500/20">
                                <FileText className="w-6 h-6 text-blue-400" />
                            </div>
                            <h3 className="font-bold text-lg mb-1">Final Presentation</h3>
                            <p className="text-sm text-slate-400 mb-4">Corrected PPTX file ready for download.</p>
                            <button className="text-blue-400 text-sm font-bold flex items-center space-x-1 group-hover:underline">
                                <span>Download .pptx</span>
                                <Download className="w-4 h-4" />
                            </button>
                        </div>

                        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 hover:border-purple-500/50 transition-colors group cursor-pointer">
                            <div className="bg-purple-500/10 w-12 h-12 rounded-lg flex items-center justify-center mb-4 group-hover:bg-purple-500/20">
                                <Download className="w-6 h-6 text-purple-400" />
                            </div>
                            <h3 className="font-bold text-lg mb-1">Evidence Pack</h3>
                            <p className="text-sm text-slate-400 mb-4">Zip file containing diffs and reports.</p>
                            <button className="text-purple-400 text-sm font-bold flex items-center space-x-1 group-hover:underline">
                                <span>Download .zip</span>
                                <Download className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                )}

            </main>
        </div>
    );
}
