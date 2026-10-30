/**
 * JARVIS Three.js 3D Holographic Arc Reactor Visualizer
 */
class JarvisScene {
    constructor(containerId = 'arc-reactor') {
        this.container = document.getElementById(containerId);
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.coreGroup = null;
        this.rings = [];
        this.particles = null;
        this.coreMesh = null;
        this.innerSphere = null;
        this.clock = null;
        this.currentState = 'IDLE';
        this.pulseSpeed = 1.0;
        this.colorPalette = {
            IDLE: { core: 0x00e5ff, rings: 0x007799, particles: 0x00e5ff },
            LISTENING: { core: 0x00ffcc, rings: 0x00aa88, particles: 0x33ffdd },
            THINKING: { core: 0xffaa00, rings: 0xcc7700, particles: 0xffcc33 },
            EXECUTING: { core: 0xff3366, rings: 0xaa1133, particles: 0xff6688 },
            SPEAKING: { core: 0x77eeff, rings: 0x00ccff, particles: 0xccffff }
        };
    }

    init() {
        if (!this.container || typeof THREE === 'undefined') {
            console.warn('[HUD Scene] Three.js or container not available.');
            return;
        }

        const width = this.container.clientWidth || window.innerWidth;
        const height = this.container.clientHeight || window.innerHeight;

        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
        this.camera.position.z = 8;

        this.renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.container.appendChild(this.renderer.domElement);

        this.clock = new THREE.Clock();
        this.coreGroup = new THREE.Group();
        this.scene.add(this.coreGroup);

        this._createArcReactor();
        this._createParticleField();
        this._setupLights();

        window.addEventListener('resize', () => this._onResize());
        this._animate();
    }

    _createArcReactor() {
        // Inner glowing core
        const coreGeo = new THREE.IcosahedronGeometry(1.0, 3);
        const coreMat = new THREE.MeshBasicMaterial({
            color: this.colorPalette.IDLE.core,
            wireframe: true,
            transparent: true,
            opacity: 0.8
        });
        this.coreMesh = new THREE.Mesh(coreGeo, coreMat);
        this.coreGroup.add(this.coreMesh);

        // Center solid glow sphere
        const innerGeo = new THREE.SphereGeometry(0.55, 32, 32);
        const innerMat = new THREE.MeshBasicMaterial({
            color: 0x00e5ff,
            transparent: true,
            opacity: 0.5
        });
        this.innerSphere = new THREE.Mesh(innerGeo, innerMat);
        this.coreGroup.add(this.innerSphere);

        // Concentric holographic rings
        const ringConfigs = [
            { radius: 1.6, tube: 0.02, segments: 64, rotSpeed: 0.015, axis: 'x' },
            { radius: 2.1, tube: 0.025, segments: 48, rotSpeed: -0.012, axis: 'y' },
            { radius: 2.6, tube: 0.015, segments: 32, rotSpeed: 0.008, axis: 'z' },
            { radius: 3.1, tube: 0.01, segments: 24, rotSpeed: -0.005, axis: 'xy' }
        ];

        ringConfigs.forEach(cfg => {
            const geo = new THREE.TorusGeometry(cfg.radius, cfg.tube, 8, cfg.segments);
            const mat = new THREE.MeshBasicMaterial({
                color: this.colorPalette.IDLE.rings,
                wireframe: true,
                transparent: true,
                opacity: 0.6
            });
            const ring = new THREE.Mesh(geo, mat);
            ring.userData = cfg;
            this.rings.push(ring);
            this.coreGroup.add(ring);
        });
    }

    _createParticleField() {
        const particleCount = 200;
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(particleCount * 3);

        for (let i = 0; i < particleCount * 3; i += 3) {
            const radius = 2.0 + Math.random() * 2.5;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos((Math.random() * 2) - 1);

            positions[i] = radius * Math.sin(phi) * Math.cos(theta);
            positions[i + 1] = radius * Math.sin(phi) * Math.sin(theta);
            positions[i + 2] = radius * Math.cos(phi);
        }

        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        const material = new THREE.PointsMaterial({
            color: this.colorPalette.IDLE.particles,
            size: 0.06,
            transparent: true,
            opacity: 0.75,
            blending: THREE.AdditiveBlending
        });

        this.particles = new THREE.Points(geometry, material);
        this.coreGroup.add(this.particles);
    }

    _setupLights() {
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
        this.scene.add(ambientLight);

        const pointLight = new THREE.PointLight(0x00e5ff, 2, 20);
        pointLight.position.set(0, 0, 5);
        this.scene.add(pointLight);
    }

    setState(state) {
        const normalized = (state || 'IDLE').toUpperCase();
        this.currentState = normalized;
        const colors = this.colorPalette[normalized] || this.colorPalette.IDLE;

        if (this.coreMesh) {
            this.coreMesh.material.color.setHex(colors.core);
        }
        if (this.innerSphere) {
            this.innerSphere.material.color.setHex(colors.core);
        }
        this.rings.forEach(r => {
            r.material.color.setHex(colors.rings);
        });
        if (this.particles) {
            this.particles.material.color.setHex(colors.particles);
        }

        switch (normalized) {
            case 'THINKING':
                this.pulseSpeed = 3.0;
                break;
            case 'LISTENING':
                this.pulseSpeed = 2.0;
                break;
            case 'SPEAKING':
                this.pulseSpeed = 2.5;
                break;
            case 'EXECUTING':
                this.pulseSpeed = 4.0;
                break;
            default:
                this.pulseSpeed = 1.0;
        }
    }

    _onResize() {
        if (!this.container || !this.renderer || !this.camera) return;
        const width = this.container.clientWidth || window.innerWidth;
        const height = this.container.clientHeight || window.innerHeight;
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    _animate() {
        requestAnimationFrame(() => this._animate());

        const elapsed = this.clock ? this.clock.getElapsedTime() : 0;
        const pulse = 1 + Math.sin(elapsed * this.pulseSpeed * 2) * 0.08;

        if (this.coreMesh) {
            this.coreMesh.rotation.x += 0.005 * this.pulseSpeed;
            this.coreMesh.rotation.y += 0.008 * this.pulseSpeed;
            this.coreMesh.scale.set(pulse, pulse, pulse);
        }

        if (this.innerSphere) {
            const innerPulse = 1 + Math.cos(elapsed * this.pulseSpeed * 3) * 0.12;
            this.innerSphere.scale.set(innerPulse, innerPulse, innerPulse);
        }

        this.rings.forEach(ring => {
            const cfg = ring.userData;
            if (cfg.axis === 'x') ring.rotation.x += cfg.rotSpeed * this.pulseSpeed;
            if (cfg.axis === 'y') ring.rotation.y += cfg.rotSpeed * this.pulseSpeed;
            if (cfg.axis === 'z') ring.rotation.z += cfg.rotSpeed * this.pulseSpeed;
            if (cfg.axis === 'xy') {
                ring.rotation.x += cfg.rotSpeed * this.pulseSpeed;
                ring.rotation.y += cfg.rotSpeed * this.pulseSpeed;
            }
        });

        if (this.particles) {
            this.particles.rotation.y += 0.002 * this.pulseSpeed;
            this.particles.rotation.x -= 0.001 * this.pulseSpeed;
        }

        if (this.renderer && this.scene && this.camera) {
            this.renderer.render(this.scene, this.camera);
        }
    }
}

window.JarvisScene = JarvisScene;

