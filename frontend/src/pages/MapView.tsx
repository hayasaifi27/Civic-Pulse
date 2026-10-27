import React, { useState, useEffect, useRef, useMemo } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { reportsApi, analyticsApi } from '../services/api';
import { ReportListItem, IssueCategory, PriorityBand } from '../types';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Select } from '../components/ui/Select';
import { Input } from '../components/ui/Input';
import { Alert } from '../components/ui/Alert';
import { Spinner } from '../components/ui/Spinner';
import { ThemeToggle } from '../components/ui/ThemeToggle';
import { MapPin, Filter, X, Layers, MapPin as MapPinIcon, AlertCircle, Search } from 'lucide-react';
import { cn, getCategoryLabel, getCategoryIcon, getCategoryColor, getPriorityColor, validateCoordinates } from '../utils/helpers';

const DEFAULT_CENTER: [number, number] = [12.9716, 77.5946];
const DEFAULT_ZOOM = 13;

const categoryOptions = [
  { value: '', label: 'All Categories' },
  ...(['pothole', 'garbage', 'streetlight', 'water_leakage', 'drainage', 'footpath', 'obstruction', 'property_damage', 'sanitation', 'other'] as IssueCategory[]).map(c => ({
    value: c,
    label: getCategoryLabel(c),
  })),
];

const statusOptions = [
  { value: '', label: 'All Statuses' },
  { value: 'reported', label: 'Reported' },
  { value: 'under_review', label: 'Under Review' },
  { value: 'verified', label: 'Verified' },
  { value: 'assigned', label: 'Assigned' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'resolved_pending_confirmation', label: 'Resolved' },
  { value: 'closed', label: 'Closed' },
];

const priorityOptions = [
  { value: '', label: 'All Priorities' },
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'critical', label: 'Critical' },
  { value: 'safety_escalation', label: 'Safety Escalation' },
];

function getMarkerColor(category: IssueCategory, priority: PriorityBand) {
  const baseColor = getCategoryColor(category);
  const priorityColors: Record<PriorityBand, string> = {
    low: '#6B7280',
    medium: '#3B82F6',
    high: '#F59E0B',
    critical: '#F97316',
    safety_escalation: '#EF4444',
  };
  return priority === 'safety_escalation' ? priorityColors[priority] : baseColor;
}

function CustomMarker({ category, priority, children }: { category: IssueCategory; priority: PriorityBand; children: React.ReactNode }) {
  const color = getMarkerColor(category, priority);
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="background: ${color}; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 11px; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">${children}</div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -32],
  });
}

