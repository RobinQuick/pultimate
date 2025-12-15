'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { api, RebuildJob, JobArtifact } from '@/lib/api';

const POLL_INTERVAL = 2000; // 2 seconds

export default function JobDetailPage() {
    const params = useParams();
    const jobId = params.id as string;

    const [job, setJob] = useState<RebuildJob | null>(null);
    const [artifacts, setArtifacts] = useState<JobArtifact[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const loadJob = useCallback(async () => {
        try {
            const jobData = await api.rebuildJobs.get(jobId);
            setJob(jobData);

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

            // Poll if job is not complete
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

    function getStatusColor(status: string): string {
        switch (status) {
            case 'QUEUED':
                return '#888';
            case 'RUNNING':
                return '#0070f3';
            case 'SUCCEEDED':
                return '#22c55e';
            case 'FAILED':
                return '#ef4444';
            default:
                return '#888';
        }
    }

    function getStatusIcon(status: string): string {
        switch (status) {
            case 'QUEUED':
                return '⏳';
            case 'RUNNING':
                return '🔄';
            case 'SUCCEEDED':
                return '✅';
            case 'FAILED':
                return '❌';
            default:
                return '❓';
        }
    }

    function formatArtifactType(type: string): string {
        return type.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
    }

    if (loading) {
        return (
            <div className="container">
                <h1>Loading Job...</h1>
            </div>
        );
    }

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
            <div className="status-card">
                <div className="status-header">
                    <span className="status-icon">{getStatusIcon(job.status)}</span>
                    <span
                        className="status-text"
                        style={{ color: getStatusColor(job.status) }}
                    >
                        {job.status}
                    </span>
                </div>

                {/* Progress Bar */}
                {(job.status === 'QUEUED' || job.status === 'RUNNING') && (
                    <div className="progress-container">
                        <div
                            className="progress-bar"
                            style={{ width: `${job.progress}%` }}
                        />
                        <span className="progress-text">{job.progress}%</span>
                    </div>
                )}

                {/* Error Message */}
                {job.status === 'FAILED' && job.error_message && (
                    <div className="error-message">
                        <strong>Error:</strong> {job.error_message}
                    </div>
                )}

                {/* Timestamps */}
                <div className="timestamps">
                    <div>Created: {new Date(job.created_at).toLocaleString()}</div>
                    {job.started_at && (
                        <div>Started: {new Date(job.started_at).toLocaleString()}</div>
                    )}
                    {job.completed_at && (
                        <div>Completed: {new Date(job.completed_at).toLocaleString()}</div>
                    )}
                </div>
            </div>

            {/* Artifacts Section */}
            {artifacts.length > 0 && (
                <div className="artifacts-section">
                    <h2>Artifacts</h2>
                    <ul className="artifacts-list">
                        {artifacts.map((artifact) => (
                            <li key={artifact.id} className="artifact-item">
                                <div className="artifact-info">
                                    <span className="artifact-type">
                                        {formatArtifactType(artifact.artifact_type)}
                                    </span>
                                    <span className="artifact-name">{artifact.filename}</span>
                                    {artifact.size_bytes && (
                                        <span className="artifact-size">
                                            ({(artifact.size_bytes / 1024).toFixed(1)} KB)
                                        </span>
                                    )}
                                </div>
                                <a
                                    href={artifact.download_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="download-btn"
                                >
                                    Download
                                </a>
                            </li>
                        ))}
                    </ul>

                    {/* Primary Download Button for Output */}
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

            <a href="/rebuild" className="back-link">← Create Another Rebuild</a>

            <style jsx>{`
                .container {
                    max-width: 700px;
                    margin: 0 auto;
                    padding: 2rem;
                }
                .header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 2rem;
                }
                h1 {
                    margin: 0;
                }
                .job-id {
                    font-family: monospace;
                    color: #666;
                    background: #f0f0f0;
                    padding: 0.25rem 0.5rem;
                    border-radius: 4px;
                }
                .status-card {
                    background: #f9f9f9;
                    padding: 1.5rem;
                    border-radius: 8px;
                    margin-bottom: 2rem;
                }
                .status-header {
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                    margin-bottom: 1rem;
                }
                .status-icon {
                    font-size: 1.5rem;
                }
                .status-text {
                    font-size: 1.25rem;
                    font-weight: 600;
                }
                .progress-container {
                    position: relative;
                    height: 24px;
                    background: #e0e0e0;
                    border-radius: 12px;
                    margin-bottom: 1rem;
                    overflow: hidden;
                }
                .progress-bar {
                    position: absolute;
                    top: 0;
                    left: 0;
                    height: 100%;
                    background: linear-gradient(90deg, #0070f3, #00c4ff);
                    border-radius: 12px;
                    transition: width 0.3s ease;
                }
                .progress-text {
                    position: absolute;
                    right: 10px;
                    top: 50%;
                    transform: translateY(-50%);
                    font-size: 0.875rem;
                    font-weight: 500;
                    color: #333;
                }
                .error-message {
                    background: #fee;
                    color: #c00;
                    padding: 1rem;
                    border-radius: 4px;
                    margin-bottom: 1rem;
                }
                .timestamps {
                    font-size: 0.875rem;
                    color: #666;
                }
                .timestamps div {
                    margin-bottom: 0.25rem;
                }
                .artifacts-section {
                    background: #f9f9f9;
                    padding: 1.5rem;
                    border-radius: 8px;
                    margin-bottom: 2rem;
                }
                .artifacts-section h2 {
                    margin-top: 0;
                    margin-bottom: 1rem;
                }
                .artifacts-list {
                    list-style: none;
                    padding: 0;
                    margin: 0 0 1rem;
                }
                .artifact-item {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 0.75rem;
                    background: white;
                    border: 1px solid #eee;
                    border-radius: 4px;
                    margin-bottom: 0.5rem;
                }
                .artifact-info {
                    display: flex;
                    gap: 0.5rem;
                    align-items: center;
                }
                .artifact-type {
                    background: #e0e0e0;
                    padding: 0.25rem 0.5rem;
                    border-radius: 4px;
                    font-size: 0.75rem;
                    font-weight: 500;
                }
                .artifact-name {
                    font-family: monospace;
                }
                .artifact-size {
                    color: #888;
                    font-size: 0.875rem;
                }
                .download-btn {
                    background: #0070f3;
                    color: white;
                    padding: 0.5rem 1rem;
                    border-radius: 4px;
                    text-decoration: none;
                    font-size: 0.875rem;
                }
                .download-btn:hover {
                    background: #0060df;
                }
                .primary-download {
                    display: block;
                    text-align: center;
                    background: #22c55e;
                    color: white;
                    padding: 1rem;
                    border-radius: 4px;
                    text-decoration: none;
                    font-size: 1.1rem;
                    font-weight: 500;
                }
                .primary-download:hover {
                    background: #16a34a;
                }
                .back-link {
                    color: #0070f3;
                    text-decoration: none;
                }
                .back-link:hover {
                    text-decoration: underline;
                }
                .error {
                    background: #fee;
                    color: #c00;
                    padding: 1rem;
                    border-radius: 4px;
                    margin-bottom: 1rem;
                }
            `}</style>
        </div>
    );
}
