/**
 * JARVIS Spatial Hand Cursor HUD Controller
 */
class JarvisHandCursor {
    constructor(elementId = 'hand-pointer') {
        this.element = document.getElementById(elementId);
        this.coordsLabel = document.getElementById('spatial-coords');
        this.gestureLabel = document.getElementById('gesture-mode');
        this.trailContainer = document.getElementById('hud-container');
        this.lastX = 0.5;
        this.lastY = 0.5;
        this.isVisible = false;
    }

    update(data) {
        if (!this.element || !data) return;

        const x = typeof data.x === 'number' ? data.x : this.lastX;
        const y = typeof data.y === 'number' ? data.y : this.lastY;
        const z = typeof data.z === 'number' ? data.z : 0;
        const isPinching = Boolean(data.pinch);
        const isOpenPalm = Boolean(data.open_palm);

        this.lastX = x;
        this.lastY = y;

        const screenX = Math.round(x * window.innerWidth);
        const screenY = Math.round(y * window.innerHeight);

        this.element.style.display = 'block';
        this.element.style.left = `${screenX}px`;
        this.element.style.top = `${screenY}px`;

        if (isPinching) {
            this.element.classList.add('pinching');
            this.element.classList.remove('open-palm');
            this._spawnRipple(screenX, screenY, '#ff3366');
        } else if (isOpenPalm) {
            this.element.classList.add('open-palm');
            this.element.classList.remove('pinching');
        } else {
            this.element.classList.remove('pinching');
            this.element.classList.remove('open-palm');
        }

        if (this.coordsLabel) {
            this.coordsLabel.textContent = `X:${x.toFixed(2)} Y:${y.toFixed(2)} Z:${z.toFixed(2)}`;
        }

        if (this.gestureLabel) {
            if (isPinching) {
                this.gestureLabel.textContent = 'PINCH (TRIGGER)';
                this.gestureLabel.style.color = '#ff3366';
            } else if (isOpenPalm) {
                this.gestureLabel.textContent = 'OPEN PALM';
                this.gestureLabel.style.color = '#00ffcc';
            } else {
                this.gestureLabel.textContent = 'POINTING';
                this.gestureLabel.style.color = '#00e5ff';
            }
        }
    }

    _spawnRipple(x, y, color = '#00e5ff') {
        if (!this.trailContainer) return;
        const ripple = document.createElement('div');
        ripple.className = 'hud-ripple';
        ripple.style.left = `${x}px`;
        ripple.style.top = `${y}px`;
        ripple.style.borderColor = color;
        this.trailContainer.appendChild(ripple);

        setTimeout(() => {
            if (ripple.parentNode) {
                ripple.parentNode.removeChild(ripple);
            }
        }, 500);
    }

    hide() {
        if (this.element) {
            this.element.style.display = 'none';
        }
    }
}

window.JarvisHandCursor = JarvisHandCursor;

