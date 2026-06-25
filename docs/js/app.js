/**
 * Main Application Logic
 * Handles routing, state management, and UI interactions.
 */

class App {
    constructor() {
        this.currentPage = 'setup';
        this.apiKey = null;
        this.currentTaskId = null;
        this.generationHistory = [];

        this._init();
    }

    /**
     * Initialize the application.
     */
    _init() {
        // Load saved state
        this._loadState();

        // Setup event listeners
        this._setupNavigation();
        this._setupSetupPage();
        this._setupDashboard();
        this._setupProgress();
        this._setupSettings();

        // Determine initial page
        if (this.apiKey) {
            this.navigateTo('dashboard');
        } else {
            this.navigateTo('setup');
        }
    }

    // === State Management ===

    /**
     * Load saved state from localStorage.
     */
    _loadState() {
        try {
            this.apiKey = localStorage.getItem('gemini_api_key') || null;
            const history = localStorage.getItem('generation_history');
            if (history) {
                this.generationHistory = JSON.parse(history);
            }
        } catch (error) {
            console.error('Failed to load state:', error);
        }
    }

    /**
     * Save state to localStorage.
     */
    _saveState() {
        try {
            if (this.apiKey) {
                localStorage.setItem('gemini_api_key', this.apiKey);
            } else {
                localStorage.removeItem('gemini_api_key');
            }
            localStorage.setItem('generation_history', JSON.stringify(this.generationHistory));
        } catch (error) {
            console.error('Failed to save state:', error);
        }
    }

    // === Navigation ===

