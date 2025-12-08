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
const field = new Field(scene, TEAM_NUMBER);

// Load mock data and position turret
async function init() {
  const positionData = await field.load('/positions.json');
  if (positionData && positionData.turrets && positionData.turrets[TEAM_NUMBER]) {
    const ourPosition = positionData.turrets[TEAM_NUMBER];
    turret.setPosition(ourPosition.r, ourPosition.theta);
    
    // Update camera to look at our turret position
    const x = ourPosition.r * Math.cos(ourPosition.theta);
    const z = ourPosition.r * Math.sin(ourPosition.theta);
    camera.position.set(x, 200, z + 400);
    camera.lookAt(x, 0, z);
    controls.target.set(x, 0, z);
  }
  
  // Auto-calibrate on startup to point toward origin
  console.log('🎯 Auto-calibrating turret to point toward origin...');
  try {
    await fetch('/api/calibrate', { 
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ point_to_origin: true })
    });
    console.log('✅ Turret calibrated and pointing toward field origin');
  } catch (error) {
    console.error('Auto-calibration failed:', error);
  }
  
  // Sync with backend position on startup
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

// Sync position with backend
async function syncWithBackend() {
  try {
    const response = await fetch('/api/position');
    const data = await response.json();
    
    // Update UI to match backend position
    state.azimuth = data.azimuth;
    state.altitude = data.altitude;
    state.laserOn = data.laser;
    
    azimuthSlider.value = data.azimuth;
    altitudeSlider.value = data.altitude;
    azimuthVal.textContent = data.azimuth.toFixed(2) + ' rad';
    altitudeVal.textContent = data.altitude.toFixed(2) + ' rad';
    laserToggle.checked = data.laser;
    
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

// Laser Control Functions
async function setLaserState(isOn) {
  state.laserOn = isOn;
  laserToggle.checked = isOn;
  
  // Send to Python backend
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
    console.log('🔴 Laser ON - Auto-shutoff in 3 seconds');
    
    // Show visual feedback
    laserControl.classList.add('laser-active');
    laserWarning.classList.add('active');
    
    // Countdown timer display
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
    
    // Auto-shutoff after 3 seconds (competition rule)
    laserTimer = setTimeout(() => {
      setLaserState(false);
      console.log('⚫ Laser AUTO-OFF (3 second limit)');
    }, 3000);
  } else {
    console.log('⚫ Laser OFF');
    
    // Hide visual feedback
    laserControl.classList.remove('laser-active');
    laserWarning.classList.remove('active');
    
    // Clear timers
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
  // Send velocity to Python backend (fire and forget)
  fetch('/api/move', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ azimuth: azimuthVel, altitude: altitudeVel })
  }).catch(error => {
    console.error('Failed to send velocity:', error);
  });
}

// Sliders temporarily disabled - use keyboard controls
azimuthSlider.addEventListener('input', (e) => {
  // Slider control disabled in velocity mode
  console.log('Use arrow keys for control');
});

altitudeSlider.addEventListener('input', (e) => {
  // Slider control disabled in velocity mode
  console.log('Use arrow keys for control');
});

btnCalibrate.addEventListener('click', async () => {
  console.log('🎯 Calibrating - Pointing toward origin and setting zero...');
  
  // Stop movement first
  sendVelocityCommand(0, 0);
  
  // Send calibration command to Python backend
  try {
    await fetch('/api/calibrate', { 
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ point_to_origin: true })
    });
    console.log('✅ Calibration complete - Turret now points toward field origin');
    // Sync with backend position
    await syncWithBackend();
  } catch (error) {
    console.error('Failed to calibrate:', error);
  }
});

btnFetch.addEventListener('click', async () => {
  console.log('📡 Fetching competition positions...');
  btnFetch.disabled = true;
  btnFetch.textContent = 'Fetching...';
  
  try {
    const response = await fetch('/api/fetch-json', { method: 'POST' });
    const result = await response.json();
    
    console.log('✅ Positions fetched and saved');
    
    // Reload the field visualization with new data
    await field.load('/positions.json');
    console.log('✅ Field updated with new positions');
    
  } catch (error) {
    console.error('❌ Failed to fetch positions:', error);
  } finally {
    btnFetch.disabled = false;
    btnFetch.textContent = 'Fetch Positions';
  }
});

let autoTargeting = false;

btnAuto.addEventListener('click', async () => {
  if (autoTargeting) {
    console.log('⚠️ Auto-targeting already in progress');
    return;
  }
  
  autoTargeting = true;
  btnAuto.style.display = 'none';
  btnStop.style.display = 'inline-block';
  
  console.log('🎯 Starting Auto-Target Sequence...');
  
  try {
    // Call backend to execute automated targeting
    const response = await fetch('/api/auto-target', { 
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    
    const result = await response.json();
    console.log('✓ Auto-target sequence initiated:', result.message);
    console.log('  Backend is now fetching targets and firing...');
    console.log('  Check terminal for detailed progress');
    
  } catch (error) {
    console.error('❌ Failed to start auto-target:', error);
    autoTargeting = false;
    btnAuto.style.display = 'inline-block';
    btnStop.style.display = 'none';
  }
});

btnStop.addEventListener('click', async () => {
  console.log('⚠️ Stopping auto-target sequence...');
  
  try {
    await fetch('/api/stop-target', { 
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    console.log('✓ Stop command sent');
  } catch (error) {
    console.error('❌ Failed to stop:', error);
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
