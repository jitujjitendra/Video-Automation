/**
 * API Communication Module
 * Handles all HTTP requests to the backend FastAPI server.
 */

class ApiClient {
    constructor() {
        // Default backend URL - can be overridden for production
        this.baseUrl = this._detectBackendUrl();
    }

    /**
     * Detect the backend URL based on the current environment.
     * If running from GitHub Pages or a different origin, use localhost.
     */
    _detectBackendUrl() {
        const hostname = window.location.hostname;

        // If running locally (served by FastAPI), use relative URLs
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return `${window.location.protocol}//${hostname}:8000`;
        }

        // If running from GitHub Pages or other static host, 
        // try to connect to a local backend
        return 'http://localhost:8000';
    }

    /**
     * Set a custom backend URL.
     * @param {string} url - The backend URL to use.
     */
    setBaseUrl(url) {
        this.baseUrl = url.replace(/\/$/, ''); // Remove trailing slash
    }

    /**
     * Make an API request.
     * @param {string} endpoint - API endpoint path.
     * @param {object} options - Fetch options.
     * @returns {Promise<object>} Response data.
     */
    async _request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;

        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers,
            },
        };

        try {
            const response = await fetch(url, mergedOptions);

            if (!response.ok) {
                const error = await response.json().catch(() => ({
                    detail: `HTTP Error ${response.status}`,
                }));
                throw new Error(error.detail || `Request failed with status ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('Cannot connect to backend server. Make sure the server is running.');
            }
            throw error;
        }
    }

    /**
     * Validate a Gemini API key.
     * @param {string} apiKey - The API key to validate.
     * @returns {Promise<{valid: boolean, message: string}>}
     */
    async validateKey(apiKey) {
        return this._request('/api/validate-key', {
            method: 'POST',
            body: JSON.stringify({ api_key: apiKey }),
        });
    }

    /**
     * Start the video generation pipeline.
     * @param {object} params - Generation parameters.
     * @param {string} params.apiKey - Gemini API key.
     * @param {string} params.idea - The video idea/concept.
     * @param {string} params.language - Target language.
     * @param {string} params.musicType - Music type selection.
     * @param {string} params.videoStyle - Video style selection.
     * @param {boolean} params.lipsync - Whether to enable lip sync.
     * @returns {Promise<{task_id: string, status: string, message: string}>}
     */
    async startGeneration(params) {
        return this._request('/api/generate', {
            method: 'POST',
            body: JSON.stringify({
                api_key: params.apiKey,
                idea: params.idea,
                language: params.language,
                music_type: params.musicType,
                video_style: params.videoStyle,
                lipsync: params.lipsync,
            }),
        });
    }

    /**
     * Get the current status of a generation task.
     * @param {string} taskId - The task ID.
     * @returns {Promise<object>} Task status data.
     */
    async getStatus(taskId) {
        return this._request(`/api/status/${taskId}`);
    }

    /**
     * Get the download URL for a completed task.
     * @param {string} taskId - The task ID.
     * @returns {string} Download URL.
     */
    getDownloadUrl(taskId) {
        return `${this.baseUrl}/api/download/${taskId}`;
    }

    /**
     * Get the download URL for a Colab notebook.
     * @param {string} taskId - The task ID.
     * @returns {string} Download URL for the notebook.
     */
    getNotebookDownloadUrl(taskId) {
        return `${this.baseUrl}/api/download/${taskId}?type=notebook`;
    }

    /**
     * Get audio file URL for playback.
     * @param {string} taskId - The task ID.
     * @param {number} sceneNumber - Scene number.
     * @returns {string} Audio file URL.
     */
    getAudioUrl(taskId, sceneNumber) {
        return `${this.baseUrl}/api/audio/${taskId}/scene_${String(sceneNumber).padStart(2, '0')}.mp3`;
    }

    /**
     * Get the video preview URL for a task.
     * @param {string} taskId - The task ID.
     * @returns {string} Video URL.
     */
    getVideoUrl(taskId) {
        return `${this.baseUrl}/api/video/${taskId}`;
    }

    /**
     * Check if the backend server is reachable.
     * @returns {Promise<boolean>}
     */
    async checkConnection() {
        try {
            await this._request('/api/health');
            return true;
        } catch {
            return false;
        }
    }
}

// Export singleton instance
const api = new ApiClient();
