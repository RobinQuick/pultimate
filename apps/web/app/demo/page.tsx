'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

export default function DemoPage() {
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    async function startDemo() {
        setLoading(true);
        setError(null);
        try {
            const job = await api.rebuildJobs.createDemoJob();
            router.push(`/jobs/${job.id}`);
        } catch (err: any) {
            setError(err.message || 'Failed to start demo');
            setLoading(false);
        }
    }

    return (
        <div className="container">
            <div className="hero">
                <h1>⚡ Pultimate V2 Demo</h1>
                <p>Experience the power of the new Rebuild Engine with a single click.</p>

                <div className="demo-card">
                    <h2>What happens?</h2>
                    <ul>
                        <li>1. We provision a sample "Golden Set" deck & template.</li>
                        <li>2. Our worker parses elements and placeholders.</li>
                        <li>3. LLM maps content (NO-GEN policy enforced).</li>
                        <li>4. Worker rebuilds the deck in the new template.</li>
                    </ul>

                    <button
                        onClick={startDemo}
                        disabled={loading}
                        className="start-btn"
                    >
                        {loading ? 'Starting Engine...' : '🚀 Start Live Demo'}
                    </button>

                    {error && <div className="error">{error}</div>}
                </div>
            </div>

            <style jsx>{`
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 4rem 2rem;
                    text-align: center;
                }
                h1 {
                    font-size: 3rem;
                    background: linear-gradient(90deg, #0070f3, #00c4ff);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin-bottom: 1rem;
                }
                .hero p {
                    font-size: 1.25rem;
                    color: #666;
                    margin-bottom: 3rem;
                }
                .demo-card {
                    background: white;
                    border: 1px solid #eee;
                    border-radius: 12px;
                    padding: 2rem;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
                    text-align: left;
                    max-width: 500px;
                    margin: 0 auto;
                }
                h2 { margin-top: 0; }
                ul {
                    margin-bottom: 2rem;
                    color: #555;
                    line-height: 1.6;
                }
                .start-btn {
                    width: 100%;
                    padding: 1rem;
                    font-size: 1.1rem;
                    font-weight: 600;
                    background: black;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    cursor: pointer;
                    transition: transform 0.1s;
                }
                .start-btn:hover:not(:disabled) {
                    transform: scale(1.02);
                    background: #222;
                }
                .start-btn:disabled {
                    opacity: 0.7;
                    cursor: not-allowed;
                }
                .error {
                    margin-top: 1rem;
                    color: #c00;
                    text-align: center;
                }
            `}</style>
        </div>
    );
}
