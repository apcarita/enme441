import * as THREE from 'three';

export class Turret {
    constructor(scene, teamNumber = null) {
        this.scene = scene;
        this.teamNumber = teamNumber;
        this.base = null;
        this.azimuthPart = null;
        this.altitudePart = null;
        this.laser = null;
        this.positionX = 0;
        this.positionZ = 0;

        this.init();
    }

    init() {
        // Materials
        const baseMaterial = new THREE.MeshStandardMaterial({ color: 0x333333, roughness: 0.5, metalness: 0.8 });
        const bodyMaterial = new THREE.MeshStandardMaterial({ color: 0x666666, roughness: 0.3, metalness: 0.9 });
        const headMaterial = new THREE.MeshStandardMaterial({ color: 0x888888, roughness: 0.2, metalness: 1.0 });
        const laserMaterial = new THREE.MeshBasicMaterial({ color: 0xff0000, transparent: true, opacity: 0.6 });

        // Base (Static) - 3cm tall
        const baseGeo = new THREE.CylinderGeometry(10, 12, 3, 32);
        this.base = new THREE.Mesh(baseGeo, baseMaterial);
        this.base.position.y = 1.5; // Center at 1.5cm
        this.base.castShadow = true;
        this.base.receiveShadow = true;
        this.scene.add(this.base);

        // Azimuth Part (Rotates Y) - starts at top of base
        this.azimuthPart = new THREE.Group();
        this.azimuthPart.position.y = 3; // Top of base
        this.base.add(this.azimuthPart);

        const bodyGeo = new THREE.BoxGeometry(10, 8, 10);
        const body = new THREE.Mesh(bodyGeo, bodyMaterial);
        body.position.y = 4; // Center of 8cm body
        body.castShadow = true;
        this.azimuthPart.add(body);

        // Altitude Part (Rotates X) - at LASER_HEIGHT = 9.911cm
        this.altitudePart = new THREE.Group();
        this.altitudePart.position.y = 6.911; // 3cm base + 6.911cm = 9.911cm total
        this.azimuthPart.add(this.altitudePart);

        const headGeo = new THREE.BoxGeometry(8, 8, 15);
        const head = new THREE.Mesh(headGeo, headMaterial);
        head.position.z = 2.5; // Offset slightly forward
        head.castShadow = true;
        this.altitudePart.add(head);

        // Laser Beam (Initially hidden or scaled 0)
        const laserGeo = new THREE.CylinderGeometry(0.5, 0.5, 1000, 8);
        laserGeo.rotateX(-Math.PI / 2); // Point forward
        laserGeo.translate(0, 0, 500); // Start from origin and extend
        this.laser = new THREE.Mesh(laserGeo, laserMaterial);
        this.laser.position.z = 10.0; // End of head
        this.laser.visible = false;
        this.altitudePart.add(this.laser);
    }

    setPosition(x, z, angleToOrigin) {
        this.positionX = x;
        this.positionZ = z;
        
        if (this.base) {
            this.base.position.x = x;
            this.base.position.z = z;
            
            // In Three.js, rotation.y = atan2(x, z) makes object face toward (x,z)
            // So to face origin from position (x,z), use atan2(-z, -x)
            // But we need atan2(x, z) format for Three.js, so: atan2(-x, -z)
            this.base.rotation.y = Math.atan2(-x, -z);
            console.log(`Turret at (${x.toFixed(1)}, ${z.toFixed(1)}), rotation=${this.base.rotation.y.toFixed(3)}`);
        }
    }

    update(azimuth, altitude, laserOn) {
        // Azimuth rotation is relative to the base orientation
        // Base already points toward origin, so azimuth adds to that
        if (this.azimuthPart) this.azimuthPart.rotation.y = azimuth;
        if (this.altitudePart) this.altitudePart.rotation.x = -altitude;
        if (this.laser) this.laser.visible = laserOn;
    }
}
