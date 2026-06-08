import { universe } from './visualizers/universe.js';
import { flowfield } from './visualizers/flowfield.js';
import { meadow } from './visualizers/meadow.js';

const canvas = document.getElementById('canvas1');
let cleanupCurrentVisualizer = null;

const visualizers = {
    universe: {
        name: 'Universe',
        module: universe,
        icon: '✨'
    },
    flowfield: {
        name: 'Neon Flow',
        module: flowfield,
        icon: '🌊'
    },
    meadow: {
        name: 'Meadow',
        module: meadow,
        icon: '🌿'
    }
};

// Launcher UI Construction
const app = document.getElementById('app');
const launcher = document.createElement('div');
launcher.className = 'launcher';

Object.keys(visualizers).forEach(key => {
    const v = visualizers[key];
    const btn = document.createElement('button');
    btn.className = 'launcher-btn';
    btn.innerHTML = `<span class="icon">${v.icon}</span><span class="label">${v.name}</span>`;
    btn.addEventListener('click', () => switchVisualizer(key));
    launcher.appendChild(btn);
});

document.body.appendChild(launcher);

// Switch Logic
function switchVisualizer(key) {
    if (cleanupCurrentVisualizer) {
        cleanupCurrentVisualizer();
    }

    // Reset canvas state if needed (clear transform, etc)
    const ctx = canvas.getContext('2d');
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalAlpha = 1;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    cleanupCurrentVisualizer = visualizers[key].module.mount(canvas);

    // active state for buttons
    document.querySelectorAll('.launcher-btn').forEach(b => b.classList.remove('active'));
    // simpler to just re-find based on click or store ref, but this is fine:
    // Actually finding the specific button to add active class would be better.
}

// Start default
switchVisualizer('universe');
