
import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Grid, Stars, Html, Line } from '@react-three/drei';
import * as THREE from 'three';
import { Drone, DroneStatus } from '../types';

// Manually extend JSX IntrinsicElements for React Three Fiber
declare global {
  namespace JSX {
    interface IntrinsicElements {
      ambientLight: any;
      pointLight: any;
      directionalLight: any;
      group: any;
      mesh: any;
      boxGeometry: any;
      cylinderGeometry: any;
      circleGeometry: any;
      ringGeometry: any;
      meshStandardMaterial: any;
      meshBasicMaterial: any;
      primitive: any;
      line: any;
      lineBasicMaterial: any;
      bufferGeometry: any;
      perspectiveCamera: any;
      scene: any;
      points: any;
      gridHelper: any;
      axesHelper: any;
      // Added missing types
      instancedMesh: any;
      spotLight: any;
      hemisphereLight: any;
      object3D: any;
      fog: any;
      color: any;
      meshPhongMaterial: any;
      meshLambertMaterial: any;
      directionalLightHelper: any;
    }
  }
}

interface SwarmVisualizerProps {
  drones: Drone[];
  selectedDroneId?: number | null;
  onSelectDrone?: (id: number) => void;
}

// Projection Constants
// 1 degree lat is approx 111,000 meters
const METERS_PER_DEG = 111000;

// Simple Instance for distant/many objects
const DroneModel = ({ drone, isSelected, onSelect, swarmCenter }: { drone: Drone, isSelected: boolean, onSelect: (id: number) => void, swarmCenter: {lat: number, lng: number} }) => {
  const groupRef = useRef<THREE.Group>(null);
  
  // Project GPS to Local 3D Space (Meters relative to center)
  const targetPosition = useMemo(() => {
    if (!drone.latitude || !drone.longitude) return new THREE.Vector3(0, 0, 0);

    // X = Longitude (East/West), Z = Latitude (North/South) - Standard Mapping projection
    // Note: Z in 3D is usually depth. Let's map Lat to -Z (North)
    
    // Adjust longitude scale for latitude (approx cos(lat))
    const latRad = swarmCenter.lat * (Math.PI / 180);
    const lngScale = Math.cos(latRad);

    const x = (drone.longitude - swarmCenter.lng) * METERS_PER_DEG * lngScale;
    const z = -(drone.latitude - swarmCenter.lat) * METERS_PER_DEG; // Invert Z so +Lat is -Z (Forward)
    const y = (drone.altitude || 0);

    return new THREE.Vector3(x, y, z);
  }, [drone.latitude, drone.longitude, drone.altitude, swarmCenter]);

  const statusColor = useMemo(() => {
    switch (drone.status) {
      case DroneStatus.FLYING: return '#3b82f6';
      case DroneStatus.ERROR: return '#ef4444';
      case DroneStatus.IDLE: return '#f59e0b';
      case DroneStatus.RETURNING: return '#a855f7';
      case DroneStatus.LANDED: return '#10b981';
      default: return '#71717a';
    }
  }, [drone.status]);

  useFrame((state, delta) => {
    if (!groupRef.current) return;
    // Faster lerp for position updates
    groupRef.current.position.lerp(targetPosition, delta * 4);
    
    // Subtle hover animation
    if(drone.status === DroneStatus.FLYING) {
        groupRef.current.position.y += Math.sin(state.clock.elapsedTime * 2 + drone.id) * 0.02;
    }
  });

  return (
    <group>
        {/* Ground Line */}
        {isSelected && (
           <group>
             <Line points={[targetPosition, new THREE.Vector3(targetPosition.x, 0, targetPosition.z)]} color={statusColor} opacity={0.5} transparent />
             <mesh position={[targetPosition.x, 0.1, targetPosition.z]} rotation={[-Math.PI/2, 0, 0]}>
                <circleGeometry args={[2, 16]} />
                <meshBasicMaterial color={statusColor} opacity={0.3} transparent />
             </mesh>
           </group>
        )}

        <group 
        ref={groupRef} 
        onClick={(e) => { e.stopPropagation(); onSelect(drone.id); }}
        onPointerOver={() => document.body.style.cursor = 'pointer'}
        onPointerOut={() => document.body.style.cursor = 'auto'}
        >
        
        {/* Selection Ring */}
        {isSelected && (
            <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -1, 0]}>
                <ringGeometry args={[3, 3.5, 32]} />
                <meshBasicMaterial color={statusColor} opacity={0.8} transparent side={THREE.DoubleSide} />
            </mesh>
        )}

        {/* Drone Body (Scaled to approx 1m size) */}
        <mesh scale={2}> 
            <boxGeometry args={[1, 0.2, 1]} />
            <meshStandardMaterial color={statusColor} emissive={statusColor} emissiveIntensity={0.6} />
        </mesh>
        
        {/* Rotors */}
        <group scale={2}>
            <mesh position={[0.6, 0.1, 0.6]}><cylinderGeometry args={[0.4, 0.4, 0.05]} /><meshBasicMaterial color="#333" /></mesh>
            <mesh position={[-0.6, 0.1, 0.6]}><cylinderGeometry args={[0.4, 0.4, 0.05]} /><meshBasicMaterial color="#333" /></mesh>
            <mesh position={[0.6, 0.1, -0.6]}><cylinderGeometry args={[0.4, 0.4, 0.05]} /><meshBasicMaterial color="#333" /></mesh>
            <mesh position={[-0.6, 0.1, -0.6]}><cylinderGeometry args={[0.4, 0.4, 0.05]} /><meshBasicMaterial color="#333" /></mesh>
        </group>

        {isSelected && (
            <Html position={[0, 4, 0]} center distanceFactor={40} style={{ pointerEvents: 'none' }}>
                <div className="bg-black/90 px-3 py-1.5 rounded-sm border-l-2 border-white flex flex-col min-w-[100px]">
                    <span className="text-[10px] text-zinc-400 font-bold uppercase">{drone.name}</span>
                    <span className="text-xs text-white font-mono font-bold">Alt: {drone.altitude?.toFixed(1)}m</span>
                </div>
            </Html>
        )}
        </group>
    </group>
  );
};

