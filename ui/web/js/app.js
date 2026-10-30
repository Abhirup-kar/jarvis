/**
 * JARVIS Master Web HUD & Fleet Command Application
 */
document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize 3D Hologram Scene
    const scene = new JarvisScene('arc-reactor');
    scene.init();

    // 2. Initialize Spatial Hand Cursor
    const cursor = new JarvisHandCursor('hand-pointer');

    // 3. UI DOM Elements
    const sysStateEl = document.getElementById('sys-state');
    const subStateEl = document.getElementById('sub-state');
    const clockEl = document.getElementById('hud-clock');
    const logsEl = document.getElementById('event-logs');
    const commandInput = document.getElementById('hud-command-input');
    const sendBtn = document.getElementById('hud-send-btn');
    const fleetCountEl = document.getElementById('fleet-count');
    const fleetListEl = document.getElementById('fleet-node-list');

    // 4. Activity Logger Helper
    function logEvent(text, level = 'info') {
        if (!logsEl) return;
        const entry = document.createElement('div');
        entry.className = `log-entry ${level}`;
        const time = new Date().toLocaleTimeString();
        entry.textContent = `[${time}] ${text}`;
        logsEl.appendChild(entry);
        logsEl.scrollTop = logsEl.scrollHeight;

        // Keep last 50 log lines
        while (logsEl.children.length > 50) {
            logsEl.removeChild(logsEl.firstChild);
        }
    }

    // 5. Digital Clock
    function updateClock() {
        if (clockEl) {
            const now = new Date();
            clockEl.textContent = now.toTimeString().split(' ')[0] + ' UTC';
        }
    }
    setInterval(updateClock, 1000);
    updateClock();

    // 6. Connected Fleet Renderer
    function renderFleet(nodes) {
        if (!fleetListEl || !fleetCountEl) return;
        
        fleetCountEl.textContent = nodes ? nodes.length : 0;
        
        if (!nodes || nodes.length === 0) {
            fleetListEl.innerHTML = `
                <div class="no-nodes-msg">No remote nodes online.<br><span class="code-hint">Run 'python nodes/agent_daemon.py'</span></div>
            `;
            return;
        }

        fleetListEl.innerHTML = '';
        nodes.forEach(node => {
            const card = document.createElement('div');
            card.className = 'node-card';
            
            const osIcon = node.os === 'Darwin' ? '🍎 macOS' : (node.os === 'Windows' ? '🪟 Windows' : '🐧 Linux');
            const cpu = node.telemetry ? Math.round(node.telemetry.cpu_percent || 0) : 0;
            const ram = node.telemetry ? Math.round(node.telemetry.ram_percent || 0) : 0;

            card.innerHTML = `
                <div class="node-header">
                    <span>${node.node_id}</span>
                    <span class="node-os-badge">${osIcon}</span>
                </div>
                <div class="node-metrics">
                    <span>CPU: <span class="node-metric-val">${cpu}%</span></span>
                    <span>RAM: <span class="node-metric-val">${ram}%</span></span>
                    <span>Host: <span style="color:#fff">${node.hostname}</span></span>
                </div>
            `;
            fleetListEl.appendChild(card);
        });
    }

    // 7. Connect WebSocket
    const ws = new JarvisWebSocket();

    ws.on('connected', () => {
        logEvent('Neural Interface Link Established. Core Online.', 'success');
        if (sysStateEl) sysStateEl.textContent = 'ONLINE';
    });

    ws.on('disconnected', () => {
        logEvent('Interface Link Severed. Reconnecting...', 'error');
        if (sysStateEl) sysStateEl.textContent = 'OFFLINE';
    });

    ws.on('state_change', (data) => {
        if (!data || !data.to) return;
        const newState = data.to;
        logEvent(`State Transition: ${data.from || 'PREV'} -> ${newState}`, 'state');
        
        if (sysStateEl) {
            sysStateEl.textContent = newState;
            sysStateEl.className = `state-${newState.toLowerCase()}`;
        }
        if (subStateEl) {
            const subtextMap = {
                IDLE: 'Awaiting vocal or spatial input...',
                LISTENING: 'Listening to speech stream...',
                THINKING: 'Neural inference and reasoning in progress...',
                EXECUTING: 'Dispatching tool execution...',
                SPEAKING: 'Synthesizing voice response...'
            };
            subStateEl.textContent = subtextMap[newState] || `Current operation: ${newState}`;
        }

        scene.setState(newState);
    });

    ws.on('fleet_updated', (nodes) => {
        renderFleet(nodes);
    });

    ws.on('node_connected', (node) => {
        logEvent(`Remote Node Linked: ${node.node_id} (${node.os})`, 'success');
    });

    ws.on('node_disconnected', (data) => {
        logEvent(`Remote Node Offline: ${data.node_id}`, 'warn');
    });

    ws.on('hand_move', (data) => {
        cursor.update(data);
    });

    ws.on('agent_response', (data) => {
        if (data && data.text) {
            logEvent(`JARVIS: "${data.text}"`, 'success');
        }
    });

    ws.on('system_interrupted', (data) => {
        logEvent(`Barge-in interrupt triggered (${data.reason || 'user speech'})`, 'warn');
    });

    ws.on('wake_word_detected', (data) => {
        logEvent(`Wake word detected (${data.word})`, 'state');
    });

    // 8. Interactive Command Input
    function sendCommand() {
        if (!commandInput) return;
        const text = commandInput.value.trim();
        if (!text) return;

        logEvent(`User: "${text}"`, 'user');
        ws.send({ event: 'user_command', text: text });
        commandInput.value = '';
    }

    if (sendBtn) {
        sendBtn.addEventListener('click', sendCommand);
    }
    if (commandInput) {
        commandInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') sendCommand();
        });
    }

    // Connect WS pipeline
    ws.connect();
});