export function MapView() {
  const [map, setMap] = useState<L.Map | null>(null);
  const [reports, setReports] = useState<ReportListItem[]>([]);
  const [hotspots, setHotspots] = useState<Array<{ coordinates: { latitude: number; longitude: number }; count: number; categories: IssueCategory[]; avg_priority: number }>>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({
    category: '',
    status: '',
    priority: '',
    date_from: '',
    date_to: '',
    bounds: null as { north: number; south: number; east: number; west: number } | null,
  });
  const [showFilters, setShowFilters] = useState(false);
  const [selectedReport, setSelectedReport] = useState<ReportListItem | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const markersRef = useRef<L.Marker[]>([]);

  useEffect(() => {
    if (mapContainerRef.current && !map) {
      initializeMap();
    }
  }, [map]);

  useEffect(() => {
    fetchReports();
    fetchHotspots();
  }, [filters]);

  const initializeMap = () => {
    if (!mapContainerRef.current || map) return;

    const leafletMap = L.map(mapContainerRef.current, {
      center: DEFAULT_CENTER,
      zoom: DEFAULT_ZOOM,
      zoomControl: false,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(leafletMap);

    L.control.zoom({ position: 'topright' }).addTo(leafletMap);

    setMap(leafletMap);
  };

  const fetchReports = async () => {
    try {
      setIsLoading(true);
      const params: any = { page_size: 500 };
      if (filters.category) params.category = [filters.category];
      if (filters.status) params.status = [filters.status];
      if (filters.priority) params.priority_band = [filters.priority];
      if (filters.date_from) params.date_from = filters.date_from;
      if (filters.date_to) params.date_to = filters.date_to;
      if (filters.bounds) {
        const centerLat = (filters.bounds.north + filters.bounds.south) / 2;
        const centerLng = (filters.bounds.east + filters.bounds.west) / 2;
        const radius = Math.max(
          111000 * (filters.bounds.north - filters.bounds.south) / 2,
          111000 * Math.cos(centerLat * Math.PI / 180) * (filters.bounds.east - filters.bounds.west) / 2
        );
        params.lat = centerLat;
        params.lng = centerLng;
        params.radius = Math.round(radius);
      }
      
      const response = await reportsApi.list(params);
      setReports(response.data.items);
    } catch (err) {
      setError('Failed to load reports');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchHotspots = async () => {
    try {
      const response = await analyticsApi.hotspots(500, 3);
      setHotspots(response.data);
    } catch {
      // Ignore hotspot errors
    }
  };

  useEffect(() => {
    if (!map) return;

    markersRef.current.forEach(m => map.removeLayer(m));
    markersRef.current = [];

    reports.forEach(report => {
      const marker = L.marker(
        [report.coordinates.latitude, report.coordinates.longitude],
        { icon: CustomMarker({ category: report.category, priority: report.priority_band, children: '📍' }) }
      );

      marker.bindPopup(`
        <div class="min-w-[200px] p-1">
          <div class="font-bold text-gray-900">${report.tracking_id}</div>
          <div class="text-sm text-gray-600 mt-1">${report.title || getCategoryLabel(report.category)}</div>
          <div class="flex items-center gap-2 mt-2">
            <Badge variant="status" status="${report.status}" className="text-xs">${report.status.replace('_', ' ')}</Badge>
            <Badge variant="priority" priority="${report.priority_band}" className="text-xs">${report.priority_band.replace('_', ' ')}</Badge>
          </div>
          <div class="flex items-center gap-1 text-xs text-gray-500 mt-2">
            <span>${getCategoryIcon(report.category)} ${getCategoryLabel(report.category)}</span>
          </div>
          <button onclick="window.dispatchEvent(new CustomEvent('map-report-click', { detail: '${report.id}' }))" class="mt-2 w-full text-civic-teal text-sm hover:underline">
            View Details
          </div>
        </div>
      `);

      marker.on('click', () => setSelectedReport(report));
      markersRef.current.push(marker);
      marker.addTo(map);
    });

    if (reports.length > 0 && filters.bounds === null) {
      const group = L.featureGroup(markersRef.current);
      map.fitBounds(group.getBounds().pad(0.1));
    }
  }, [map, reports, filters.bounds]);

  useEffect(() => {
    const handleReportClick = (e: CustomEvent) => {
      const report = reports.find(r => r.id === e.detail);
      if (report) setSelectedReport(report);
    };
    window.addEventListener('map-report-click', handleReportClick as EventListener);
    return () => window.removeEventListener('map-report-click', handleReportClick as EventListener);
  }, [reports]);

  const handleMapMove = () => {
    if (!map) return;
    const bounds = map.getBounds();
    setFilters(prev => ({
      ...prev,
      bounds: {
        north: bounds.getNorth(),
        south: bounds.getSouth(),
        east: bounds.getEast(),
        west: bounds.getWest(),
      },
    }));
  };

  useEffect(() => {
    if (map) {
      map.on('moveend', handleMapMove);
      return () => {
        map.off('moveend', handleMapMove);
      };
    }
  }, [map]);

  const clearFilters = () => {
    setFilters({
      category: '',
      status: '',
      priority: '',
      date_from: '',
      date_to: '',
      bounds: null,
    });
  };

  const hasActiveFilters = filters.category || filters.status || filters.priority || filters.date_from || filters.date_to;

  return (
    <div className="h-screen flex flex-col">
      <header className="sticky top-0 z-40 bg-white/95 dark:bg-gray-900/95 backdrop-blur-sm border-b border-gray-200 dark:border-gray-700 px-4 py-3 flex-shrink-0">
        <div className="max-w-full mx-auto flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold text-civic-navy dark:text-white">CivicPulse Map</h1>
            <Badge variant="primary">{reports.length} reports</Badge>
          </div>
          
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative hidden sm:block">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-gray-500" />
              <input
                type="text"
                placeholder="Search location..."
                className="input pl-10 w-64"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    geocode(e.currentTarget.value);
                  }
                }}
              />
            </div>
            
            <ThemeToggle variant="dropdown" />
            
            <Button variant={showFilters ? 'primary' : 'secondary'} size="sm" onClick={() => setShowFilters(!showFilters)}>
              <Filter className="w-4 h-4 mr-1" />
              Filters
            </Button>

            {hasActiveFilters && (
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                <X className="w-4 h-4 mr-1" />
                Clear
              </Button>
            )}
          </div>
        </div>

        {showFilters && (
          <div className="mt-4 flex flex-wrap gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 animate-slide-up">
            <Select
              value={filters.category}
              onChange={(e) => setFilters(prev => ({ ...prev, category: e.target.value }))}
              options={categoryOptions}
              placeholder="Category"
              className="w-48"
            />
            <Select
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              options={statusOptions}
              placeholder="Status"
              className="w-40"
            />
            <Select
              value={filters.priority}
              onChange={(e) => setFilters(prev => ({ ...prev, priority: e.target.value }))}
              options={priorityOptions}
              placeholder="Priority"
              className="w-40"
            />
            <Input
              type="date"
              value={filters.date_from}
              onChange={(e) => setFilters(prev => ({ ...prev, date_from: e.target.value }))}
              placeholder="From Date"
              className="w-40"
            />
            <Input
              type="date"
              value={filters.date_to}
              onChange={(e) => setFilters(prev => ({ ...prev, date_to: e.target.value }))}
              placeholder="To Date"
              className="w-40"
            />
          </div>
        )}
      </header>

      <div className="flex-1 relative overflow-hidden">
        <div 
          ref={mapContainerRef} 
          className="w-full h-full"
          role="application"
          aria-label="Interactive map showing civic issue reports"
        />
        
        {isLoading && (
          <div className="absolute inset-0 bg-white/80 dark:bg-gray-900/80 flex items-center justify-center z-10">
            <Spinner size="lg" />
          </div>
        )}

        {error && (
          <div className="absolute top-20 left-4 right-4 z-10 max-w-md mx-auto">
            <Alert variant="error" onDismiss={() => setError('')}>
              {error}
            </Alert>
          </div>
        )}

        <div className="absolute bottom-4 left-4 right-4 md:left-auto md:right-4 md:bottom-4 md:top-auto md:w-72 z-10">
          <Card className="p-3">
            <h4 className="font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
              <Layers className="w-4 h-4 text-civic-teal" />
              Legend
            </h4>
            <div className="space-y-1.5 text-sm text-gray-700 dark:text-gray-300">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#E74C3C' }} />
                <span>Pothole / Road</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#F39C12' }} />
                <span>Garbage</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#3498DB' }} />
                <span>Water Leakage</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#EF4444' }} />
                <span>Safety Critical</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full border-2 border-white dark:border-gray-800 bg-gray-400" style={{ boxShadow: '0 2px 8px rgba(0,0,0,0.3)' }} />
                <span>Cluster</span>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {selectedReport && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4 bg-black/50" onClick={() => setSelectedReport(null)}>
          <Card className="w-full max-w-md max-h-[80vh] overflow-y-auto animate-slide-up" onClick={(e) => e.stopPropagation()}>
            <div className="p-4 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Badge variant="primary">{selectedReport.tracking_id}</Badge>
                <Badge variant="status" status={selectedReport.status}>{selectedReport.status.replace('_', ' ')}</Badge>
              </div>
              <button onClick={() => setSelectedReport(null)} className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" aria-label="Close">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4">
              {selectedReport.primary_media && (
                <img
                  src={selectedReport.primary_media.storage_path.startsWith('http') ? selectedReport.primary_media.storage_path : `/api/v1/media/${selectedReport.primary_media.id}`}
                  alt="Report photo"
                  className="w-full h-48 object-cover rounded-lg mb-3"
                />
              )}
              <h3 className="font-semibold text-gray-900 dark:text-white mb-1">{selectedReport.title || getCategoryLabel(selectedReport.category)}</h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm mb-3 line-clamp-2">{selectedReport.description}</p>
              <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-3">
                <span className="flex items-center gap-1">
                  <MapPinIcon className="w-3.5 h-3.5" />
                  {selectedReport.address || 'Map location'}
                </span>
              </div>
              <div className="flex items-center gap-2 mb-3">
                <Badge variant="priority" priority={selectedReport.priority_band}>{selectedReport.priority_band.replace('_', ' ')}</Badge>
                <span className="flex items-center gap-1">
                  {getCategoryIcon(selectedReport.category)} {getCategoryLabel(selectedReport.category)}
                </span>
              </div>
              <Button className="w-full" onClick={() => window.location.href = `/reports/${selectedReport.id}`}>
                View Full Details
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}

async function geocode(query: string) {
  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=1`,
      { headers: { 'User-Agent': 'CivicPulse/1.0' } }
    );
    const data = await response.json();
    if (data.length > 0) {
      const { lat, lon } = data[0];
      // This would need map context - simplified for now
    }
  } catch {
    // Ignore geocoding errors
  }
}