"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Upload, ArrowRight, FileType, CheckCircle } from "lucide-react";

export default function UploadPage() {
    const router = useRouter();
    const [original, setOriginal] = useState<File | null>(null);
    const [template, setTemplate] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleUpload = async () => {
        if (!original || !template) return;
        setLoading(true);
        setError("");
        try {
            const job = await api.createJob(original, template);
            // Start the job
            await api.runJob(job.id);
            router.push(`/jobs/${job.id}`);
        } catch (err: any) {
            setError(err.message || "Failed to create job");
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-slate-900 text-white">
            <div className="max-w-xl w-full space-y-8">
                <div className="text-center space-y-2">
                    <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-500">
                        DeckLint
                    </h1>
                    <p className="text-slate-400">Enterprise Presentation Audit & Repair</p>
                </div>

                <div className="bg-slate-800/50 p-8 rounded-2xl border border-slate-700 backdrop-blur-sm space-y-6">
                    {/* File 1: Original */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-300">Original Presentation</label>
                        <div className="relative group">
                            <input
                                type="file"
                                accept=".pptx"
                                onChange={(e) => setOriginal(e.target.files?.[0] || null)}
                                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                            />
                            <div className={`border-2 border-dashed rounded-xl p-6 flex items-center justify-center transition-colors ${original ? "border-green-500/50 bg-green-500/10" : "border-slate-600 group-hover:border-blue-400 bg-slate-800"
                                }`}>
                                {original ? (
                                    <div className="flex items-center space-x-2 text-green-400">
                                        <CheckCircle className="w-5 h-5" />
                                        <span className="truncate max-w-[200px]">{original.name}</span>
                                    </div>
                                ) : (
                                    <div className="flex flex-col items-center text-slate-400">
                                        <Upload className="w-8 h-8 mb-2" />
                                        <span className="text-sm">Drop file or click to upload</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* File 2: Template */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-300">Corporate Template</label>
                        <div className="relative group">
                            <input
                                type="file"
                                accept=".pptx"
                                onChange={(e) => setTemplate(e.target.files?.[0] || null)}
                                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                            />
                            <div className={`border-2 border-dashed rounded-xl p-6 flex items-center justify-center transition-colors ${template ? "border-green-500/50 bg-green-500/10" : "border-slate-600 group-hover:border-blue-400 bg-slate-800"
                                }`}>
                                {template ? (
                                    <div className="flex items-center space-x-2 text-green-400">
                                        <CheckCircle className="w-5 h-5" />
                                        <span className="truncate max-w-[200px]">{template.name}</span>
                                    </div>
                                ) : (
                                    <div className="flex flex-col items-center text-slate-400">
                                        <FileType className="w-8 h-8 mb-2" />
                                        <span className="text-sm">Drop template file</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {error && (
                        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
                            {error}
                        </div>
                    )}

                    <button
                        onClick={handleUpload}
                        disabled={!original || !template || loading}
                        className="w-full py-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl font-bold transition-all flex items-center justify-center space-x-2"
                    >
                        {loading ? (
                            <span className="animate-pulse">Processing...</span>
                        ) : (
                            <>
                                <span>Start Audit</span>
                                <ArrowRight className="w-5 h-5" />
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}
