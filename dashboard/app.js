/**
 * PACKET MONITOR — APPLICATION LOGIC
 * =============================================
 * Handles modes and packet counters.
 */

const API = '';
let currentState = null;

document.addEventListener('DOMContentLoaded', () => {
    initClock();
    fetchState();
    setInterval(fetchState, 3000);
});

function initClock() {
    const clockEl = document.getElementById('hud-clock');
    const update = () => {
        clockEl.textContent = new Date().toLocaleTimeString('en-US', { hour12: false });
    };
    update();
    setInterval(update, 1000);
}

async function fetchState() {
    try {
        const res = await fetch(`${API}/api/state`);
        const data = await res.json();
        renderDashboard(data);
    } catch (err) {
        console.error('State link error:', err);
    }
}

function renderDashboard(state) {
    // Mode Update
    document.querySelectorAll('.m-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.id === `m-${state.mode.toLowerCase()}`) btn.classList.add('active');
    });
    document.getElementById('mode-detail').textContent = state.mode_reason;
    document.getElementById('signal-label').textContent = `SIGNAL: ${state.signal_status}`;

    // Packet Update
    const sentEl = document.getElementById('packets-sent');
    const recEl = document.getElementById('packets-received');
    
    animateValue(sentEl, state.telemetry.packets.transmitted);
    animateValue(recEl, state.telemetry.packets.received);

    // Quick Queue Visibility
    const quickQueue = document.getElementById('quick-queue');
    if (state.pending_actions.length > 0) {
        quickQueue.classList.remove('hidden');
    } else {
        quickQueue.classList.add('hidden');
    }
}

function animateValue(obj, endValue) {
    const startValue = parseInt(obj.textContent) || 0;
    if (startValue === endValue) return;
    
    obj.textContent = endValue;
    obj.style.transform = 'scale(1.2)';
    setTimeout(() => obj.style.transform = 'scale(1)', 200);
}

async function setMode(mode) {
    try {
        await fetch(`${API}/api/mode`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode, reason: `Operator switched to ${mode}` }),
        });
        showToast(`MODE: ${mode}`, 'info');
        fetchState();
    } catch (err) {
        showToast('Mode Switch Failed', 'error');
    }
}

async function triggerNewScan() {
    try {
        const res = await fetch(`${API}/api/scan`, { method: 'POST' });
        const data = await res.json();
        showToast(`SCAN COMPLETE: Data packets buffered`, 'success');
        fetchState();
    } catch (err) {
        showToast('Scan error', 'error');
    }
}

async function approveMostRecent() {
    try {
        const state = await (await fetch(`${API}/api/state`)).json();
        for (const act of state.pending_actions) {
            await fetch(`${API}/api/approve/${act.action_id}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ operator: 'CPT. TRIPATHI' }),
            });
        }
        showToast(`AUTHORIZING: Packets transmitted egress`, 'info');
        fetchState();
    } catch (err) {
        showToast('Auth error', 'error');
    }
}

async function resetSystem() {
    if (!confirm('RESET SYSTEM PACKET COUNTERS?')) return;
    try {
        await fetch(`${API}/api/reset`, { method: 'POST' });
        showToast('SYSTEM RESET COMPLETE', 'warning');
        fetchState();
    } catch (err) {
        showToast('Reset failed', 'error');
    }
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.style.cssText = `
        padding: 12px 24px;
        border: 1px solid var(--border);
        background: rgba(0,0,0,0.8);
        border-radius: 8px;
        color: #fff;
        margin-bottom: 10px;
        font-family: 'JetBrains Mono';
        font-size: 0.8rem;
        border-left: 4px solid var(--cyan);
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    `;
    if (type === 'success') toast.style.borderColor = 'var(--emerald)';
    if (type === 'error') toast.style.borderColor = 'var(--crimson)';
    
    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}
