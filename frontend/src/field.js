import * as THREE from 'three';

export class Field {
    constructor(scene, ourTeamNumber = null) {
        this.scene = scene;
        this.ourTeamNumber = ourTeamNumber;
        this.turrets = [];
        this.globes = [];
    }

    async load(url) {
        try {
            const response = await fetch(url);
            const data = await response.json();
            this.render(data);
            return data; // Return the data so main.js can use it
        } catch (error) {
            console.error('Failed to load field data:', error);
            return null;
        }
    }

    render(data) {
        // Clear existing
        this.turrets.forEach(m => this.scene.remove(m));
        this.globes.forEach(m => this.scene.remove(m));
        this.turrets = [];
        this.globes = [];

        // Materials
        const turretMat = new THREE.MeshStandardMaterial({ color: 0xff4444, roughness: 0.7 });
        const globeMat = new THREE.MeshStandardMaterial({ color: 0x4444ff, roughness: 0.2, metalness: 0.5 });

        // Render Turrets (skip our own turret since we render it separately)
        Object.entries(data.turrets).forEach(([id, pos]) => {
            // Skip our own turret - it's rendered by the Turret class
            if (this.ourTeamNumber && id === String(this.ourTeamNumber)) {
                return;
            }
            
            // Convert Polar (r, theta) to Cartesian (x, z)
            // Note: In 3D, Y is up. So we map to X and Z.
            const x = pos.r * Math.cos(pos.theta);
            const z = pos.r * Math.sin(pos.theta);

            const geometry = new THREE.CylinderGeometry(5, 5, 15, 16); // Approx size
            const mesh = new THREE.Mesh(geometry, turretMat);
            mesh.position.set(x, 7.5, z); // y = height/2
            mesh.castShadow = true;

            this.scene.add(mesh);
            this.turrets.push(mesh);
        });

        // Render Globes
        data.globes.forEach(pos => {
            const x = pos.r * Math.cos(pos.theta);
            const z = pos.r * Math.sin(pos.theta);
            const y = pos.z;

            const geometry = new THREE.SphereGeometry(5, 32, 32);
            const mesh = new THREE.Mesh(geometry, globeMat);
            mesh.position.set(x, y, z);
            mesh.castShadow = true;

            this.scene.add(mesh);
            this.globes.push(mesh);
        });
    }
}
