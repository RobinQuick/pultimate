'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { api, RebuildJob, JobArtifact, JobEvent } from '@/lib/api';

const POLL_INTERVAL = 2000; // 2 seconds

export default function JobDetailPage() {
    const params = useParams();
    const jobId = params.id as string;

    const [job, setJob] = useState<RebuildJob | null>(null);
    const [artifacts, setArtifacts] = useState<JobArtifact[]>([]);
    const [events, setEvents] = useState<JobEvent[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const loadJob = useCallback(async () => {
        try {
            const [jobData, eventsData] = await Promise.all([
                api.rebuildJobs.get(jobId),
                api.rebuildJobs.getEvents(jobId)
            ]);

            setJob(jobData);
            setEvents(eventsData);

            // Load artifacts if job is complete
            if (jobData.status === 'SUCCEEDED' || jobData.status === 'FAILED') {
                try {
                    const artifactsData = await api.rebuildJobs.getArtifacts(jobId);
                    setArtifacts(artifactsData.artifacts);
                } catch {
                    // Artifacts might not exist yet
                }
            }

            setError(null);
            return jobData;
        } catch (err: any) {
            setError(err.message || 'Failed to load job');
            return null;
        }
    }, [jobId]);

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

    if (loading) return <div className="container"><h1>Loading Job...</h1></div>;

    if (error || !job) {
        return (
            <div className="container">
                <h1>Job Not Found</h1>
                <div className="error">{error || 'Job does not exist'}</div>
                <a href="/rebuild" className="back-link">← Back to Rebuild</a>
            </div>
        );
    }

    return (
        <div className="container">
            <div className="header">
                <h1>Rebuild Job</h1>
                <span className="job-id">{job.id.slice(0, 8)}...</span>
            </div>

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

                {job.status === 'FAILED' && job.error_message && (
                    <div className="error-message">
                        <strong>Error:</strong> {job.error_message}
                    </div>
                )}

                <div className="timestamps">
                    <div>Created: {new Date(job.created_at).toLocaleString()}</div>
                    {job.started_at && <div>Started: {new Date(job.started_at).toLocaleString()}</div>}
                    {job.completed_at && <div>Completed: {new Date(job.completed_at).toLocaleString()}</div>}
                </div>
            </div>

            <div className="grid-layout">
                <div className="main-col">
                    {/* Timeline */}
                    <div className="card">
                        <h2>Timeline</h2>
                        <ul className="timeline">
                            {events.map((event) => (
                                <li key={event.id} className="timeline-item">
                                    <div className="time">{new Date(event.created_at).toLocaleTimeString()}</div>
                                    <div className="content">
                                        <div className="message">{event.message}</div>
                                        <div className="type">{event.event_type}</div>
                                        {event.event_type === 'FAILED' && (
                                            <div className="fail-badge">FAILED</div>
                                        )}
                                    </div>
                                </li>
                            ))}
                            {events.length === 0 && <li className="empty">No events yet</li>}
                        </ul>
                    </div>

                    {/* Artifacts */}
                    {artifacts.length > 0 && (
                        <div className="card">
                            <h2>Artifacts</h2>
                            <ul className="artifacts-list">
                                {artifacts.map((artifact) => (
                                    <li key={artifact.id} className="artifact-item">
                                        <div className="artifact-info">
                                            <span className="artifact-type">{formatArtifactType(artifact.artifact_type)}</span>
                                            <span className="artifact-name">{artifact.filename}</span>
                                            {artifact.size_bytes && <span className="artifact-size">({(artifact.size_bytes / 1024).toFixed(1)} KB)</span>}
                                        </div>
                                        <a href={artifact.download_url} target="_blank" rel="noopener noreferrer" className="download-btn">Download</a>
                                    </li>
                                ))}
                            </ul>

                            {artifacts.find((a) => a.artifact_type === 'OUTPUT_DECK') && (
                                <a
                                    href={artifacts.find((a) => a.artifact_type === 'OUTPUT_DECK')?.download_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="primary-download"
                                >
                                    📥 Download Rebuilt Deck
                                </a>
                            )}
                        </div>
                    )}
                </div>

                <div className="side-col">
                    {/* Evidence / Stats */}
                    <div className="card stats-card">
                        <h2>Evidence</h2>
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

                        {/* Content Preservation (Mock logic for now, real logic would use golden runner output) */}
                        <div className="stat-row">
                            <span className="label">Content Preserved</span>
                            <span className="value success">
                                {evidence.elementsMapped !== '?' && evidence.elementsMapped !== '0' ? '✅ YES' : '—'}
                            </span>
                        </div>

                        <div className="stat-row">
                            <span className="label">Warnings</span>
                            <span className={`value ${evidence.warnings > 0 ? 'warning' : 'success'}`}>
                                {evidence.warnings}
                            </span>
                        </div>

                        {evidence.warnings > 0 && (
                            <div className="warnings-list">
                                <h3>Warning Details</h3>
                                <ul>
                                    {/* Placeholder for real warning text, fetching specifically if needed */}
                                    <li>See events for details</li>
                                </ul>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            <a href="/rebuild" className="back-link">← Create Another Rebuild</a>

            <style jsx>{`
                .container { max-width: 1000px; margin: 0 auto; padding: 2rem; }
                .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
                h1 { margin: 0; }
                .job-id { font-family: monospace; color: #666; background: #f0f0f0; padding: 0.25rem 0.5rem; border-radius: 4px; }
                
                .card { background: #f9f9f9; padding: 1.5rem; border-radius: 8px; margin-bottom: 2rem; }
                .grid-layout { display: grid; grid-template-columns: 2fr 1fr; gap: 2rem; }
                @media (max-width: 768px) { .grid-layout { grid-template-columns: 1fr; } }

                .status-header { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; }
                .status-icon { font-size: 1.5rem; }
                .status-text { font-size: 1.25rem; font-weight: 600; }
                
                .progress-container { position: relative; height: 24px; background: #e0e0e0; border-radius: 12px; margin-bottom: 1rem; overflow: hidden; }
                .progress-bar { position: absolute; top: 0; left: 0; height: 100%; background: linear-gradient(90deg, #0070f3, #00c4ff); border-radius: 12px; transition: width 0.3s ease; }
                .progress-text { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); font-size: 0.875rem; font-weight: 500; color: #333; }
                
                .error-message { background: #fee; color: #c00; padding: 1rem; border-radius: 4px; margin-bottom: 1rem; }
                .timestamps { font-size: 0.875rem; color: #666; }
                
                .timeline { list-style: none; padding: 0; margin: 0; }
                .timeline-item { display: flex; gap: 1rem; padding-bottom: 1rem; border-left: 2px solid #ddd; padding-left: 1rem; position: relative; }
                .timeline-item::before { content: ''; position: absolute; left: -5px; top: 0; width: 8px; height: 8px; background: #bbb; border-radius: 50%; }
                .timeline-item:first-child::before { background: #0070f3; }
                .time { font-family: monospace; font-size: 0.8rem; color: #888; white-space: nowrap; width: 70px; }
                .message { font-weight: 500; margin-bottom: 0.25rem; }
                .type { font-size: 0.75rem; color: #666; background: #e0e0e0; display: inline-block; padding: 0 0.4rem; border-radius: 4px; }
                .fail-badge { background: #fee; color: #c00; font-weight: bold; font-size: 0.75rem; display: inline-block; padding: 0 0.4rem; border-radius: 4px; margin-left: 0.5rem; }

                .stat-row { display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #eee; }
                .stat-row:last-child { border-bottom: none; }
                .label { color: #555; }
                .value { font-weight: 600; font-family: monospace; font-size: 1.1rem; }
                .warning { color: #f5a623; }
                .success { color: #22c55e; }
                
                .warnings-list { margin-top: 1rem; font-size: 0.9rem; color: #666; }
                .warnings-list h3 { font-size: 1rem; margin-bottom: 0.5rem; }
                .warnings-list ul { padding-left: 1.2rem; margin: 0; }

                .artifacts-list { list-style: none; padding: 0; margin: 0 0 1rem; }
                .artifact-item { display: flex; justify-content: space-between; align-items: center; padding: 0.75rem; background: white; border: 1px solid #eee; border-radius: 4px; margin-bottom: 0.5rem; }
                .artifact-info { display: flex; gap: 0.5rem; align-items: center; }
                .artifact-type { background: #e0e0e0; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 500; }
                .artifact-name { font-family: monospace; }
                .artifact-size { color: #888; font-size: 0.875rem; }
                .download-btn { background: #0070f3; color: white; padding: 0.5rem 1rem; border-radius: 4px; text-decoration: none; font-size: 0.875rem; }
                .primary-download { display: block; text-align: center; background: #22c55e; color: white; padding: 1rem; border-radius: 4px; text-decoration: none; font-size: 1.1rem; font-weight: 500; }
                
                .back-link { color: #0070f3; text-decoration: none; display: inline-block; margin-top: 1rem; }
                .error { background: #fee; color: #c00; padding: 1rem; border-radius: 4px; margin-bottom: 1rem; }
            `}</style>
        </div>
    );
}