export const SwarmVisualizer: React.FC<SwarmVisualizerProps> = ({ drones, selectedDroneId, onSelectDrone }) => {
  // Calculate Center of Mass to center the scene
  const swarmCenter = useMemo(() => {
    if (drones.length === 0) return { lat: 35.05, lng: -118.15 };
    const lat = drones.reduce((sum, d) => sum + (d.latitude || 0), 0) / drones.length;
    const lng = drones.reduce((sum, d) => sum + (d.longitude || 0), 0) / drones.length;
    return { lat, lng };
  }, [drones]);

  return (
    <div className="w-full h-full relative bg-zinc-950">
      <Canvas>
        <PerspectiveCamera makeDefault position={[100, 100, 100]} fov={50} />
        <OrbitControls 
          maxPolarAngle={Math.PI / 2 - 0.05} 
          minDistance={10}
          maxDistance={2000}
          enableDamping
          target={[0, 0, 0]}
        />
        
        <ambientLight intensity={0.2} />
        <directionalLight position={[50, 100, 50]} intensity={1.5} />
        <pointLight position={[-50, 20, -50]} intensity={0.5} color="#blue" />
        
        <Stars radius={1500} depth={50} count={3000} factor={6} saturation={0} fade />
        
        {/* Scale grid to 100m sections */}
        <Grid 
            infiniteGrid 
            fadeDistance={1500} 
            sectionColor="#3f3f46" 
            cellColor="#18181b" 
            sectionSize={100} 
            cellSize={20} 
        />

        {drones.map(drone => (
          <DroneModel 
            key={drone.id} 
            drone={drone} 
            isSelected={drone.id === selectedDroneId}
            onSelect={(id) => onSelectDrone && onSelectDrone(id)}
            swarmCenter={swarmCenter}
          />
        ))}
      </Canvas>
      
      <div className="absolute bottom-4 left-4 pointer-events-none">
         <div className="bg-black/50 backdrop-blur px-2 py-1 rounded text-[10px] text-zinc-500 font-mono border border-white/5">
            CENTER: {swarmCenter.lat.toFixed(4)}, {swarmCenter.lng.toFixed(4)}
         </div>
      </div>
    </div>
  );
};
