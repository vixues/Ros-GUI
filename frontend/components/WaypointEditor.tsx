
import React, { useState, useEffect, useRef } from 'react';
import { Drone, Waypoint } from '../types';
import { X, Save, Plus, MapPin, Trash2, Crosshair, ArrowUp, Navigation, LocateFixed } from 'lucide-react';
import { cn } from '../lib/utils';
import { Map, TileLayer, Marker, Polyline, divIcon, LeafletMouseEvent } from 'leaflet';
import { useStore } from '../store/useStore';
import { api } from '../services/api';

interface WaypointEditorProps {
  drone: Drone;
  onClose: () => void;
}

export const WaypointEditor: React.FC<WaypointEditorProps> = ({ drone, onClose }) => {
  const { updateDrone } = useStore();
  const [waypoints, setWaypoints] = useState<Waypoint[]>(drone.waypoints || []);
  const [selectedWpId, setSelectedWpId] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  // Map Refs
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<Map | null>(null);
  const markersRef = useRef<{ [key: string]: Marker }>({});
  const polylineRef = useRef<Polyline | null>(null);

  // Initialize Map
  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    // Use drone location or fallback, but prioritize drone location significantly
    const startLat = (drone.latitude && drone.latitude !== 0) ? drone.latitude : 35.0542;
    const startLng = (drone.longitude && drone.longitude !== 0) ? drone.longitude : -118.1523;

    const map = new Map(mapRef.current, {
        zoomControl: false,
        attributionControl: false,
        center: [startLat, startLng],
        zoom: 16 // Zoomed in closer for mission planning
    });

    new TileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
      subdomains: 'abcd',
      className: 'contrast-125 opacity-60' 
    }).addTo(map);

    // Click map to add waypoint
    map.on('click', (e: LeafletMouseEvent) => {
        const newWp: Waypoint = {
            id: `wp-${Date.now()}`,
            lat: e.latlng.lat,
            lng: e.latlng.lng,
            alt: 30, // Default alt
            type: 'FLY_THROUGH',
            speed: 10
        };
        setWaypoints(prev => [...prev, newWp]);
    });

    mapInstanceRef.current = map;

    // Initial Marker for Drone Position
    const droneIcon = divIcon({
        className: 'drone-start-marker',
        html: `<div style="width: 12px; height: 12px; background: #10b981; border: 2px solid white; border-radius: 50%; box-shadow: 0 0 10px #10b981;"></div>`,
        iconSize: [12, 12],
        iconAnchor: [6, 6]
    });
    new Marker([startLat, startLng], { icon: droneIcon, interactive: false }).addTo(map);

    return () => {
        map.remove();
        mapInstanceRef.current = null;
    };
  }, []);

  // Sync Markers & Polyline
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    // 1. Draw Polyline
    const latLngs = waypoints.map(wp => [wp.lat, wp.lng] as [number, number]);
    // Prepend drone position
    if (drone.latitude && drone.longitude) {
        latLngs.unshift([drone.latitude, drone.longitude]);
    }

    if (polylineRef.current) {
        polylineRef.current.setLatLngs(latLngs);
    } else {
        polylineRef.current = new Polyline(latLngs, {
            color: '#3b82f6', // Primary Blue
            weight: 2,
            dashArray: '5, 10',
            opacity: 0.8
        }).addTo(map);
    }

    // 2. Sync Markers
    // Remove old
    Object.keys(markersRef.current).forEach(id => {
        if (!waypoints.find(wp => wp.id === id)) {
            markersRef.current[id].remove();
            delete markersRef.current[id];
        }
    });

    // Add/Update
    waypoints.forEach((wp, index) => {
        let m = markersRef.current[wp.id];
        const isSelected = selectedWpId === wp.id;

        const iconHtml = `
            <div style="
                width: 20px; height: 20px; 
                background: ${isSelected ? '#3b82f6' : '#18181b'}; 
                border: 2px solid ${isSelected ? '#fff' : '#3f3f46'};
                color: ${isSelected ? '#fff' : '#a1a1aa'};
                border-radius: 50%; 
                display: flex; align-items: center; justify-content: center;
                font-family: monospace; font-size: 10px; font-weight: bold;
                box-shadow: 0 0 10px rgba(0,0,0,0.5);
            ">${index + 1}</div>
        `;

        const icon = divIcon({
            className: 'wp-marker',
            html: iconHtml,
            iconSize: [20, 20],
            iconAnchor: [10, 10]
        });

        if (m) {
            m.setLatLng([wp.lat, wp.lng]);
            m.setIcon(icon);
            m.setZIndexOffset(isSelected ? 1000 : 0);
        } else {
            m = new Marker([wp.lat, wp.lng], { icon, draggable: true }).addTo(map);
            m.on('click', () => setSelectedWpId(wp.id));
            m.on('dragend', (e) => {
                const newLatLng = (e.target as Marker).getLatLng();
                setWaypoints(prev => prev.map(p => p.id === wp.id ? { ...p, lat: newLatLng.lat, lng: newLatLng.lng } : p));
            });
            markersRef.current[wp.id] = m;
        }
    });

  }, [waypoints, selectedWpId, drone.latitude, drone.longitude]);

  // Form Handlers
  const handleUpdateWp = (id: string, field: keyof Waypoint, value: any) => {
    setWaypoints(prev => prev.map(wp => wp.id === id ? { ...wp, [field]: value } : wp));
  };

  const handleDeleteWp = (id: string) => {
      setWaypoints(prev => prev.filter(wp => wp.id !== id));
      if (selectedWpId === id) setSelectedWpId(null);
  };

  const handleRecenter = () => {
      if(mapInstanceRef.current && drone.latitude && drone.longitude) {
          mapInstanceRef.current.flyTo([drone.latitude, drone.longitude], 17);
      }
  };

  const handleAddWaypoint = () => {
      const map = mapInstanceRef.current;
      if (!map) return;

      const center = map.getCenter();
      
      // If we have points, try to put next one slightly offset from last one, 
      // UNLESS the map center is far away (user panned), then use map center
      const lastWp = waypoints[waypoints.length - 1];
      
      let newLat = center.lat;
      let newLng = center.lng;

      // Logic: If map center is very close to last WP (user hasn't moved map), just offset
      // Otherwise use where the user is looking
      if (lastWp) {
          const dist = Math.sqrt(Math.pow(center.lat - lastWp.lat, 2) + Math.pow(center.lng - lastWp.lng, 2));
          if (dist < 0.0005) {
              newLat = lastWp.lat + 0.0005; // Offset slightly North
              newLng = lastWp.lng;
          }
      } else if (drone.latitude && drone.longitude) {
          // If no waypoints, check distance to drone
          const distToDrone = Math.sqrt(Math.pow(center.lat - drone.latitude, 2) + Math.pow(center.lng - drone.longitude, 2));
           if (distToDrone < 0.0005) {
               newLat = drone.latitude + 0.0005;
               newLng = drone.longitude;
           }
      }

      const newWp: Waypoint = {
          id: `wp-${Date.now()}`,
          lat: newLat,
          lng: newLng,
          alt: 30,
          type: 'FLY_THROUGH',
          speed: 10
      };
      setWaypoints(prev => [...prev, newWp]);
  };

  const handleSave = async () => {
      setIsSaving(true);
      try {
          await api.updateWaypoints(drone.id, waypoints);
          updateDrone(drone.id, { waypoints });
          onClose();
      } catch (e) {
          console.error(e);
      } finally {
          setIsSaving(false);
      }
  };

  return (
    <div className="fixed inset-0 z-[999] flex items-center justify-center bg-black/90 backdrop-blur-sm p-8 animate-in fade-in duration-200">
        <div className="bg-zinc-950 w-full max-w-6xl h-full max-h-[85vh] border border-zinc-800 rounded-xl shadow-2xl flex flex-col overflow-hidden">
            {/* Header */}
            <div className="h-14 border-b border-zinc-800 bg-zinc-900/50 flex items-center justify-between px-6">
                <div className="flex items-center gap-4">
                    <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400">
                        <MapPin size={20} />
                    </div>
                    <div>
                        <h2 className="text-white font-bold text-lg tracking-tight">MISSION PLANNER</h2>
                        <div className="flex items-center gap-3 text-xs font-mono text-zinc-500">
                            <span className="text-white font-bold">{drone.name}</span>
                            <span>|</span>
                            <span>{waypoints.length} WAYPOINTS</span>
                            <span>|</span>
                            <span>Est. Time: {waypoints.length * 2.5} MIN</span>
                        </div>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    <button 
                        onClick={onClose}
                        className="px-4 py-2 text-zinc-400 hover:text-white text-xs font-bold uppercase transition-colors"
                    >
                        Cancel
                    </button>
                    <button 
                        onClick={handleSave}
                        disabled={isSaving}
                        className="bg-blue-600 hover:bg-blue-500 text-white px-5 py-2 rounded-lg text-xs font-bold uppercase flex items-center gap-2 transition-all shadow-lg shadow-blue-900/20"
                    >
                        <Save size={16} />
                        {isSaving ? 'Uploading...' : 'Upload Mission'}
                    </button>
                </div>
            </div>

            {/* Content Split */}
            <div className="flex-1 flex min-h-0">
                
                {/* Left Panel: Waypoint List */}
                <div className="w-[400px] border-r border-zinc-800 flex flex-col bg-black/50">
                    <div className="p-4 border-b border-zinc-800 flex justify-between items-center bg-zinc-900/30">
                        <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Flight Path Sequence</span>
                        <button 
                            onClick={handleAddWaypoint}
                            className="p-1.5 bg-zinc-800 hover:bg-zinc-700 text-white rounded border border-zinc-700 transition-colors"
                            title="Add Waypoint"
                        >
                            <Plus size={14} />
                        </button>
                    </div>

                    <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
                        {waypoints.length === 0 && (
                            <div className="h-40 flex flex-col items-center justify-center text-zinc-600 border-2 border-dashed border-zinc-800 rounded-lg">
                                <Crosshair className="mb-2 opacity-50" />
                                <span className="text-xs font-medium">Click map to place waypoints</span>
                            </div>
                        )}
                        
                        {waypoints.map((wp, index) => (
                            <div 
                                key={wp.id}
                                onClick={() => setSelectedWpId(wp.id)}
                                className={cn(
                                    "relative p-3 rounded-lg border transition-all cursor-pointer group",
                                    selectedWpId === wp.id 
                                    ? "bg-blue-500/5 border-blue-500/30 ring-1 ring-blue-500/20" 
                                    : "bg-zinc-900 border-zinc-800 hover:border-zinc-700"
                                )}
                            >
                                {/* Timeline Connector */}
                                {index < waypoints.length - 1 && (
                                    <div className="absolute left-[19px] top-10 bottom-[-14px] w-px bg-zinc-800 z-0"></div>
                                )}

                                <div className="flex items-start gap-3 relative z-10">
                                    <div className={cn(
                                        "w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold border font-mono flex-shrink-0 mt-0.5",
                                        selectedWpId === wp.id ? "bg-blue-600 border-white text-white" : "bg-zinc-800 border-zinc-700 text-zinc-500"
                                    )}>
                                        {index + 1}
                                    </div>
                                    
                                    <div className="flex-1 space-y-3">
                                        <div className="flex justify-between items-start">
                                            <div className="flex flex-col gap-1">
                                                <select 
                                                    value={wp.type}
                                                    onChange={(e) => handleUpdateWp(wp.id, 'type', e.target.value)}
                                                    className="bg-black border border-zinc-700 text-white text-[10px] font-bold px-1.5 py-0.5 rounded focus:border-blue-500 focus:outline-none uppercase w-28"
                                                >
                                                    <option value="FLY_THROUGH">FLY THROUGH</option>
                                                    <option value="HOVER">HOVER</option>
                                                    <option value="LAND">LAND</option>
                                                    <option value="ROI">ORBIT ROI</option>
                                                </select>
                                                <div className="flex gap-2 text-[9px] font-mono text-zinc-500">
                                                    <span>{wp.lat.toFixed(6)}, {wp.lng.toFixed(6)}</span>
                                                </div>
                                            </div>
                                            <button 
                                                onClick={(e) => { e.stopPropagation(); handleDeleteWp(wp.id); }}
                                                className="text-zinc-600 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity p-1"
                                            >
                                                <Trash2 size={14} />
                                            </button>
                                        </div>

                                        <div className="grid grid-cols-2 gap-2">
                                            <div className="bg-black p-1.5 rounded border border-zinc-800 flex items-center gap-2">
                                                <ArrowUp size={12} className="text-zinc-500" />
                                                <div className="flex flex-col">
                                                    <label className="text-[8px] text-zinc-500 uppercase font-bold">Altitude</label>
                                                    <div className="flex items-center gap-1">
                                                        <input 
                                                            type="number" 
                                                            value={wp.alt}
                                                            onChange={(e) => handleUpdateWp(wp.id, 'alt', parseFloat(e.target.value))}
                                                            className="w-10 bg-transparent text-white font-mono text-xs font-bold focus:outline-none"
                                                        />
                                                        <span className="text-[9px] text-zinc-600">m</span>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="bg-black p-1.5 rounded border border-zinc-800 flex items-center gap-2">
                                                <Navigation size={12} className="text-zinc-500 rotate-90" />
                                                <div className="flex flex-col">
                                                    <label className="text-[8px] text-zinc-500 uppercase font-bold">Speed</label>
                                                    <div className="flex items-center gap-1">
                                                        <input 
                                                            type="number" 
                                                            value={wp.speed || 10}
                                                            onChange={(e) => handleUpdateWp(wp.id, 'speed', parseFloat(e.target.value))}
                                                            className="w-10 bg-transparent text-white font-mono text-xs font-bold focus:outline-none"
                                                        />
                                                        <span className="text-[9px] text-zinc-600">m/s</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Right Panel: Map */}
                <div className="flex-1 relative bg-black group">
                     <div ref={mapRef} className="absolute inset-0 z-0"></div>
                     
                     {/* Overlay Controls */}
                     <div className="absolute top-4 left-4 z-[400] pointer-events-none">
                         <div className="bg-black/80 backdrop-blur px-3 py-1.5 rounded border border-white/10 text-white text-xs font-bold shadow-lg">
                            CLICK MAP TO ADD WAYPOINT
                         </div>
                     </div>

                     <button 
                        onClick={handleRecenter}
                        className="absolute bottom-6 right-6 z-[400] bg-zinc-900/90 text-white p-2 rounded-lg border border-zinc-700 shadow-xl hover:bg-zinc-800 transition-colors"
                        title="Recenter on Drone"
                     >
                        <LocateFixed size={20} />
                     </button>
                </div>

            </div>
        </div>
    </div>
  );
};
