
import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Map, TileLayer, GridLayer, marker, divIcon, Coords, LatLngExpression, Marker } from 'leaflet';
import { Drone, DroneStatus } from '../types';
import { DroneDetailCard } from './DroneDetailCard';
import { Layers, SignalHigh, SignalLow, WifiOff, Crosshair, Grid as GridIcon } from 'lucide-react';

interface MapViewProps {
  drones: Drone[];
  selectedDroneId?: number | null;
  onSelectDrone?: (id: number) => void;
  onOpenWaypointEditor?: (id: number) => void;
}

const getStatusColor = (status: DroneStatus) => {
  switch (status) {
    case DroneStatus.FLYING: return '#00f3ff';
    case DroneStatus.ERROR: return '#ff2a2a';
    case DroneStatus.IDLE: return '#ffae00';
    case DroneStatus.RETURNING: return '#c084fc';
    case DroneStatus.LANDED: return '#34d399';
    default: return '#64748b';
  }
};

type MapLayerType = 'dark' | 'terrain' | 'offline';

export const MapView: React.FC<MapViewProps> = ({ drones, selectedDroneId, onSelectDrone, onOpenWaypointEditor }) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const markersRef = useRef<{ [key: number]: Marker }>({});
  const layersRef = useRef<{ [key: string]: any }>({});
  
  const [activeLayer, setActiveLayer] = useState<MapLayerType>('terrain');

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    // Default center (Mojave) if no drones
    const defaultCenter: LatLngExpression = [35.0542, -118.1523];

    const mapInstance = new Map(mapContainerRef.current, {
      zoomControl: false,
      attributionControl: false,
      center: defaultCenter,
      zoom: 14,
    });

    // Dark Matter Layer - Reduced Opacity for HUD effect
    const darkLayer = new TileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
      subdomains: 'abcd',
      className: 'map-tiles-dark opacity-50 contrast-125' 
    });

    // Terrain Layer - Reduced Opacity
    const terrainLayer = new TileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
      maxZoom: 17,
      className: 'map-tiles-terrain opacity-40 grayscale-[50%]'
    });

    // Custom GridLayer for Offline fallback
    const OfflineGrid = GridLayer.extend({
      createTile: function(coords: Coords) {
        const tile = document.createElement('canvas');
        tile.width = 256;
        tile.height = 256;
        const ctx = tile.getContext('2d');
        if (ctx) {
          // Draw dark background
          ctx.fillStyle = '#0f172a'; // Zinc 900
          ctx.fillRect(0, 0, 256, 256);
          
          // Draw grid lines
          ctx.strokeStyle = '#1e293b'; // Zinc 800
          ctx.lineWidth = 1;
          ctx.strokeRect(0, 0, 256, 256);
          
          // Draw crosshair center
          ctx.beginPath();
          ctx.moveTo(128, 120);
          ctx.lineTo(128, 136);
          ctx.moveTo(120, 128);
          ctx.lineTo(136, 128);
          ctx.strokeStyle = '#334155';
          ctx.stroke();

          // Text info
          ctx.fillStyle = '#475569';
          ctx.font = '10px monospace';
          ctx.fillText(`X:${coords.x} Y:${coords.y} Z:${coords.z}`, 10, 20);
        }
        return tile;
      }
    });

    const offlineLayer = new OfflineGrid();

    layersRef.current = { dark: darkLayer, terrain: terrainLayer, offline: offlineLayer };
    
    // Default to terrain
    terrainLayer.addTo(mapInstance);
    
    mapInstanceRef.current = mapInstance;

    return () => {
      mapInstance.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Handle Layer Switching
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;
    Object.values(layersRef.current).forEach(layer => map.removeLayer(layer));
    if (layersRef.current[activeLayer]) {
      layersRef.current[activeLayer].addTo(map);
    }
  }, [activeLayer]);

  // Handle Selection: Fly to drone and open popup
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !selectedDroneId || !markersRef.current[selectedDroneId]) return;

    const marker = markersRef.current[selectedDroneId];
    // Fly to drone if not already visible or to center it
    const latLng = marker.getLatLng();
    map.flyTo(latLng, 16, { duration: 1.5 });
    
    // Open popup
    marker.openPopup();
  }, [selectedDroneId]);

  // Update Markers
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    const validDrones = drones.filter(d => d.latitude !== 0 || d.longitude !== 0);

    validDrones.forEach(drone => {
      // Use REAL coordinates
      const lat = drone.latitude ?? 0;
      const lng = drone.longitude ?? 0;
      
      const color = getStatusColor(drone.status);
      const isSelected = drone.id === selectedDroneId;
      
      const iconHtml = `
        <div style="
          width: 14px; 
          height: 14px; 
          background: ${color};
          border: 2px solid ${isSelected ? '#fff' : 'rgba(0,0,0,0.5)'};
          border-radius: 50%;
          box-shadow: 0 0 ${isSelected ? '15px' : '6px'} ${color};
          transition: transform 0.2s;
          transform: scale(${isSelected ? 1.5 : 1});
        "></div>
        <div style="
            position: absolute;
            top: -24px;
            left: 50%;
            transform: translateX(-50%);
            color: ${isSelected ? 'white' : '#ccc'};
            background: ${isSelected ? 'rgba(0,0,0,0.7)' : 'transparent'};
            padding: 1px 4px;
            border-radius: 3px;
            font-size: 9px;
            font-weight: bold;
            text-shadow: 0 1px 2px black;
            display: block;
            white-space: nowrap;
            opacity: ${isSelected ? 1 : 0.7};
        ">
            ${drone.name}
        </div>
      `;

      const customIcon = divIcon({
        className: 'custom-drone-marker',
        html: iconHtml,
        iconSize: [14, 14],
        iconAnchor: [7, 7]
      });

      let m = markersRef.current[drone.id];

      if (m) {
        m.setLatLng([lat, lng]);
        m.setIcon(customIcon);
        m.setZIndexOffset(isSelected ? 1000 : 100);
      } else {
        m = marker([lat, lng], { icon: customIcon }).addTo(map);
        
        // --- Custom Popup Logic using React Portal approach ---
        const popupNode = document.createElement('div');
        popupNode.className = "custom-popup-node";
        
        m.bindPopup(popupNode, {
            maxWidth: 320,
            minWidth: 300,
            className: 'bg-transparent border-none shadow-none',
            closeButton: false,
            autoPan: true
        });

        // Store reference
        markersRef.current[drone.id] = m;

        // Interaction
        m.on('click', () => {
             if(onSelectDrone) onSelectDrone(drone.id);
        });
      }
      
      // Update Popup Content
      const updatePopup = () => {
         const popupContent = m.getPopup()?.getContent();
         if (popupContent instanceof HTMLElement) {
             const root = createRoot(popupContent);
             // Pass the callback prop down
             root.render(<DroneDetailCard drone={drone} onOpenWaypointEditor={onOpenWaypointEditor} />);
         }
      };

      if (m.isPopupOpen()) {
         updatePopup();
      } else {
         m.off('popupopen').on('popupopen', updatePopup);
      }

    });

    // Cleanup removed drones
    Object.keys(markersRef.current).forEach(idStr => {
      const id = parseInt(idStr);
      if (!drones.find(d => d.id === id)) {
        markersRef.current[id].remove();
        delete markersRef.current[id];
      }
    });

  }, [drones, selectedDroneId, onSelectDrone, onOpenWaypointEditor]);

  const handleCenterSwarm = () => {
      const map = mapInstanceRef.current;
      if (!map || drones.length === 0) return;
      const totalLat = drones.reduce((sum, d) => sum + (d.latitude || 0), 0);
      const totalLng = drones.reduce((sum, d) => sum + (d.longitude || 0), 0);
      map.flyTo([totalLat / drones.length, totalLng / drones.length], 15);
  };

  return (
    <div className="w-full h-full relative bg-[#050505] overflow-hidden rounded-lg group">
      <div ref={mapContainerRef} className={`w-full h-full z-0`} style={{ background: '#09090b' }} />
      
      {/* 2D HUD Overlay */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[400] flex bg-black/80 backdrop-blur rounded-lg border border-white/10 p-1 shadow-2xl gap-1">
        <button 
            onClick={() => setActiveLayer('dark')} 
            className={`flex items-center gap-2 px-3 py-1.5 rounded text-[10px] font-bold font-mono transition-all ${activeLayer === 'dark' ? 'bg-white text-black' : 'text-slate-400 hover:text-white'}`}
        >
          <SignalHigh size={12} />
          TACTICAL
        </button>
        <button 
            onClick={() => setActiveLayer('terrain')} 
            className={`flex items-center gap-2 px-3 py-1.5 rounded text-[10px] font-bold font-mono transition-all ${activeLayer === 'terrain' ? 'bg-white text-black' : 'text-slate-400 hover:text-white'}`}
        >
          <Layers size={12} />
          TERRAIN
        </button>
        <button 
            onClick={() => setActiveLayer('offline')} 
            className={`flex items-center gap-2 px-3 py-1.5 rounded text-[10px] font-bold font-mono transition-all ${activeLayer === 'offline' ? 'bg-white text-black' : 'text-slate-400 hover:text-white'}`}
        >
          <GridIcon size={12} />
          OFFLINE
        </button>
      </div>

      <button 
        onClick={handleCenterSwarm}
        className="absolute bottom-4 right-4 z-[400] bg-surface border border-zinc-700 p-2 rounded text-white hover:bg-zinc-700 shadow-lg"
        title="Center on Swarm"
      >
        <Crosshair size={16} />
      </button>
    </div>
  );
};
