import * as THREE from 'three';

export function createScene() {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x202020); // Dark grey background

  const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 2000);
  // Move camera back to see the field (Radius ~300cm)
  camera.position.set(0, 200, 400);
  camera.lookAt(0, 0, 0);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.shadowMap.enabled = true;

  // Lights
  const ambientLight = new THREE.AmbientLight(0x404040, 2); // Soft white light
  scene.add(ambientLight);

  const directionalLight = new THREE.DirectionalLight(0xffffff, 2);
  directionalLight.position.set(100, 200, 100); // Move light higher
  directionalLight.castShadow = true;
  // Increase shadow map area
  directionalLight.shadow.camera.top = 500;
  directionalLight.shadow.camera.bottom = -500;
  directionalLight.shadow.camera.left = -500;
  directionalLight.shadow.camera.right = 500;
  scene.add(directionalLight);

  // Grid (Larger)
  const gridHelper = new THREE.GridHelper(800, 20, 0x444444, 0x333333);
  scene.add(gridHelper);

  // Origin marker (bright cylinder at 0,0)
  const originGeo = new THREE.CylinderGeometry(10, 10, 50, 32);
  const originMat = new THREE.MeshStandardMaterial({ color: 0x00ff00, emissive: 0x00ff00 });
  const originMarker = new THREE.Mesh(originGeo, originMat);
  originMarker.position.set(0, 25, 0);
  scene.add(originMarker);

  // Circle showing r=300cm boundary
  const circleGeo = new THREE.RingGeometry(298, 302, 64);
  const circleMat = new THREE.MeshBasicMaterial({ color: 0xffff00, side: THREE.DoubleSide });
  const circle = new THREE.Mesh(circleGeo, circleMat);
  circle.rotation.x = -Math.PI / 2;
  circle.position.y = 0.5;
  scene.add(circle);

  // Floor (Larger)
  const planeGeometry = new THREE.PlaneGeometry(1000, 1000);
  const planeMaterial = new THREE.MeshStandardMaterial({ color: 0x1a1a1a });
  const plane = new THREE.Mesh(planeGeometry, planeMaterial);
  plane.rotation.x = -Math.PI / 2;
  plane.receiveShadow = true;
  scene.add(plane);

  // Handle resize
  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  return { scene, camera, renderer };
}
