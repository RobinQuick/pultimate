const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface FetchOptions extends RequestInit {
    token?: string;
}

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

// API helper object for common operations
export const api = {
    async createJob(original: File, template: File) {
        const formData = new FormData();
        formData.append('original', original);
        formData.append('template', template);

        const response = await fetch(`${API_URL}/api/v1/jobs/`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Failed to create job' }));
            throw new Error(error.detail);
        }
        return response.json();
    },

    async runJob(jobId: string) {
        const response = await fetch(`${API_URL}/api/v1/jobs/${jobId}/run`, {
            method: 'POST',
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Failed to run job' }));
            throw new Error(error.detail);
        }
        return response.json();
    },

    async getJob(jobId: string) {
        return fetchClient(`/api/v1/jobs/${jobId}`);
    }
};
