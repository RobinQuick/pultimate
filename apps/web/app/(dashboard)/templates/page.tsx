'use client';

import { useState, useEffect } from 'react';
import { api, Template } from '@/lib/api';

export default function TemplatesPage() {
    const [templates, setTemplates] = useState<Template[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [uploading, setUploading] = useState(false);
    const [uploadName, setUploadName] = useState('');

    useEffect(() => {
        loadTemplates();
    }, []);

    async function loadTemplates() {
        try {
            setLoading(true);
            const data = await api.templates.list();
            setTemplates(data);
            setError(null);
        } catch (err: any) {
            setError(err.message || 'Failed to load templates');
        } finally {
            setLoading(false);
        }
    }

    async function handleUpload(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault();
        const form = e.currentTarget;
        const fileInput = form.elements.namedItem('file') as HTMLInputElement;
        const file = fileInput?.files?.[0];

        if (!file || !uploadName.trim()) {
            setError('Please select a file and enter a name');
            return;
        }

        try {
            setUploading(true);
            setError(null);
            await api.templates.upload(file, uploadName.trim());
            setUploadName('');
            fileInput.value = '';
            await loadTemplates();
        } catch (err: any) {
            setError(err.message || 'Upload failed');
        } finally {
            setUploading(false);
        }
    }

    return (
        <div className="container">
            <h1>Templates</h1>

            {/* Upload Form */}
            <div className="upload-section">
                <h2>Upload New Template</h2>
                <form onSubmit={handleUpload}>
                    <div className="form-group">
                        <label htmlFor="name">Template Name</label>
                        <input
                            id="name"
                            type="text"
                            value={uploadName}
                            onChange={(e) => setUploadName(e.target.value)}
                            placeholder="Enter template name"
                            required
                        />
                    </div>
                    <div className="form-group">
                        <label htmlFor="file">File (.pptx, .potx)</label>
                        <input
                            id="file"
                            name="file"
                            type="file"
                            accept=".pptx,.potx"
                            required
                        />
                    </div>
                    <button type="submit" disabled={uploading}>
                        {uploading ? 'Uploading...' : 'Upload Template'}
                    </button>
                </form>
            </div>

            {error && <div className="error">{error}</div>}

            {/* Templates List */}
            <div className="list-section">
                <h2>Your Templates</h2>
                {loading ? (
                    <p>Loading...</p>
                ) : templates.length === 0 ? (
                    <p className="empty">No templates yet. Upload one above.</p>
                ) : (
                    <ul className="item-list">
                        {templates.map((template) => (
                            <li key={template.id} className="item">
                                <span className="name">{template.name}</span>
                                <span className="id">{template.id.slice(0, 8)}...</span>
                            </li>
                        ))}
                    </ul>
                )}
            </div>

            <style jsx>{`
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 2rem;
                }
                h1 { margin-bottom: 2rem; }
                .upload-section, .list-section {
                    background: #f9f9f9;
                    padding: 1.5rem;
                    border-radius: 8px;
                    margin-bottom: 2rem;
                }
                h2 { margin-top: 0; margin-bottom: 1rem; font-size: 1.25rem; }
                .form-group { margin-bottom: 1rem; }
                .form-group label { display: block; margin-bottom: 0.5rem; font-weight: 500; }
                .form-group input[type="text"] {
                    width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px;
                }
                button {
                    background: #0070f3; color: white; border: none; padding: 0.75rem 1.5rem;
                    border-radius: 4px; cursor: pointer; font-size: 1rem;
                }
                button:disabled { opacity: 0.6; cursor: not-allowed; }
                .error { background: #fee; color: #c00; padding: 1rem; border-radius: 4px; margin-bottom: 1rem; }
                .empty { color: #666; font-style: italic; }
                .item-list { list-style: none; padding: 0; margin: 0; }
                .item {
                    display: flex; justify-content: space-between; align-items: center;
                    padding: 0.75rem; background: white; border: 1px solid #eee;
                    border-radius: 4px; margin-bottom: 0.5rem;
                }
                .name { font-weight: 500; }
                .id { color: #999; font-family: monospace; font-size: 0.875rem; }
            `}</style>
        </div>
    );
}
