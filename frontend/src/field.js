import * as THREE from 'three';

export class Field {
    constructor(scene) {
        this.scene = scene;
        this.turrets = [];
        this.globes = [];
        this.turretMat = new THREE.MeshStandardMaterial({ color: 0xff4444, roughness: 0.7 });
        this.globeMat = new THREE.MeshStandardMaterial({ color: 0x4444ff, roughness: 0.2, metalness: 0.5 });
    }

    update(enemies, globes) {
        // Clear existing
        this.turrets.forEach(m => this.scene.remove(m));
        this.globes.forEach(m => this.scene.remove(m));
        this.turrets = [];
        this.globes = [];

        // Render enemy turrets at ground level (cylinder center at y=7.5 puts base at y=0)
        enemies.forEach(pos => {
            const geometry = new THREE.CylinderGeometry(5, 5, 15, 16);
            const mesh = new THREE.Mesh(geometry, this.turretMat);
            mesh.position.set(pos.x, 7.5, pos.z);
            mesh.castShadow = true;

            this.scene.add(mesh);
            this.turrets.push(mesh);
        });

        // Render globes (backend sends Cartesian coordinates)
        globes.forEach(pos => {
            const geometry = new THREE.SphereGeometry(5, 32, 32);
            const mesh = new THREE.Mesh(geometry, this.globeMat);
            mesh.position.set(pos.x, pos.y, pos.z);
            mesh.castShadow = true;

            this.scene.add(mesh);
            this.globes.push(mesh);
        });
    }
}
