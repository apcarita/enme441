import './style.css';
import { createScene } from './scene.js';
import { Turret } from './turret.js';
import { Field } from './field.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

const TEAM_NUMBER = 13;

const app = document.querySelector('#app');
const { scene, camera, renderer } = createScene();
app.appendChild(renderer.domElement);

// Add OrbitControls to look around
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;

const turret = new Turret(scene, TEAM_NUMBER);
const field = new Field(scene);

// Initialize - sync with backend
async function init() {
  await syncWithBackend();
}

init();

// UI Elements
const laserToggle = document.getElementById('laser-toggle');
const laserControl = document.getElementById('laser-control');
const laserWarning = document.getElementById('laser-warning');
const laserTimerDisplay = document.getElementById('laser-timer');
const azimuthSlider = document.getElementById('azimuth-slider');
const altitudeSlider = document.getElementById('altitude-slider');
const azimuthVal = document.getElementById('azimuth-val');
const altitudeVal = document.getElementById('altitude-val');
const btnCalibrate = document.getElementById('btn-calibrate');
const btnFetch = document.getElementById('btn-fetch');
const btnFire = document.getElementById('btn-fire');
const btnAuto = document.getElementById('btn-auto');
const btnStop = document.getElementById('btn-stop');

// State
let state = {
  azimuth: 0,
  altitude: 0,
  laserOn: false
};

let laserTimer = null;
let laserCountdownInterval = null;

// Sync all data with backend
async function syncWithBackend() {
  try {
    const response = await fetch('/api/position');
    const data = await response.json();
    
    // Update turret state
    state.azimuth = data.turret.azimuth;
    state.altitude = data.turret.altitude;
    state.laserOn = data.turret.laser;
    
    azimuthSlider.value = data.turret.azimuth;
    altitudeSlider.value = data.turret.altitude;
    azimuthVal.textContent = data.turret.azimuth.toFixed(2) + ' rad';
    altitudeVal.textContent = data.turret.altitude.toFixed(2) + ' rad';
    laserToggle.checked = data.turret.laser;
    
    // Position our turret (update if position changed)
    if (data.my_position) {
      const posChanged = !turret.positioned || 
                        Math.abs(turret.positionX - data.my_position.x) > 0.1 || 
                        Math.abs(turret.positionZ - data.my_position.z) > 0.1;
      
      if (posChanged) {
        turret.setPosition(data.my_position.x, data.my_position.z, data.my_position.angle_to_origin);
        
        // Update camera on position change
        camera.position.set(data.my_position.x, 200, data.my_position.z + 400);
        camera.lookAt(data.my_position.x, 0, data.my_position.z);
        controls.target.set(data.my_position.x, 0, data.my_position.z);
        
        turret.positioned = true;
      }
    }
    
    // Update field visualization
    if (data.enemies && data.globes) {
      console.log(`Rendering ${data.enemies.length} enemies, ${data.globes.length} globes`);
      field.update(data.enemies, data.globes);
    }
    
    return data;
  } catch (error) {
    console.error('Failed to sync with backend:', error);
    return null;
  }
}

// Frequent sync with backend for smooth display (every 100ms)
setInterval(syncWithBackend, 100);

// Keyboard controls - send velocity commands
const keysPressed = new Set();
let currentAzimuthVel = 0;
let currentAltitudeVel = 0;

document.addEventListener('keydown', (e) => {
  // Prevent default arrow key scrolling
  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
    e.preventDefault();
  }
  keysPressed.add(e.key);
  updateVelocity();
});

document.addEventListener('keyup', (e) => {
  keysPressed.delete(e.key);
  updateVelocity();
});

// Update velocity based on keys pressed
function updateVelocity() {
  let azimuthVel = 0;
  let altitudeVel = 0;
  
  if (keysPressed.has('ArrowLeft')) {
    azimuthVel -= 1;
  }
  if (keysPressed.has('ArrowRight')) {
    azimuthVel += 1;
  }
  if (keysPressed.has('ArrowUp')) {
    altitudeVel += 1;
  }
  if (keysPressed.has('ArrowDown')) {
    altitudeVel -= 1;
  }
  
  // Only send if velocity changed
  if (azimuthVel !== currentAzimuthVel || altitudeVel !== currentAltitudeVel) {
    currentAzimuthVel = azimuthVel;
    currentAltitudeVel = altitudeVel;
    sendVelocityCommand(azimuthVel, altitudeVel);
  }
}

