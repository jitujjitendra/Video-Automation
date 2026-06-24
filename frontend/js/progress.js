/**
 * Live Progress Updates Module
 * Handles WebSocket communication for real-time pipeline progress.
 */

class ProgressManager {
    constructor() {
        this.ws = null;
        this.taskId = null;
        this.callbacks = {
            onProgress: null,
            onCompleted: null,
            onError: null,
        };
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000;
        this.keepaliveInterval = null;
    }

    /**
     * Connect to the WebSocket for a specific task.
     * @param {string} taskId - The task ID to monitor.
     * @param {object} callbacks - Event callbacks.
     * @param {function} callbacks.onProgress - Called on progress updates.
     * @param {function} callbacks.onCompleted - Called when generation completes.
     * @param {function} callbacks.onError - Called on errors.
     */
    connect(taskId, callbacks = {}) {
        this.taskId = taskId;
        this.callbacks = { ...this.callbacks, ...callbacks };
        this.reconnectAttempts = 0;

        this._createConnection();
    }

    /**
     * Create the WebSocket connection.
     */
    _createConnection() {
        // Determine WebSocket URL
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const hostname = window.location.hostname;
        const host = (hostname === 'localhost' || hostname === '127.0.0.1')
            ? `${hostname}:8000`
            : 'localhost:8000';

        const wsUrl = `${protocol}//${host}/ws/progress/${this.taskId}`;

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log(`[WS] Connected for task: ${this.taskId}`);
                this.reconnectAttempts = 0;
                this._startKeepalive();
            };

            this.ws.onmessage = (event) => {
                this._handleMessage(event.data);
            };

            this.ws.onclose = (event) => {
                console.log(`[WS] Connection closed: ${event.code}`);
                this._stopKeepalive();
                this._attemptReconnect();
            };

            this.ws.onerror = (error) => {
                console.error('[WS] Error:', error);
            };
        } catch (error) {
            console.error('[WS] Failed to create connection:', error);
            this._attemptReconnect();
        }
    }

    /**
     * Handle incoming WebSocket messages.
     * @param {string} data - Raw message data.
     */
    _handleMessage(data) {
        // Handle pong responses
        if (data === 'pong') return;

        try {
            const message = JSON.parse(data);

            switch (message.type) {
                case 'progress':
                    if (this.callbacks.onProgress) {
                        this.callbacks.onProgress(message.data);
                    }
                    break;

                case 'completed':
                    if (this.callbacks.onCompleted) {
                        this.callbacks.onCompleted(message.data);
                    }
                    break;

                case 'error':
                    if (this.callbacks.onError) {
                        this.callbacks.onError(message.data);
                    }
                    break;

                case 'status':
                    // Initial status update
                    if (this.callbacks.onProgress) {
                        this.callbacks.onProgress(message.data);
                    }
                    break;

                case 'keepalive':
                    // Server keepalive, ignore
                    break;

                default:
                    console.log('[WS] Unknown message type:', message.type);
            }
        } catch (error) {
            console.error('[WS] Failed to parse message:', error);
        }
    }

    /**
     * Start the keepalive ping interval.
     */
    _startKeepalive() {
        this._stopKeepalive();
        this.keepaliveInterval = setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send('ping');
            }
        }, 25000); // Ping every 25 seconds
    }

    /**
     * Stop the keepalive ping interval.
     */
    _stopKeepalive() {
        if (this.keepaliveInterval) {
            clearInterval(this.keepaliveInterval);
            this.keepaliveInterval = null;
        }
    }

    /**
     * Attempt to reconnect to the WebSocket.
     */
    _attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('[WS] Max reconnect attempts reached');
            if (this.callbacks.onError) {
                this.callbacks.onError({
                    error: 'Lost connection to server. Please refresh the page.',
                });
            }
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * this.reconnectAttempts;

        console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

        setTimeout(() => {
            if (this.taskId) {
                this._createConnection();
            }
        }, delay);
    }

    /**
     * Disconnect from the WebSocket.
     */
    disconnect() {
        this._stopKeepalive();
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.taskId = null;
    }

    /**
     * Check if currently connected.
     * @returns {boolean}
     */
    isConnected() {
        return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
    }
}

// Export singleton instance
const progressManager = new ProgressManager();
