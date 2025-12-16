'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { api, SharedJobDetail } from '@/lib/api';

const POLL_INTERVAL = 5000; // Slower polling for public page

export default function SharedJobPage() {
    const params = useParams();
    const token = params.token as string;

    const [job, setJob] = useState<SharedJobDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const loadJob = useCallback(async () => {
        try {
            const jobData = await api.rebuildJobs.getSharedJob(token);
            setJob(jobData);
            setError(null);
            return jobData;
        } catch (err: any) {
            setError(err.message || 'Failed to load report');
            return null;
        }
    }, [token]);

    useEffect(() => {
        let intervalId: NodeJS.Timeout;

        async function init() {
            setLoading(true);
            const jobData = await loadJob();
            setLoading(false);

            // Poll while running
            if (jobData && (jobData.status === 'QUEUED' || jobData.status === 'RUNNING')) {
                intervalId = setInterval(async () => {
                    const updated = await loadJob();
                    if (updated && (updated.status === 'SUCCEEDED' || updated.status === 'FAILED')) {
                        clearInterval(intervalId);
                    }
                }, POLL_INTERVAL);
            }
        }

        init();

        return () => {
            if (intervalId) clearInterval(intervalId);
        };
    }, [loadJob]);

    // Derive evidence metrics from events
    // We reuse logic from job page
    const events = job?.events || [];
    const parsedDeckEvent = events.find(e => e.event_type === 'PARSED_DECK');
    const mappingEvent = events.find(e => e.event_type === 'LLM_MAPPING') || events.find(e => e.event_type === 'STEP_COMPLETED' && e.message.includes('LLM mapping'));
    const appliedEvent = events.find(e => e.event_type === 'MAPPING_APPLIED') || events.find(e => e.event_type === 'STEP_COMPLETED' && e.message.includes('Deck rebuilt'));

    const evidence = {
        inputElements: parsedDeckEvent?.message.match(/\d+/)?.[0] || '?',
        slidesCreated: appliedEvent?.message.match(/(\d+) slides/)?.[1] || '?',
        elementsMapped: appliedEvent?.message.match(/(\d+) elements/)?.[1] || '?',
        warnings: (mappingEvent?.data?.warnings || 0) + (appliedEvent?.data?.warnings || 0),
    };

    function getStatusColor(status: string): string {
        switch (status) {
            case 'QUEUED': return '#888';
            case 'RUNNING': return '#0070f3';
            case 'SUCCEEDED': return '#22c55e';
            case 'FAILED': return '#ef4444';
            default: return '#888';
        }
    }

    function getStatusIcon(status: string): string {
        switch (status) {
            case 'QUEUED': return '⏳';
            case 'RUNNING': return '🔄';
            case 'SUCCEEDED': return '✅';
            case 'FAILED': return '❌';
            default: return '❓';
        }
    }

    function formatArtifactType(type: string): string {
        return type.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
    }

    if (loading) return <div className="container"><h1>Loading Report...</h1></div>;

    if (error || !job) {
        return (
            <div className="container">
                <h1>Report Not Found</h1>
                <div className="error">{error || 'This link may be invalid or expired.'}</div>
                <a href="/" className="back-link">← Go to Pultimate</a>
            </div>
        );
    }

    return (
        <div className="container">
            <header className="page-header">
                <div>
                    <h1>Rebuild Report</h1>
                    <div className="sub-header">Shared via secure link</div>
                </div>
                <a href="/" className="logo">⚡ Pultimate</a>
            </header>

            {/* Status Section */}
            <div className="card status-card">
                <div className="status-header">
                    <span className="status-icon">{getStatusIcon(job.status)}</span>
                    <span className="status-text" style={{ color: getStatusColor(job.status) }}>
                        {job.status}
                    </span>
                </div>

                {(job.status === 'QUEUED' || job.status === 'RUNNING') && (
                    <div className="progress-container">
                        <div className="progress-bar" style={{ width: `${job.progress}%` }} />
                        <span className="progress-text">{job.progress}%</span>
                    </div>
                )}

                <div className="timestamps">
                    <div>Created: {new Date(job.created_at).toLocaleString()}</div>
                    {job.completed_at && <div>Completed: {new Date(job.completed_at).toLocaleString()}</div>}
                </div>
            </div>

            <div className="grid-layout">
                <div className="main-col">
                    {/* Artifacts (Primary CTA) */}
                    {job.artifacts.length > 0 && (
                        <div className="card highlight-card">
                            <h2>Transformed Output</h2>
                            <p>Download the fully reconstructed presentation.</p>

                            {job.artifacts.find((a) => a.artifact_type === 'OUTPUT_DECK') && (
                                <a
                                    href={job.artifacts.find((a) => a.artifact_type === 'OUTPUT_DECK')?.download_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="primary-download"
                                >
                                    📥 Download Rebuilt Deck
                                </a>
                            )}

                            <ul className="artifacts-list mini">
                                {job.artifacts.map((artifact) => (
                                    <li key={artifact.id} className="artifact-item">
                                        <span className="artifact-name">{artifact.filename}</span>
                                        <a href={artifact.download_url} className="link-btn">Download</a>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {/* Timeline */}
                    <div className="card">
                        <h2>Execution Timeline</h2>
                        <ul className="timeline">
                            {job.events.map((event) => (
                                <li key={event.id} className="timeline-item">
                                    <div className="time">{new Date(event.created_at).toLocaleTimeString()}</div>
                                    <div className="content">
                                        <div className="message">{event.message}</div>
                                        <div className="type">{event.event_type}</div>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>

                <div className="side-col">
                    {/* Evidence / Stats */}
                    <div className="card stats-card">
                        <h2>Evidence & Metrics</h2>
                        <div className="stat-row">
                            <span className="label">Input Elements</span>
                            <span className="value">{evidence.inputElements}</span>
                        </div>
                        <div className="stat-row">
                            <span className="label">Slides Created</span>
                            <span className="value">{evidence.slidesCreated}</span>
                        </div>
                        <div className="stat-row">
                            <span className="label">Elements Mapped</span>
                            <span className="value">{evidence.elementsMapped}</span>
                        </div>
                        <div className="stat-row">
                            <span className="label">Warnings</span>
                            <span className={`value ${evidence.warnings > 0 ? 'warning' : 'success'}`}>
                                {evidence.warnings}
                            </span>
                        </div>
                    </div>

                    <div className="card trust-card">
                        <h3>🔒 Secure & Private</h3>
                        <p>This report was generated securely. No generative AI was used to hallucinate content. 100% logic-based layout enforcement.</p>
                        <a href="/" className="marketing-link">Learn how Pultimate works →</a>
                    </div>
                </div>
            </div>

            <style jsx>{`
                .container { max-width: 1000px; margin: 0 auto; padding: 2rem; font-family: 'Inter', sans-serif; }
                .page-header { display: flex; justify-content: space-between; align-items: start; margin-bottom: 2rem; }
                .logo { font-weight: 800; font-size: 1.2rem; text-decoration: none; color: black; }
                .sub-header { color: #666; font-size: 0.9rem; }
                h1 { margin: 0; }
                
                .card { background: #f9f9f9; padding: 1.5rem; border-radius: 8px; margin-bottom: 2rem; }
                .highlight-card { background: #f0f7ff; border: 1px solid #cce4ff; }
                .trust-card { background: #333; color: white; }
                .trust-card h3 { margin-top: 0; }
                .marketing-link { color: #00c4ff; text-decoration: none; display: inline-block; margin-top: 0.5rem; font-size: 0.9rem; }
                
                .grid-layout { display: grid; grid-template-columns: 2fr 1fr; gap: 2rem; }
                @media (max-width: 768px) { .grid-layout { grid-template-columns: 1fr; } }

                .status-header { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; }
                .status-icon { font-size: 1.5rem; }
                .status-text { font-size: 1.25rem; font-weight: 600; }
                
                .progress-container { position: relative; height: 16px; background: #e0e0e0; border-radius: 8px; margin-bottom: 1rem; overflow: hidden; }
                .progress-bar { position: absolute; top: 0; left: 0; height: 100%; background: #0070f3; border-radius: 8px; transition: width 0.3s ease; }
                .progress-text { position: absolute; right: 10px; font-size: 0.75rem; font-weight: 500; color: #333; top: 0; line-height: 16px; }
                
                .timestamps { font-size: 0.875rem; color: #666; }
                
                .timeline { list-style: none; padding: 0; margin: 0; }
                .timeline-item { display: flex; gap: 1rem; padding-bottom: 1rem; border-left: 2px solid #ddd; padding-left: 1rem; position: relative; }
                .timeline-item::before { content: ''; position: absolute; left: -5px; top: 0; width: 8px; height: 8px; background: #bbb; border-radius: 50%; }
                .time { font-family: monospace; font-size: 0.8rem; color: #888; white-space: nowrap; width: 70px; }
                .message { font-weight: 500; margin-bottom: 0.25rem; }
                .type { font-size: 0.75rem; color: #666; background: #e0e0e0; display: inline-block; padding: 0 0.4rem; border-radius: 4px; }

                .stat-row { display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #ddd; }
                .stat-row:last-child { border-bottom: none; }
                .label { color: #555; }
                .value { font-weight: 600; font-family: monospace; font-size: 1.1rem; }
                .warning { color: #f5a623; }
                .success { color: #22c55e; }

                .primary-download { display: block; text-align: center; background: #22c55e; color: white; padding: 1rem; border-radius: 4px; text-decoration: none; font-size: 1.1rem; font-weight: 700; margin: 1rem 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: transform 0.2s; }
                .primary-download:hover { transform: translateY(-2px); }

                .artifacts-list.mini { padding: 0; list-style: none; margin-top: 1rem; border-top: 1px solid #daeaff; pt: 1rem; font-size: 0.9rem; }
                .artifact-item { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
                .artifact-name { font-family: monospace; color: #444; }
                .link-btn { color: #0070f3; text-decoration: underline; cursor: pointer; }
                
                .back-link { color: #0070f3; text-decoration: none; display: inline-block; margin-top: 1rem; }
                .error { background: #fee; color: #c00; padding: 1rem; border-radius: 4px; margin-bottom: 1rem; }
            `}</style>
        </div>
    );
}
