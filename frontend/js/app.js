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

        // Check backend status
        this._checkBackendStatus();
        // Re-check every 30 seconds
        setInterval(() => this._checkBackendStatus(), 30000);
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
                // Backend not available - switch to demo mode
                console.log('Backend unavailable, switching to demo mode.');
                this.navigateTo('progress');
                this._runDemoMode({ idea, language, musicType, videoStyle, lipsync });
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
     * Run demo mode when backend is unavailable.
     * @param {object} settings - Generation settings from the form.
     */
    _runDemoMode(settings) {
        this._resetProgressUI();

        if (typeof DemoMode !== 'undefined') {
            DemoMode.runDemoMode(
                settings,
                (data) => this._handleProgressUpdate(data),
                (data) => {
                    this._handleCompletion(data);
                    // Show demo mode message
                    const subtitle = document.getElementById('progress-subtitle');
                    subtitle.textContent = 'Demo mode complete! Install locally for full functionality.';
                }
            );
        } else {
            // Fallback if demo.js is not loaded
            document.getElementById('progress-subtitle').textContent =
                'Demo mode - backend not available. Install locally for full functionality.';
            document.getElementById('progress-actions').classList.remove('hidden');
        }
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
            } else if (data.status === 'partial') {
                statusEl.textContent = '⚠️';
                stepEl.classList.remove('active');
                stepEl.classList.add('completed');
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

        // Store step results for later display
        if (!this._stepResults) this._stepResults = {};
        this._stepResults[data.step] = data;
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
     * Display the generated script/screenplay output and all pipeline results.
     * @param {object} data - Pipeline result data.
     */
    _displayScriptOutput(data) {
        const outputEl = document.getElementById('script-output');
        const contentEl = document.getElementById('script-content');

        if (!data || !data.steps) {
            return;
        }

        let html = '';

        // === Script Output Section ===
        const scriptStep = data.steps.script_generation;
        if (scriptStep && scriptStep.screenplay) {
            const screenplay = scriptStep.screenplay;

            html += '<details open><summary style="cursor:pointer;font-weight:bold;font-size:1.1rem;margin-bottom:0.5rem;">📝 Generated Script</summary>';

            if (screenplay.title) {
                html += `<h3 style="color: var(--accent-primary); margin-bottom: 1rem;">${screenplay.title}</h3>`;
            }

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
            html += '</details>';
        }

        // === Visual Prompts Section ===
        const visualStep = data.steps.visual_generation;
        if (visualStep && visualStep.data && visualStep.data.visual_prompts) {
            html += '<details><summary style="cursor:pointer;font-weight:bold;font-size:1.1rem;margin:1rem 0 0.5rem;">🎨 Visual Prompts (for AI Generation)</summary>';
            html += '<p style="opacity:0.7;margin-bottom:0.5rem;">Copy these prompts to Veo 3.1 / Imagen in Google AI Pro</p>';

            visualStep.data.visual_prompts.forEach(vp => {
                html += `
                    <div class="scene-card" style="border-left: 3px solid var(--accent-primary);">
                        <h4>Scene ${vp.scene_number}</h4>
                        <p><strong>Image Prompt:</strong> ${vp.image_prompt || ''}</p>
                        <p><strong>Video Prompt:</strong> ${vp.video_prompt || ''}</p>
                        <p style="opacity:0.7;"><strong>Camera:</strong> ${vp.camera_direction || ''} | <strong>Duration:</strong> ${vp.duration_seconds}s</p>
                        <p style="color:#ff6b6b;font-size:0.85rem;"><strong>Avoid:</strong> ${vp.negative_prompt || ''}</p>
                    </div>
                `;
            });
            html += '</details>';
        }

        // === Audio Output Section ===
        const audioStep = data.steps.audio_generation;
        if (audioStep && audioStep.data) {
            html += '<details><summary style="cursor:pointer;font-weight:bold;font-size:1.1rem;margin:1rem 0 0.5rem;">🎵 Audio Output</summary>';

            const audioData = audioStep.data;
            if (audioData.voiceover && audioData.voiceover.audio_files) {
                const completedFiles = audioData.voiceover.audio_files.filter(f => f.status === 'completed');
                html += `<p style="margin-bottom:0.5rem;">Generated ${completedFiles.length} audio files (voice: ${audioData.voiceover.voice_used || 'default'})</p>`;

                completedFiles.forEach(af => {
                    html += `
                        <div class="scene-card" style="border-left: 3px solid #4CAF50;">
                            <strong>Scene ${af.scene_number}</strong> - Duration: ${(af.duration_seconds || 0).toFixed(1)}s
                            ${af.audio_path ? `<br><small style="opacity:0.7;">${af.audio_path}</small>` : ''}
                        </div>
                    `;
                });
            }

            if (audioData.suno_guide) {
                html += `
                    <div class="scene-card" style="border-left: 3px solid #FF9800;">
                        <h4>Suno AI Guide</h4>
                        <p><strong>Style:</strong> ${audioData.suno_guide.style_tags || ''}</p>
                        <p><strong>BPM:</strong> ${audioData.suno_guide.estimated_bpm || 120}</p>
                        <pre style="white-space:pre-wrap;max-height:200px;overflow-y:auto;background:rgba(0,0,0,0.2);padding:0.5rem;border-radius:4px;">${audioData.suno_guide.lyrics || ''}</pre>
                    </div>
                `;
            }
            html += '</details>';
        }

        // === Lip Sync Section ===
        const lipsyncStep = data.steps.lipsync;
        if (lipsyncStep && lipsyncStep.data && lipsyncStep.data.notebook) {
            html += '<details><summary style="cursor:pointer;font-weight:bold;font-size:1.1rem;margin:1rem 0 0.5rem;">👄 Lip Sync (Colab Notebook)</summary>';
            html += `
                <div class="scene-card" style="border-left: 3px solid #9C27B0;">
                    <p><strong>Status:</strong> Notebook generated</p>
                    <p><strong>File:</strong> ${lipsyncStep.data.notebook.notebook_path || ''}</p>
                    <p><strong>Instructions:</strong></p>
                    <ol style="margin-left:1rem;">
                        ${(lipsyncStep.data.notebook.instructions || []).map(i => `<li>${i}</li>`).join('')}
                    </ol>
                </div>
            `;
            html += '</details>';
        }

        // === Editing/Output Section ===
        const editStep = data.steps.editing;
        if (editStep && editStep.data) {
            html += '<details><summary style="cursor:pointer;font-weight:bold;font-size:1.1rem;margin:1rem 0 0.5rem;">🎬 Final Output</summary>';

            if (editStep.data.output_path) {
                html += `
                    <div class="scene-card" style="border-left: 3px solid #2196F3;">
                        <p><strong>Video assembled successfully!</strong></p>
                        <p>Output: ${editStep.data.output_path}</p>
                        <p>Steps completed: ${(editStep.data.steps_completed || []).join(', ')}</p>
                    </div>
                `;
            } else if (editStep.data.assets_available) {
                html += `
                    <div class="scene-card" style="border-left: 3px solid #FF9800;">
                        <p><strong>Partial assembly</strong> - assets generated but video could not be assembled</p>
                        <p>${editStep.data.message || ''}</p>
                    </div>
                `;
            }
            html += '</details>';
        }

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
     * Check backend connectivity and update status indicator.
     */
    async _checkBackendStatus() {
        const dot = document.getElementById('status-dot');
        const text = document.getElementById('status-text');
        if (!dot || !text) return;

        try {
            const connected = await api.checkConnection();
            if (connected) {
                dot.className = 'status-dot connected';
                text.textContent = 'Connected';
            } else {
                throw new Error('not reachable');
            }
        } catch {
            // Check if we are on GitHub Pages
            const isGitHubPages = window.location.hostname.includes('github.io') ||
                                  (window.location.hostname !== 'localhost' &&
                                   window.location.hostname !== '127.0.0.1');
            if (isGitHubPages) {
                dot.className = 'status-dot demo';
                text.textContent = 'Demo Mode';
            } else {
                dot.className = 'status-dot offline';
                text.textContent = 'Offline';
            }
        }
    }

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
