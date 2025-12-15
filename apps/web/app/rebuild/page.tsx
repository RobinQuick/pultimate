'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { api, Deck, Template } from '@/lib/api';

function RebuildForm() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const preselectedDeckId = searchParams.get('deck');

    const [decks, setDecks] = useState<Deck[]>([]);
    const [templates, setTemplates] = useState<Template[]>([]);
    const [selectedDeck, setSelectedDeck] = useState<string>(preselectedDeckId || '');
    const [selectedTemplate, setSelectedTemplate] = useState<string>('');
    const [dryRun, setDryRun] = useState(false);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => { loadData(); }, []);

    async function loadData() {
        try {
            setLoading(true);
            const [decksData, templatesData] = await Promise.all([
                api.decks.list(),
                api.templates.list(),
            ]);
            setDecks(decksData);
            setTemplates(templatesData);
            setError(null);
            if (decksData.length > 0 && !preselectedDeckId) setSelectedDeck(decksData[0].id);
            if (templatesData.length > 0) setSelectedTemplate(templatesData[0].id);
        } catch (err: any) {
            setError(err.message || 'Failed to load data');
        } finally {
            setLoading(false);
        }
    }

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        if (!selectedDeck || !selectedTemplate) {
            setError('Please select both a deck and a template');
            return;
        }
        try {
            setSubmitting(true);
            setError(null);
            const job = await api.rebuildJobs.create(selectedDeck, selectedTemplate, dryRun ? { dry_run: true } : undefined);
            router.push(`/jobs/${job.id}`);
        } catch (err: any) {
            setError(err.message || 'Failed to create job');
            setSubmitting(false);
        }
    }

    if (loading) return <div className="container"><h1>Rebuild Deck</h1><p>Loading...</p></div>;

    return (
        <div className="container">
            <h1>Rebuild Deck</h1>
            {decks.length === 0 || templates.length === 0 ? (
                <div className="info-box">
                    <p>To rebuild a deck, you need:</p>
                    <ul>
                        <li>At least one deck: {decks.length === 0 ? <a href="/decks">Upload a deck →</a> : '✓'}</li>
                        <li>At least one template: {templates.length === 0 ? <a href="/templates">Upload a template →</a> : '✓'}</li>
                    </ul>
                </div>
            ) : (
                <form onSubmit={handleSubmit} className="rebuild-form">
                    <div className="form-group">
                        <label htmlFor="deck">Source Deck</label>
                        <select id="deck" value={selectedDeck} onChange={(e) => setSelectedDeck(e.target.value)} required>
                            <option value="">Select a deck...</option>
                            {decks.map((deck) => (
                                <option key={deck.id} value={deck.id}>{deck.id.slice(0, 8)}... ({new Date(deck.created_at).toLocaleDateString()})</option>
                            ))}
                        </select>
                    </div>
                    <div className="form-group">
                        <label htmlFor="template">Target Template</label>
                        <select id="template" value={selectedTemplate} onChange={(e) => setSelectedTemplate(e.target.value)} required>
                            <option value="">Select a template...</option>
                            {templates.map((template) => (
                                <option key={template.id} value={template.id}>{template.name}</option>
                            ))}
                        </select>
                    </div>
                    <div className="form-group checkbox">
                        <label>
                            <input type="checkbox" checked={dryRun} onChange={(e) => setDryRun(e.target.checked)} />
                            Dry run (mapping only, no output file)
                        </label>
                    </div>
                    {error && <div className="error">{error}</div>}
                    <button type="submit" disabled={submitting} className="submit-btn">
                        {submitting ? 'Creating Job...' : 'Start Rebuild'}
                    </button>
                </form>
            )}
            <style jsx>{`
                .container { max-width: 600px; margin: 0 auto; padding: 2rem; }
                h1 { margin-bottom: 2rem; }
                .info-box { background: #fff3cd; border: 1px solid #ffc107; padding: 1.5rem; border-radius: 8px; }
                .info-box ul { margin: 0.5rem 0 0; padding-left: 1.5rem; }
                .info-box a { color: #0070f3; }
                .rebuild-form { background: #f9f9f9; padding: 2rem; border-radius: 8px; }
                .form-group { margin-bottom: 1.5rem; }
                .form-group label { display: block; margin-bottom: 0.5rem; font-weight: 500; }
                .form-group.checkbox label { display: flex; align-items: center; gap: 0.5rem; font-weight: normal; }
                select { width: 100%; padding: 0.75rem; border: 1px solid #ddd; border-radius: 4px; font-size: 1rem; background: white; }
                .error { background: #fee; color: #c00; padding: 1rem; border-radius: 4px; margin-bottom: 1rem; }
                .submit-btn { width: 100%; background: #0070f3; color: white; border: none; padding: 1rem; border-radius: 4px; font-size: 1.1rem; cursor: pointer; font-weight: 500; }
                .submit-btn:hover { background: #0060df; }
                .submit-btn:disabled { opacity: 0.6; cursor: not-allowed; }
            `}</style>
        </div>
    );
}

export default function RebuildPage() {
    return (
        <Suspense fallback={<div className="container"><h1>Rebuild Deck</h1><p>Loading...</p></div>}>
            <RebuildForm />
        </Suspense>
    );
}
