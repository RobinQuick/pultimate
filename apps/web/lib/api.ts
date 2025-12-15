const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface FetchOptions extends RequestInit {
    token?: string;
}

// Type definitions
export interface Template {
    id: string;
    name: string;
    workspace_id: string;
    is_archived: boolean;
}

export interface TemplateVersion {
    id: string;
    template_id: string;
    version_num: number;
    status: string;
}

export interface Deck {
    id: string;
    workspace_id: string;
    owner_id: string;
    created_at: string;
    download_url?: string;
}

export interface DeckFile {
    id: string;
    deck_id: string;
    type: string;
    filename: string;
    download_url?: string;
}

export interface RebuildJob {
    id: string;
    deck_id: string;
    template_id: string;
    status: 'QUEUED' | 'RUNNING' | 'SUCCEEDED' | 'FAILED';
    progress: number;
    created_at: string;
    started_at?: string;
    completed_at?: string;
    error_message?: string;
}

export interface JobArtifact {
    id: string;
    artifact_type: string;
    filename: string;
    size_bytes?: number;
    download_url: string;
    expires_in: number;
}

export interface JobEvent {
    id: string;
    event_type: string;
    message: string;
    data?: Record<string, any>;
    created_at: string;
}

// Generic fetch client
export async function fetchClient<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
    const headers = new Headers(options.headers);
    headers.set('Content-Type', 'application/json');

    if (options.token) {
        headers.set('Authorization', `Bearer ${options.token}`);
    } else {
        // Auto-attach from localStorage if available (client-side only behavior)
        if (typeof window !== 'undefined') {
            const storedToken = localStorage.getItem('access_token');
            if (storedToken) {
                headers.set('Authorization', `Bearer ${storedToken}`);
            }
        }
    }

    // Handle FormData specifically (don't set Content-Type, let browser set boundary)
    if (options.body instanceof FormData) {
        headers.delete('Content-Type');
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers,
    });

    if (!response.ok) {
        if (response.status === 401) {
            // Handle unauthorized (redirect logic handled by AuthContext usually)
            if (typeof window !== 'undefined') {
                // Optional: dispatch event or clear token
            }
        }
        const errorBody = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorBody.detail || 'API request failed');
    }

    return response.json();
}

// File upload helper with auth
async function uploadWithAuth(endpoint: string, formData: FormData): Promise<any> {
    const headers: HeadersInit = {};

    if (typeof window !== 'undefined') {
        const token = localStorage.getItem('access_token');
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers,
        body: formData,
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
        throw new Error(error.detail);
    }
    return response.json();
}

// API namespace
export const api = {
    // =========================================================================
    // TEMPLATES
    // =========================================================================
    templates: {
        async list(): Promise<Template[]> {
            const result = await fetchClient<{ items: Template[] }>('/api/v1/templates/');
            return result.items || [];
        },

        async get(id: string): Promise<Template> {
            return fetchClient<Template>(`/api/v1/templates/${id}`);
        },

        async upload(file: File, name: string): Promise<Template> {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('name', name);
            return uploadWithAuth('/api/v1/templates/', formData);
        },

        async delete(id: string): Promise<void> {
            await fetchClient(`/api/v1/templates/${id}`, { method: 'DELETE' });
        },
    },

    // =========================================================================
    // DECKS
    // =========================================================================
    decks: {
        async list(): Promise<Deck[]> {
            const result = await fetchClient<{ items: Deck[] }>('/api/v1/decks/');
            return result.items || [];
        },

        async get(id: string): Promise<Deck & { files: DeckFile[] }> {
            return fetchClient<Deck & { files: DeckFile[] }>(`/api/v1/decks/${id}`);
        },

        async upload(file: File): Promise<Deck> {
            const formData = new FormData();
            formData.append('file', file);
            return uploadWithAuth('/api/v1/decks/', formData);
        },

        async delete(id: string): Promise<void> {
            await fetchClient(`/api/v1/decks/${id}`, { method: 'DELETE' });
        },
    },

    // =========================================================================
    // REBUILD JOBS
    // =========================================================================
    rebuildJobs: {
        async create(deckId: string, templateId: string, options?: { dry_run?: boolean }): Promise<RebuildJob> {
            return fetchClient<RebuildJob>('/api/v1/rebuild-jobs/', {
                method: 'POST',
                body: JSON.stringify({
                    deck_id: deckId,
                    template_id: templateId,
                    options,
                }),
            });
        },

        async list(): Promise<{ items: RebuildJob[]; total: number }> {
            return fetchClient<{ items: RebuildJob[]; total: number }>('/api/v1/rebuild-jobs/');
        },

        async get(id: string): Promise<RebuildJob> {
            return fetchClient<RebuildJob>(`/api/v1/rebuild-jobs/${id}`);
        },

        async getArtifacts(id: string): Promise<{ job_id: string; artifacts: JobArtifact[] }> {
            return fetchClient<{ job_id: string; artifacts: JobArtifact[] }>(`/api/v1/rebuild-jobs/${id}/artifacts`);
        },

        async getEvents(id: string): Promise<JobEvent[]> {
            return fetchClient<JobEvent[]>(`/api/v1/rebuild-jobs/${id}/events`);
        },

        async createDemoJob(): Promise<RebuildJob> {
            return fetchClient<RebuildJob>('/api/v1/rebuild-jobs/demo', {
                method: 'POST',
            });
        },
    },

    // =========================================================================
    // AUTH (existing)
    // =========================================================================
    auth: {
        async login(email: string, password: string): Promise<{ access_token: string; token_type: string }> {
            const formData = new URLSearchParams();
            formData.append('username', email);
            formData.append('password', password);

            const response = await fetch(`${API_URL}/api/v1/auth/token`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData,
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: 'Login failed' }));
                throw new Error(error.detail);
            }

            const data = await response.json();
            if (typeof window !== 'undefined') {
                localStorage.setItem('access_token', data.access_token);
            }
            return data;
        },

        async register(email: string, password: string): Promise<any> {
            return fetchClient('/api/v1/auth/register', {
                method: 'POST',
                body: JSON.stringify({ email, password }),
            });
        },

        logout() {
            if (typeof window !== 'undefined') {
                localStorage.removeItem('access_token');
            }
        },

        getToken(): string | null {
            if (typeof window !== 'undefined') {
                return localStorage.getItem('access_token');
            }
            return null;
        },
    },

    // Legacy methods for backwards compatibility
    async createJob(original: File, template: File) {
        const formData = new FormData();
        formData.append('original', original);
        formData.append('template', template);
        return uploadWithAuth('/api/v1/jobs/', formData);
    },

    async runJob(jobId: string) {
        return fetchClient(`/api/v1/jobs/${jobId}/run`, { method: 'POST' });
    },

    async getJob(jobId: string) {
        return fetchClient(`/api/v1/jobs/${jobId}`);
    },
};
