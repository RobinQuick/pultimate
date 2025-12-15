'use client';

import { useState, useEffect } from 'react';
import { api, Deck } from '@/lib/api';

export default function DecksPage() {
    const [decks, setDecks] = useState<Deck[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [uploading, setUploading] = useState(false);

    useEffect(() => { loadDecks(); }, []);

    async function loadDecks() {
        try {
            setLoading(true);
            const data = await api.decks.list();
            setDecks(data);
            setError(null);
        } catch (err: any) {
            setError(err.message || 'Failed to load decks');
        } finally {
            setLoading(false);
        }
    }

    async function handleUpload(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault();
        const form = e.currentTarget;
        const fileInput = form.elements.namedItem('file') as HTMLInputElement;
        const file = fileInput?.files?.[0];
        if (!file) { setError('Please select a file'); return; }
        try {
            setUploading(true); setError(null);
            await api.decks.upload(file);
            fileInput.value = '';
            await loadDecks();
        } catch (err: any) {
            setError(err.message || 'Upload failed');
        } finally { setUploading(false); }
    }

    return (
        <div className="container">
            <h1>Decks</h1>
            <div className="upload-section">
                <h2>Upload New Deck</h2>
                <form onSubmit={handleUpload}>
                    <div className="form-group">
                        <label htmlFor="file">PowerPoint File (.pptx)</label>
                        <input id="file" name="file" type="file" accept=".pptx" required />
                    </div>
                    <button type="submit" disabled={uploading}>
                        {uploading ? 'Uploading...' : 'Upload Deck'}
                    </button>
                </form>
            </div>
            {error && <div className="error">{error}</div>}
            <div className="list-section">
                <h2>Your Decks</h2>
                {loading ? (<p>Loading...</p>) : decks.length === 0 ? (
                    <p className="empty">No decks yet. Upload one above.</p>
                ) : (
                    <ul className="item-list">
                        {decks.map((deck) => (
                            <li key={deck.id} className="item">
                                <div className="item-info">
                                    <span className="id">{deck.id.slice(0, 8)}...</span>
                                    <span className="date">{new Date(deck.created_at).toLocaleDateString()}</span>
                                </div>
                                <a href={`/rebuild?deck=${deck.id}`} className="action-link">Rebuild →</a>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
            <style jsx>{`
                .container { max-width: 800px; margin: 0 auto; padding: 2rem; }
                h1 { margin-bottom: 2rem; }
                .upload-section, .list-section { background: #f9f9f9; padding: 1.5rem; border-radius: 8px; margin-bottom: 2rem; }
                h2 { margin-top: 0; margin-bottom: 1rem; font-size: 1.25rem; }
                .form-group { margin-bottom: 1rem; }
                .form-group label { display: block; margin-bottom: 0.5rem; font-weight: 500; }
                button { background: #0070f3; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 4px; cursor: pointer; }
                button:disabled { opacity: 0.6; cursor: not-allowed; }
                .error { background: #fee; color: #c00; padding: 1rem; border-radius: 4px; margin-bottom: 1rem; }
                .empty { color: #666; font-style: italic; }
                .item-list { list-style: none; padding: 0; margin: 0; }
                .item { display: flex; justify-content: space-between; align-items: center; padding: 0.75rem; background: white; border: 1px solid #eee; border-radius: 4px; margin-bottom: 0.5rem; }
                .item-info { display: flex; gap: 1rem; }
                .id { font-family: monospace; color: #333; }
                .date { color: #666; }
                .action-link { color: #0070f3; text-decoration: none; font-weight: 500; }
            `}</style>
        </div>
    );
}
