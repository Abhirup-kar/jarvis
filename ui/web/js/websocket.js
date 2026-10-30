/**
 * JARVIS WebSocket Client
 * Manages resilient bidirectional connection with FastAPI backend.
 */
class JarvisWebSocket {
    constructor(url = null) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const defaultHost = window.location.host || '127.0.0.1:8000';
        this.url = url || `${protocol}//${defaultHost}/ws`;
        this.socket = null;
        this.listeners = new Map();
        this.reconnectInterval = 2000;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 30;
        this.isConnected = false;
    }

    connect() {
        try {
            console.log(`[HUD] Connecting to JARVIS core at ${this.url}...`);
            this.socket = new WebSocket(this.url);

            this.socket.onopen = () => {
                console.log('[HUD] Connected to JARVIS Core.');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this._emit('connected', { status: 'ONLINE' });
            };

            this.socket.onmessage = (event) => {
                try {
                    const payload = JSON.parse(event.data);
                    if (payload && payload.event) {
                        this._emit(payload.event, payload.data);
                    }
                } catch (e) {
                    console.error('[HUD] Error parsing incoming WS frame:', e);
                }
            };

            this.socket.onerror = (err) => {
                console.warn('[HUD] WebSocket encountered error:', err);
                this._emit('error', err);
            };

            this.socket.onclose = () => {
                this.isConnected = false;
                this._emit('disconnected', { status: 'OFFLINE' });
                this._reconnect();
            };
        } catch (err) {
            console.error('[HUD] Connection exception:', err);
            this._reconnect();
        }
    }

    _reconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const timeout = Math.min(this.reconnectInterval * Math.pow(1.2, this.reconnectAttempts), 10000);
            console.log(`[HUD] Reconnecting attempt ${this.reconnectAttempts} in ${timeout}ms...`);
            setTimeout(() => this.connect(), timeout);
        }
    }

    on(event, handler) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(handler);
    }

    off(event, handler) {
        if (!this.listeners.has(event)) return;
        const list = this.listeners.get(event).filter(fn => fn !== handler);
        this.listeners.set(event, list);
    }

    _emit(event, data) {
        if (this.listeners.has(event)) {
            for (const handler of this.listeners.get(event)) {
                try {
                    handler(data);
                } catch (e) {
                    console.error(`[HUD] Handler error for ${event}:`, e);
                }
            }
        }
    }

    send(data) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            const msg = typeof data === 'string' ? data : JSON.stringify(data);
            this.socket.send(msg);
        }
    }
}

window.JarvisWebSocket = JarvisWebSocket;