// Laser Control
async function setLaserState(isOn) {
  state.laserOn = isOn;
  laserToggle.checked = isOn;
  
  try {
    await fetch('/api/laser', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ laser: isOn })
    });
  } catch (error) {
    console.error('Failed to set laser state:', error);
  }
  
  if (isOn) {
    laserControl.classList.add('laser-active');
    laserWarning.classList.add('active');
    
    let timeLeft = 3;
    laserTimerDisplay.textContent = timeLeft;
    
    laserCountdownInterval = setInterval(() => {
      timeLeft -= 0.1;
      if (timeLeft <= 0) {
        clearInterval(laserCountdownInterval);
      } else {
        laserTimerDisplay.textContent = timeLeft.toFixed(1);
      }
    }, 100);
    
    laserTimer = setTimeout(() => setLaserState(false), 3000);
  } else {
    laserControl.classList.remove('laser-active');
    laserWarning.classList.remove('active');
    
    if (laserTimer) {
      clearTimeout(laserTimer);
      laserTimer = null;
    }
    if (laserCountdownInterval) {
      clearInterval(laserCountdownInterval);
      laserCountdownInterval = null;
    }
  }
}

// Event Listeners
laserToggle.addEventListener('change', (e) => {
  setLaserState(e.target.checked);
});

function sendVelocityCommand(azimuthVel, altitudeVel) {
  fetch('/api/move', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ azimuth: azimuthVel, altitude: altitudeVel })
  }).catch(error => {
    console.error('Failed to send velocity:', error);
  });
}

btnCalibrate.addEventListener('click', async () => {
  sendVelocityCommand(0, 0);
  try {
    await fetch('/api/calibrate', { method: 'POST' });
    await syncWithBackend();
  } catch (error) {
    console.error('Calibration failed:', error);
  }
});

btnFetch.addEventListener('click', async () => {
  btnFetch.disabled = true;
  btnFetch.textContent = 'Fetching...';
  try {
    await fetch('/api/fetch-json', { method: 'POST' });
  } catch (error) {
    console.error('Fetch failed:', error);
  } finally {
    btnFetch.disabled = false;
    btnFetch.textContent = 'Fetch Positions';
  }
});

btnFire.addEventListener('click', async () => {
  if (state.laserOn) return; // Already firing
  
  btnFire.disabled = true;
  btnFire.textContent = 'Firing...';
  
  // Fire for 3 seconds
  await setLaserState(true);
  
  // Re-enable button after complete
  setTimeout(() => {
    btnFire.disabled = false;
    btnFire.textContent = '🔴 Fire Laser (3s)';
  }, 3100); // Slightly longer than laser duration
});

let autoTargeting = false;

btnAuto.addEventListener('click', async () => {
  if (autoTargeting) return;
  
  autoTargeting = true;
  btnAuto.style.display = 'none';
  btnStop.style.display = 'inline-block';
  
  try {
    await fetch('/api/auto-target', { method: 'POST' });
  } catch (error) {
    console.error('Failed to start auto-target:', error);
    autoTargeting = false;
    btnAuto.style.display = 'inline-block';
    btnStop.style.display = 'none';
  }
});

btnStop.addEventListener('click', async () => {
  try {
    await fetch('/api/stop-target', { method: 'POST' });
  } catch (error) {
    console.error('Failed to stop:', error);
  }
  
  autoTargeting = false;
  btnAuto.style.display = 'inline-block';
  btnStop.style.display = 'none';
});

// Animation Loop
function animate() {
  requestAnimationFrame(animate);

  controls.update();

  // Update Turret
  turret.update(state.azimuth, state.altitude, state.laserOn);

  renderer.render(scene, camera);
}

// Start the animation loop
animate();