    /**
     * Navigate to a specific page.
     * @param {string} pageName - Name of the page to show.
     */
    navigateTo(pageName) {
        // Hide all pages
        document.querySelectorAll('.page').forEach(page => {
            page.classList.remove('active');
        });

        // Show target page
        const targetPage = document.getElementById(`page-${pageName}`);
        if (targetPage) {
            targetPage.classList.add('active');
        }

        // Update nav links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
            if (link.dataset.page === pageName) {
                link.classList.add('active');
            }
        });

        // Show/hide nav based on page
        const navbar = document.querySelector('.navbar');
        if (pageName === 'setup') {
            navbar.style.display = 'none';
        } else {
            navbar.style.display = 'flex';
        }

        this.currentPage = pageName;

        // Page-specific initialization
        if (pageName === 'gallery') {
            this._renderGallery();
        }
        if (pageName === 'settings') {
            this._loadSettings();
        }
    }

    /**
     * Setup navigation event listeners.
     */
    _setupNavigation() {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = link.dataset.page;
                if (page) {
                    this.navigateTo(page);
                }
            });
        });
    }

    // === Setup Page ===

    /**
     * Setup the API key entry page.
     */
    _setupSetupPage() {
        const keyInput = document.getElementById('api-key-input');
        const startBtn = document.getElementById('btn-start-engine');
        const toggleBtn = document.getElementById('toggle-key-visibility');
        const statusEl = document.getElementById('key-status');

        // Toggle key visibility
        toggleBtn.addEventListener('click', () => {
            if (keyInput.type === 'password') {
                keyInput.type = 'text';
                toggleBtn.textContent = '🙈';
            } else {
                keyInput.type = 'password';
                toggleBtn.textContent = '👁️';
            }
        });

        // Start Engine button
        startBtn.addEventListener('click', async () => {
            const key = keyInput.value.trim();

            if (!key) {
                this._showStatus(statusEl, 'Please enter your API key.', 'error');
                return;
            }

            if (!key.startsWith('AIza')) {
                this._showStatus(statusEl, 'Invalid key format. Gemini API keys start with "AIza".', 'error');
                return;
            }

            // Show loading
            startBtn.disabled = true;
            startBtn.innerHTML = '<span class="spinner"></span> Validating...';
            statusEl.classList.add('hidden');

            try {
                const result = await api.validateKey(key);

                if (result.valid) {
                    this._showStatus(statusEl, result.message, 'success');
                    this.apiKey = key;
                    this._saveState();

                    // Navigate to dashboard after a brief delay
                    setTimeout(() => {
                        this.navigateTo('dashboard');
                    }, 1000);
                } else {
                    this._showStatus(statusEl, result.message, 'error');
                }
            } catch (error) {
                // If backend is not available, save key locally and proceed
                // (allows UI testing without backend)
                this._showStatus(
                    statusEl,
                    'Could not reach backend server. Key saved locally - you can test the UI.',
                    'info'
                );
                this.apiKey = key;
                this._saveState();

                setTimeout(() => {
                    this.navigateTo('dashboard');
                }, 2000);
            } finally {
                startBtn.disabled = false;
                startBtn.innerHTML = 'Start Engine 🚀';
            }
        });

        // Allow Enter key
        keyInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                startBtn.click();
            }
        });
    }

    // === Dashboard ===

    /**
     * Setup the dashboard/creation page.
     */
    _setupDashboard() {
        const generateBtn = document.getElementById('btn-generate');
        const lipsyncToggle = document.getElementById('lipsync-toggle');
        const lipsyncLabel = document.getElementById('lipsync-label');

        // Lip sync toggle label
        lipsyncToggle.addEventListener('change', () => {
            lipsyncLabel.textContent = lipsyncToggle.checked ? 'On' : 'Off';
        });

        // Generate button
        generateBtn.addEventListener('click', async () => {
            const idea = document.getElementById('idea-input').value.trim();
            const language = document.getElementById('language-select').value;
            const musicType = document.getElementById('music-type-select').value;
            const videoStyle = document.getElementById('style-select').value;
            const lipsync = lipsyncToggle.checked;

            // Validation
            if (!idea) {
                alert('Please enter your video idea or concept.');
                return;
            }

            if (idea.length < 10) {
                alert('Please provide a more detailed idea (at least 10 characters).');
                return;
            }

            if (!this.apiKey) {
                this.navigateTo('setup');
                return;
            }

            // Start generation
            generateBtn.disabled = true;
            generateBtn.innerHTML = '<span class="spinner"></span> Starting...';

            try {
                const result = await api.startGeneration({
                    apiKey: this.apiKey,
                    idea,
                    language,
                    musicType,
                    videoStyle,
                    lipsync,
                });

                this.currentTaskId = result.task_id;

                // Navigate to progress page
                this.navigateTo('progress');
                this._startProgressTracking(result.task_id);

            } catch (error) {
                alert(`Failed to start generation: ${error.message}`);
            } finally {
                generateBtn.disabled = false;
                generateBtn.innerHTML = 'Generate Video 🎬';
            }
        });
    }

    // === Progress Page ===

    /**
     * Setup progress page elements.
     */
    _setupProgress() {
        const backBtn = document.getElementById('btn-back-dashboard');
        const downloadBtn = document.getElementById('btn-download-result');

        backBtn.addEventListener('click', () => {
            progressManager.disconnect();
            this._resetProgressUI();
            this.navigateTo('dashboard');
        });

        downloadBtn.addEventListener('click', () => {
            if (this.currentTaskId) {
                const url = api.getDownloadUrl(this.currentTaskId);
                window.open(url, '_blank');
            }
        });
    }

    /**
     * Start tracking progress for a task.
     * @param {string} taskId - Task ID to track.
     */
    _startProgressTracking(taskId) {
        this._resetProgressUI();

        // Connect via WebSocket
        progressManager.connect(taskId, {
            onProgress: (data) => this._handleProgressUpdate(data),
            onCompleted: (data) => this._handleCompletion(data),
            onError: (data) => this._handleError(data),
        });

        // Also poll status as fallback
        this._startPolling(taskId);
    }

    /**
     * Start polling for status updates (fallback for WebSocket).
     * @param {string} taskId - Task ID to poll.
     */
    _startPolling(taskId) {
        this._pollInterval = setInterval(async () => {
            try {
                const status = await api.getStatus(taskId);

                if (status.status === 'completed' || status.status === 'failed') {
                    clearInterval(this._pollInterval);

                    if (status.status === 'completed') {
                        this._handleCompletion(status.result || status);
                    } else {
                        this._handleError({ error: status.error || 'Generation failed' });
                    }
                }
            } catch (error) {
                // Ignore polling errors (WebSocket may be handling it)
            }
        }, 5000);
    }

    /**
     * Handle a progress update from WebSocket.
     * @param {object} data - Progress data.
     */
    _handleProgressUpdate(data) {
        const stepEl = document.getElementById(`step-${data.step}`);
        if (!stepEl) return;

        // Update step appearance
        stepEl.classList.add('active');

        // Update progress bar
        const progressFill = stepEl.querySelector('.step-progress-fill');
        if (progressFill && data.progress_percent !== undefined) {
            progressFill.style.width = `${data.progress_percent}%`;
        }

        // Update message
        const messageEl = stepEl.querySelector('.step-message');
        if (messageEl && data.message) {
            messageEl.textContent = data.message;
        }

        // Update status icon
        const statusEl = stepEl.querySelector('.step-status');
        if (statusEl) {
            if (data.status === 'completed' || data.progress_percent === 100) {
                statusEl.textContent = '✅';
                stepEl.classList.remove('active');
                stepEl.classList.add('completed');
            } else if (data.status === 'coming_soon') {
                statusEl.textContent = '🔜';
                stepEl.classList.remove('active');
                stepEl.classList.add('coming-soon');
            } else if (data.status === 'skipped') {
                statusEl.textContent = '⏭️';
                stepEl.classList.remove('active');
                stepEl.classList.add('coming-soon');
            } else if (data.error) {
                statusEl.textContent = '❌';
                stepEl.classList.remove('active');
            } else {
                statusEl.textContent = '⚙️';
            }
        }

        // Update subtitle
        if (data.message) {
            document.getElementById('progress-subtitle').textContent = data.message;
        }
    }

    /**
     * Handle pipeline completion.
     * @param {object} data - Completion data with results.
     */
    _handleCompletion(data) {
        clearInterval(this._pollInterval);
        progressManager.disconnect();

        // Update subtitle
        document.getElementById('progress-subtitle').textContent = 'Generation complete!';

        // Show actions
        document.getElementById('progress-actions').classList.remove('hidden');

        // Display script output if available
        this._displayScriptOutput(data);

        // Add to history
        this._addToHistory(data);
    }

    /**
     * Handle pipeline error.
     * @param {object} data - Error data.
     */
    _handleError(data) {
        clearInterval(this._pollInterval);

        document.getElementById('progress-subtitle').textContent =
            `Error: ${data.error || 'Something went wrong'}`;
        document.getElementById('progress-actions').classList.remove('hidden');
    }

    /**
     * Display the generated script/screenplay output.
     * @param {object} data - Pipeline result data.
     */
    _displayScriptOutput(data) {
        const outputEl = document.getElementById('script-output');
        const contentEl = document.getElementById('script-content');

        if (!data || !data.steps) {
            return;
        }

        const scriptStep = data.steps.script_generation;
        if (!scriptStep || !scriptStep.screenplay) {
            return;
        }

        const screenplay = scriptStep.screenplay;
        let html = '';

        // Title
        if (screenplay.title) {
            html += `<h3 style="color: var(--accent-primary); margin-bottom: 1rem;">${screenplay.title}</h3>`;
        }

        // Scenes
        const scenes = screenplay.scenes || [];
        scenes.forEach(scene => {
            html += `
                <div class="scene-card">
                    <h4>Scene ${scene.scene_number}: ${scene.scene_type || ''}</h4>
                    <p><strong>Description:</strong> ${scene.description || ''}</p>
                    <p class="visual-prompt"><strong>Visual:</strong> ${scene.visual_prompt || ''}</p>
                    ${scene.dialogue ? `<p><strong>Dialogue/Lyrics:</strong> ${scene.dialogue}</p>` : ''}
                    <p><strong>Duration:</strong> ${scene.duration_seconds || 0}s</p>
                </div>
            `;
        });

        if (html) {
            contentEl.innerHTML = html;
            outputEl.classList.remove('hidden');
        }
    }

    /**
     * Reset the progress UI to initial state.
     */
    _resetProgressUI() {
        document.querySelectorAll('.step').forEach(step => {
            step.classList.remove('active', 'completed', 'coming-soon');
            const fill = step.querySelector('.step-progress-fill');
            if (fill) fill.style.width = '0%';
            const msg = step.querySelector('.step-message');
            if (msg) msg.textContent = '';
            const status = step.querySelector('.step-status');
            if (status) status.textContent = '⏳';
        });

        document.getElementById('progress-subtitle').textContent =
            'Please wait while AI works its magic...';
        document.getElementById('progress-actions').classList.add('hidden');
        document.getElementById('script-output').classList.add('hidden');
    }

    /**
     * Add a completed generation to history.
     * @param {object} data - Generation result data.
     */
    _addToHistory(data) {
        const entry = {
            taskId: data.task_id || this.currentTaskId,
            title: data.steps?.script_generation?.screenplay?.title || 'Untitled',
            idea: data.idea || '',
            language: data.language || 'English',
            contentType: data.music_type || 'song',
            timestamp: new Date().toISOString(),
            status: data.status || 'completed',
        };

        this.generationHistory.unshift(entry);

        // Keep only last 50 entries
        if (this.generationHistory.length > 50) {
            this.generationHistory = this.generationHistory.slice(0, 50);
        }

        this._saveState();
    }

    // === Gallery ===

    /**
     * Render the gallery page with generation history.
     */
    _renderGallery() {
        const grid = document.getElementById('gallery-grid');

        if (this.generationHistory.length === 0) {
            grid.innerHTML = `
                <div class="gallery-empty">
                    <span class="empty-icon">🎬</span>
                    <p>No videos generated yet.</p>
                    <p>Go to Dashboard to create your first video!</p>
                    <button class="btn-primary" onclick="window.app.navigateTo('dashboard')">
                        Create Video
                    </button>
                </div>
            `;
            return;
        }

        grid.innerHTML = this.generationHistory.map(entry => `
            <div class="gallery-item">
                <div class="gallery-item-preview">🎬</div>
                <div class="gallery-item-info">
                    <div class="gallery-item-title">${this._escapeHtml(entry.title)}</div>
                    <div class="gallery-item-meta">
                        ${entry.language} | ${entry.contentType} | ${this._formatDate(entry.timestamp)}
                    </div>
                    <div class="gallery-item-actions">
                        <button class="btn-secondary" onclick="window.open('${api.getDownloadUrl(entry.taskId)}', '_blank')">
                            Download 📥
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    // === Settings ===

    /**
     * Setup settings page interactions.
     */
    _setupSettings() {
        const saveBtn = document.getElementById('btn-save-settings');
        const clearBtn = document.getElementById('btn-clear-data');
        const toggleBtn = document.getElementById('settings-toggle-key');
        const keyInput = document.getElementById('settings-api-key');
        const statusEl = document.getElementById('settings-status');

        // Toggle visibility
        toggleBtn.addEventListener('click', () => {
            if (keyInput.type === 'password') {
                keyInput.type = 'text';
                toggleBtn.textContent = '🙈';
            } else {
                keyInput.type = 'password';
                toggleBtn.textContent = '👁️';
            }
        });

        // Save settings
        saveBtn.addEventListener('click', async () => {
            const key = keyInput.value.trim();

            if (!key) {
                this._showStatus(statusEl, 'Please enter an API key.', 'error');
                return;
            }

            saveBtn.disabled = true;
            saveBtn.innerHTML = '<span class="spinner"></span> Saving...';

            try {
                const result = await api.validateKey(key);

                if (result.valid) {
                    this.apiKey = key;
                    this._saveState();
                    this._showStatus(statusEl, 'Settings saved successfully!', 'success');
                } else {
                    this._showStatus(statusEl, result.message, 'error');
                }
            } catch {
                // Save anyway if backend is unreachable
                this.apiKey = key;
                this._saveState();
                this._showStatus(statusEl, 'Key saved locally (backend unreachable).', 'info');
            } finally {
                saveBtn.disabled = false;
                saveBtn.innerHTML = 'Save Settings';
            }
        });

        // Clear all data
        clearBtn.addEventListener('click', () => {
            if (confirm('Are you sure? This will clear your API key and all local data.')) {
                localStorage.clear();
                this.apiKey = null;
                this.generationHistory = [];
                this.navigateTo('setup');
            }
        });
    }

    /**
     * Load current settings into the settings form.
     */
    _loadSettings() {
        const keyInput = document.getElementById('settings-api-key');
        if (this.apiKey) {
            keyInput.value = this.apiKey;
        }
    }

    // === Utilities ===

    /**
     * Show a status message.
     * @param {HTMLElement} el - Status element.
     * @param {string} message - Message text.
     * @param {string} type - Message type (success, error, info).
     */
    _showStatus(el, message, type) {
        el.textContent = message;
        el.className = `status-message ${type}`;
        el.classList.remove('hidden');
    }

    /**
     * Escape HTML to prevent XSS.
     * @param {string} text - Text to escape.
     * @returns {string} Escaped text.
     */
    _escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Format a date string.
     * @param {string} isoString - ISO date string.
     * @returns {string} Formatted date.
     */
    _formatDate(isoString) {
        try {
            const date = new Date(isoString);
            return date.toLocaleDateString(undefined, {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
            });
        } catch {
            return '';
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});
