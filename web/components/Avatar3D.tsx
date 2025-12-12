import React, { useRef, useEffect, Suspense } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, useGLTF } from '@react-three/drei';
import * as THREE from 'three';

interface ModelProps {
    url: string;
}

function Model({ url }: ModelProps) {
    const { scene } = useGLTF(url);
    const modelRef = useRef<THREE.Group>(null);

    useEffect(() => {
        if (scene) {
            const twoToneGradient = new Uint8Array([180, 180, 180, 255, 255, 255]);
            const gradientMap = new THREE.DataTexture(twoToneGradient, 2, 1, THREE.RGBFormat);
            gradientMap.minFilter = THREE.NearestFilter;
            gradientMap.magFilter = THREE.NearestFilter;
            gradientMap.needsUpdate = true;

            scene.traverse((child) => {
                if ((child as THREE.Mesh).isMesh) {
                    const mesh = child as THREE.Mesh;
                    mesh.castShadow = true;
                    mesh.receiveShadow = true;
                    mesh.frustumCulled = false;

                    console.log(`[3D] Mesh: ${mesh.name}`);

                    const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
                    const newMaterials: THREE.Material[] = [];

                    materials.forEach((mat) => {
                        const oldMat = mat as THREE.MeshStandardMaterial;
                        if (oldMat && oldMat.isMeshStandardMaterial) {
                            const boostedColor = oldMat.color.clone();
                            const hsl = { h: 0, s: 0, l: 0 };
                            boostedColor.getHSL(hsl);
                            hsl.s = Math.min(hsl.s * 1.3, 1.0);
                            hsl.l = Math.min(hsl.l * 1.1, 1.0);
                            boostedColor.setHSL(hsl.h, hsl.s, hsl.l);

                            const toonMat = new THREE.MeshToonMaterial({
                                color: boostedColor,
                                map: oldMat.map,
                                gradientMap: gradientMap,
                                side: THREE.DoubleSide,
                                transparent: oldMat.transparent,
                                alphaTest: oldMat.alphaTest || 0.1,
                            });

                            if (oldMat.map) {
                                oldMat.map.minFilter = THREE.LinearFilter;
                                oldMat.map.magFilter = THREE.LinearFilter;
                                oldMat.map.generateMipmaps = false;
                            }

                            newMaterials.push(toonMat);
                        } else {
                            newMaterials.push(mat);
                        }
                    });

                    mesh.material = newMaterials.length === 1 ? newMaterials[0] : newMaterials;

                    if (mesh.morphTargetInfluences) {
                        console.log(`[3D] Shape keys on ${mesh.name}:`, Object.keys(mesh.morphTargetDictionary || {}));
                    }
                }
            });
        }
    }, [scene]);

    useFrame((state) => {
        if (modelRef.current) {
            modelRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.3) * 0.05;
        }
    });

    return (
        <primitive
            ref={modelRef}
            object={scene}
            scale={4.5}
            position={[0, -4.5, 0]}
        />
    );
}

function LoadingFallback() {
    return (
        <mesh>
            <sphereGeometry args={[0.5, 32, 32]} />
            <meshStandardMaterial color="#a855f7" wireframe />
        </mesh>
    );
}

interface Avatar3DProps {
    className?: string;
}

export const Avatar3D: React.FC<Avatar3DProps> = ({ className }) => {
    return (
        <div className={`w-full h-full ${className || ''}`}>
            <Canvas
                camera={{ position: [0, 1, 5], fov: 45 }}
                gl={{ antialias: true, alpha: true, toneMapping: THREE.NoToneMapping }}
                style={{ background: 'transparent' }}
            >
                <ambientLight intensity={3.2} color="#d8c2a1ff" />
                <directionalLight
                    position={[3, 5, 5]}
                    intensity={1.5}
                    color="#ffffff"
                />
                <directionalLight position={[-2, 3, -2]} intensity={0.8} color="#ffeedd" />
                <hemisphereLight
                    args={['#ffeedd', '#ddccbb', 0.6]}
                />

                <Suspense fallback={<LoadingFallback />}>
                    <Model url="/assets/AnnieMie.glb" />
                </Suspense>

                <OrbitControls
                    enablePan={false}
                    enableZoom={true}
                    minDistance={3}
                    maxDistance={10}
                    minPolarAngle={Math.PI / 4}
                    maxPolarAngle={Math.PI / 2}
                    target={[0, 0, 0]}
                />
            </Canvas>
        </div>
    );
};
