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

// Laser Control Functions
async function setLaserState(isOn) {
  state.laserOn = isOn;
  laserToggle.checked = isOn;
  
  // TODO: Send to Python backend
  // Example API call (implement when backend is ready):
  /*
  try {
    await fetch('/api/laser', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ laser: isOn })
    });
  } catch (error) {
    console.error('Failed to set laser state:', error);
  }
  */
  
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

async function setMotorAngles(azimuth, altitude) {
  state.azimuth = azimuth;
  state.altitude = altitude;
  azimuthSlider.value = azimuth;
  altitudeSlider.value = altitude;
  azimuthVal.textContent = azimuth.toFixed(2) + ' rad';
  altitudeVal.textContent = altitude.toFixed(2) + ' rad';
  
  // TODO: Send to Python backend
  // Example API call (implement when backend is ready):
  /*
  try {
    await fetch('/api/motors', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ azimuth, altitude })
    });
  } catch (error) {
    console.error('Failed to set motor angles:', error);
  }
  */
}

azimuthSlider.addEventListener('input', (e) => {
  setMotorAngles(parseFloat(e.target.value), state.altitude);
});

altitudeSlider.addEventListener('input', (e) => {
  setMotorAngles(state.azimuth, parseFloat(e.target.value));
});

btnCalibrate.addEventListener('click', async () => {
  console.log('🎯 Calibrating - Setting Zero Position...');
  await setMotorAngles(0, 0);
  
  // TODO: Send calibration command to Python backend
  /*
  try {
    await fetch('/api/calibrate', { method: 'POST' });
    console.log('✅ Calibration complete');
  } catch (error) {
    console.error('Failed to calibrate:', error);
  }
  */
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
