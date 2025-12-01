import './style.css';
import { createScene } from './scene.js';
import { Turret } from './turret.js';
import { Field } from './field.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

// Team Configuration
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
const btnAuto = document.getElementById('btn-auto');

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
  console.log('🎯 Calibrating - Setting Zero Position...');
  
  // Stop movement first
  sendVelocityCommand(0, 0);
  
  // Send calibration command to Python backend
  try {
    await fetch('/api/calibrate', { method: 'POST' });
    console.log('✅ Calibration complete');
    // Sync with backend position
    await syncWithBackend();
  } catch (error) {
    console.error('Failed to calibrate:', error);
  }
});

let autoTargeting = false;

btnAuto.addEventListener('click', async () => {
  if (autoTargeting) {
    console.log('⚠️ Auto-targeting already in progress');
    return;
  }
  
  autoTargeting = true;
  btnAuto.disabled = true;
  btnAuto.textContent = 'Targeting...';
  
  console.log('🎯 Starting Auto-Target Sequence...');
  
  // Reload positions
  const positionData = await field.load('/positions.json');
  
  // TODO: Implement actual targeting calculations
  // This is a placeholder - you'll need to:
  // 1. Get your own turret position from positions.json
  // 2. Calculate azimuth/altitude to each target
  // 3. Aim and fire for 3 seconds at each target
  
  /* Example auto-target sequence (implement when ready):
  try {
    const response = await fetch('/positions.json');
    const data = await response.json();
    
    // Example: Fire at first 3 targets
    const targets = [
      { az: 1.0, alt: 0.3 },
      { az: 2.0, alt: 0.4 },
      { az: 3.0, alt: 0.2 }
    ];
    
    for (const target of targets) {
      console.log(`Targeting: az=${target.az}, alt=${target.alt}`);
      await setMotorAngles(target.az, target.alt);
      await new Promise(resolve => setTimeout(resolve, 500)); // Aim delay
      
      // Fire for 3 seconds
      await setLaserState(true);
      await new Promise(resolve => setTimeout(resolve, 3000));
      // Laser auto-turns off after 3 seconds
      
      await new Promise(resolve => setTimeout(resolve, 500)); // Delay between targets
    }
    
    console.log('✅ Auto-target sequence complete');
  } catch (error) {
    console.error('Auto-target failed:', error);
  }
  */
  
  // For now, just demonstrate the laser timer
  console.log('Demo: Firing laser for 3 seconds...');
  await setLaserState(true);
  await new Promise(resolve => setTimeout(resolve, 3100)); // Wait for auto-shutoff
  
  autoTargeting = false;
  btnAuto.disabled = false;
  btnAuto.textContent = 'Start Auto-Target';
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
