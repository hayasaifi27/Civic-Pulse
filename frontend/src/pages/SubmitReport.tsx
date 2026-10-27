import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { reportsApi, mediaApi } from '../services/api';
import { Category, IssueCategory, Coordinates } from '../types';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Textarea } from '../components/ui/Textarea';
import { Select } from '../components/ui/Select';
import { Alert } from '../components/ui/Alert';
import { Spinner } from '../components/ui/Spinner';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { MapPin, Camera, X, Loader2, MapPin as MapPinIcon, AlertCircle, CheckCircle } from 'lucide-react';
import { cn, getCategoryLabel, validateCoordinates, isValidImageType, isValidFileSize, formatFileSize } from '../utils/helpers';

const DEFAULT_CENTER: Coordinates = { latitude: 12.9716, longitude: 77.5946 };

const reportSchema = z.object({
  title: z.string().max(500).optional(),
  description: z.string().min(10, 'Description must be at least 10 characters').max(5000),
  category: z.enum(['pothole', 'garbage', 'streetlight', 'water_leakage', 'drainage', 'footpath', 'obstruction', 'property_damage', 'sanitation', 'other']),
  coordinates: z.object({
    latitude: z.number().min(-90).max(90),
    longitude: z.number().min(-180).max(180),
  }),
  address: z.string().max(500).optional(),
  landmark: z.string().max(500).optional(),
  is_anonymous: z.boolean().default(false),
  media_ids: z.array(z.string()).optional(),
});

type ReportForm = z.infer<typeof reportSchema>;

const CATEGORIES: Array<{ value: IssueCategory; label: string; icon: string }> = [
  { value: 'pothole', label: 'Pothole / Road Damage', icon: '🕳️' },
  { value: 'garbage', label: 'Garbage Accumulation', icon: '🗑️' },
  { value: 'streetlight', label: 'Broken Streetlight', icon: '💡' },
  { value: 'water_leakage', label: 'Water Leakage', icon: '💧' },
  { value: 'drainage', label: 'Drainage Blockage', icon: '🚰' },
  { value: 'footpath', label: 'Damaged Footpath', icon: '🚶' },
  { value: 'obstruction', label: 'Unsafe Road Obstruction', icon: '🚧' },
  { value: 'property_damage', label: 'Public Property Damage', icon: '🔨' },
  { value: 'sanitation', label: 'Sanitation Concern', icon: '🚻' },
  { value: 'other', label: 'Other / Uncertain', icon: '❓' },
];

const categoryOptions = CATEGORIES.map(c => ({ value: c.value, label: `${c.icon} ${c.label}` }));

export function SubmitReport() {
  const navigate = useNavigate();
  const [categories, setCategories] = useState<Category[]>([]);
  const [map, setMap] = useState<L.Map | null>(null);
  const [marker, setMarker] = useState<L.Marker | null>(null);
  const [mapCenter, setMapCenter] = useState<Coordinates>(DEFAULT_CENTER);
  const [selectedCoords, setSelectedCoords] = useState<Coordinates | null>(null);
  const [duplicateWarning, setDuplicateWarning] = useState<{ count: number; message: string } | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [uploadedMedia, setUploadedMedia] = useState<Array<{ id: string; preview: string; file: File }>>([]);
  const mapContainerRef = useRef<HTMLDivElement>(null);

  const { register, handleSubmit, watch, setValue, formState: { errors, isValid } } = useForm<ReportForm>({
    resolver: zodResolver(reportSchema),
    defaultValues: {
      title: '',
      description: '',
      category: 'other',
      coordinates: DEFAULT_CENTER,
      address: '',
      landmark: '',
      is_anonymous: false,
      media_ids: [],
    },
    mode: 'onChange',
  });

  const watchedCategory = watch('category');
  const watchedCoords = watch('coordinates');

  useEffect(() => {
    fetchCategories();
  }, []);

  useEffect(() => {
    if (mapContainerRef.current && !map) {
      initializeMap();
    }
  }, [map]);

  useEffect(() => {
    if (marker && selectedCoords) {
      marker.setLatLng([selectedCoords.latitude, selectedCoords.longitude]);
      map?.setView([selectedCoords.latitude, selectedCoords.longitude], map?.getZoom() || 16);
    }
  }, [selectedCoords, marker, map]);

  const fetchCategories = async () => {
    try {
      const response = await reportsApi.list({ page_size: 1 });
    } catch {
      // Categories will be loaded from static list
    }
  };

  const initializeMap = () => {
    if (!mapContainerRef.current || map) return;

    const leafletMap = L.map(mapContainerRef.current, {
      center: [mapCenter.latitude, mapCenter.longitude],
      zoom: 13,
      zoomControl: false,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(leafletMap);

    L.control.zoom({ position: 'topright' }).addTo(leafletMap);

    const customIcon = L.divIcon({
      className: 'custom-marker',
      html: `<div style="background: #14b8a6; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 12px; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">📍</div>`,
      iconSize: [32, 32],
      iconAnchor: [16, 32],
    });

    const newMarker = L.marker([mapCenter.latitude, mapCenter.longitude], { 
      icon: customIcon,
      draggable: true,
    }).addTo(leafletMap);

    newMarker.on('dragend', (e) => {
      const pos = e.target.getLatLng();
      const coords: Coordinates = { latitude: pos.lat, longitude: pos.lng };
      setSelectedCoords(coords);
      setValue('coordinates', coords, { shouldValidate: true });
      checkDuplicates(coords, watchedCategory);
      reverseGeocode(coords);
    });

    leafletMap.on('click', (e) => {
      const coords: Coordinates = { latitude: e.latlng.lat, longitude: e.latlng.lng };
      setSelectedCoords(coords);
      setValue('coordinates', coords, { shouldValidate: true });
      checkDuplicates(coords, watchedCategory);
      reverseGeocode(coords);
    });

    setMap(leafletMap);
    setMarker(newMarker);
  };

  const checkDuplicates = async (coords: Coordinates, category: IssueCategory) => {
    try {
      const response = await reportsApi.list({
        lat: coords.latitude,
        lng: coords.longitude,
        radius: 100,
        category: [category],
        page_size: 5,
      });
      if (response.data.total > 0) {
        setDuplicateWarning({
          count: response.data.total,
          message: `Found ${response.data.total} existing report${response.data.total > 1 ? 's' : ''} nearby for this category. Please check if this is a duplicate.`
        });
      } else {
        setDuplicateWarning(null);
      }
    } catch {
      // Ignore duplicate check errors
    }
  };

  const reverseGeocode = async (coords: Coordinates) => {
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${coords.latitude}&lon=${coords.longitude}&zoom=18&addressdetails=1`,
        { headers: { 'User-Agent': 'CivicPulse/1.0' } }
      );
      const data = await response.json();
      if (data.address) {
        const addressParts = [
          data.address.road,
          data.address.suburb,
          data.address.city || data.address.town || data.address.village,
        ].filter(Boolean);
        setValue('address', addressParts.join(', '));
      }
    } catch {
      // Ignore geocoding errors
    }
  };

  const handleFileUpload = async (files: FileList) => {
    for (const file of Array.from(files)) {
      if (!isValidImageType(file)) {
        setError(`File "${file.name}" is not a valid image type. Please use JPEG, PNG, WebP, or HEIC.`);
        return;
      }
      if (!isValidFileSize(file)) {
        setError(`File "${file.name}" exceeds the 10MB size limit.`);
        return;
      }
      if (uploadedMedia.length >= 5) {
        setError('Maximum 5 photos allowed per report.');
        return;
      }

      const preview = URL.createObjectURL(file);
      const tempId = `temp-${Date.now()}-${Math.random()}`;
      
      setUploadedMedia(prev => [...prev, { id: tempId, preview, file }]);
      
      try {
        const response = await mediaApi.upload(file);
        setUploadedMedia(prev => prev.map(m => m.id === tempId ? { ...m, id: response.data.id } : m));
        const currentMediaIds = watch('media_ids') || [];
        setValue('media_ids', [...currentMediaIds, response.data.id]);
      } catch {
        setError(`Failed to upload "${file.name}". Please try again.`);
        setUploadedMedia(prev => prev.filter(m => m.id !== tempId));
      }
    }
  };

  const removeMedia = (id: string) => {
    const media = uploadedMedia.find(m => m.id === id);
    if (media) {
      URL.revokeObjectURL(media.preview);
    }
    setUploadedMedia(prev => prev.filter(m => m.id !== id));
    const currentMediaIds = watch('media_ids') || [];
    setValue('media_ids', currentMediaIds.filter((m: string) => m !== id));
  };

  const onSubmit = async (data: ReportForm) => {
    setIsSubmitting(true);
    setError('');
    try {
      const response = await reportsApi.create(data);
      navigate(`/reports/${response.data.id}`, { state: { success: true } });
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to submit report. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const useCurrentLocation = () => {
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser');
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const coords: Coordinates = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        };
        setMapCenter(coords);
        setSelectedCoords(coords);
        setValue('coordinates', coords, { shouldValidate: true });
        map?.setView([coords.latitude, coords.longitude], 16);
        marker?.setLatLng([coords.latitude, coords.longitude]);
        checkDuplicates(coords, watchedCategory);
        reverseGeocode(coords);
      },
      (err) => {
        setError(err.code === err.PERMISSION_DENIED 
          ? 'Location permission denied. Please enable location access or select manually on the map.'
          : 'Unable to get your location. Please select manually on the map.'
        );
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  return (
    <div className="page-container max-w-4xl">
      <div className="mb-8">
        <h1 className="section-title">Submit a Civic Issue Report</h1>
        <p className="text-gray-600 dark:text-gray-400">Help improve your community by reporting civic issues</p>
      </div>

      {error && <Alert variant="error" className="mb-6" onDismiss={() => setError('')}>{error}</Alert>}

      {duplicateWarning && (
        <Alert variant="warning" className="mb-6" onDismiss={() => setDuplicateWarning(null)}>
          <AlertCircle className="w-5 h-5 mr-2" />
          {duplicateWarning.message}
          <button onClick={() => navigate('/map')} className="ml-2 text-civic-teal hover:underline text-sm">
            View nearby reports
          </button>
        </Alert>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6" noValidate>
        <Card className="p-6">
          <h2 className="subsection-title flex items-center gap-2">
            <MapPin className="w-5 h-5 text-civic-teal" />
            Location
          </h2>
          <p className="text-gray-500 dark:text-gray-400 text-sm mb-4">Click on the map or use the button below to set the issue location</p>
          
          <div className="relative mb-4">
            <div 
              ref={mapContainerRef} 
              className="h-96 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden"
              role="application"
              aria-label="Interactive map for selecting issue location"
            />
            <div className="absolute top-3 right-3 z-10 flex flex-col gap-2">
              <Button variant="ghost" size="sm" onClick={useCurrentLocation} className="shadow-lg">
                <MapPinIcon className="w-4 h-4 mr-1" />
                Use My Location
              </Button>
              <Button variant="ghost" size="sm" onClick={() => map?.locate({ setView: true, maxZoom: 16 })} className="shadow-lg">
                Center Map
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              {...register('address')}
              label="Address / Area"
              placeholder="e.g., Main Street, Near City Mall"
              error={errors.address?.message}
              disabled={isSubmitting}
            />
            <Input
              {...register('landmark')}
              label="Landmark (optional)"
              placeholder="e.g., Opposite Metro Station"
              error={errors.landmark?.message}
              disabled={isSubmitting}
            />
          </div>

          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 text-sm">
            <p className="font-medium text-gray-900 dark:text-white">Selected Coordinates:</p>
            <p className="font-mono text-civic-teal">
              {selectedCoords 
                ? `${selectedCoords.latitude.toFixed(6)}, ${selectedCoords.longitude.toFixed(6)}`
                : `${DEFAULT_CENTER.latitude.toFixed(6)}, ${DEFAULT_CENTER.longitude.toFixed(6)} (default)`
              }
            </p>
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="subsection-title flex items-center gap-2">
            <Camera className="w-5 h-5 text-civic-teal" />
            Photos (Optional but Recommended)
          </h2>
          <p className="text-gray-500 dark:text-gray-400 text-sm mb-4">Upload up to 5 photos (JPEG, PNG, WebP, HEIC - max 10MB each)</p>
          
          <div
            className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center hover:border-civic-teal transition-colors"
            onDragOver={(e) => { e.preventDefault(); e.currentTarget.classList.add('border-civic-teal'); }}
            onDragLeave={(e) => { e.currentTarget.classList.remove('border-civic-teal'); }}
            onDrop={(e) => { e.preventDefault(); e.currentTarget.classList.remove('border-civic-teal'); handleFileUpload(e.dataTransfer.files); }}
          >
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp,image/heic"
              multiple
              onChange={(e) => e.target.files && handleFileUpload(e.target.files)}
              className="hidden"
              id="file-upload"
              disabled={isSubmitting || uploadedMedia.length >= 5}
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <Camera className="w-12 h-12 mx-auto text-gray-400 mb-3" />
              <p className="text-gray-600 dark:text-gray-400 mb-1">Click or drag photos here</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">Maximum 5 files, 10MB each</p>
            </label>
          </div>

          {uploadedMedia.length > 0 && (
            <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
              {uploadedMedia.map((media) => (
                <div key={media.id} className="relative aspect-square rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
                  <img src={media.preview} alt="Upload preview" className="w-full h-full object-cover" />
                  <button
                    type="button"
                    onClick={() => removeMedia(media.id)}
                    className="absolute top-1 right-1 w-6 h-6 rounded-full bg-red-500 text-white flex items-center justify-center hover:bg-red-600 transition-colors"
                    aria-label="Remove photo"
                  >
                    <X className="w-4 h-4" />
                  </button>
                  <div className="absolute bottom-0 left-0 right-0 bg-black/50 text-white text-xs p-1 truncate">
                    {formatFileSize(media.file.size)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card className="p-6">
          <h2 className="subsection-title">Issue Details</h2>
          
          <div className="space-y-4">
            <Input
              {...register('title')}
              label="Title (Optional)"
              placeholder="Brief summary of the issue"
              error={errors.title?.message}
              disabled={isSubmitting}
            />

            <Textarea
              {...register('description')}
              label="Description *"
              placeholder="Describe the issue in detail: what you see, when you noticed it, any safety concerns, etc."
              error={errors.description?.message}
              maxLength={5000}
              disabled={isSubmitting}
            />

            <Select
              {...register('category')}
              label="Category *"
              options={categoryOptions}
              placeholder="Select issue category"
              error={errors.category?.message}
              disabled={isSubmitting}
            />

            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="anonymous"
                {...register('is_anonymous')}
                className="w-4 h-4 rounded border-gray-300 dark:border-gray-600 text-civic-teal focus:ring-civic-teal"
              />
              <label htmlFor="anonymous" className="text-sm text-gray-700 dark:text-gray-300">
                Submit anonymously (your identity will not be shown publicly)
              </label>
            </div>
          </div>
        </Card>

        <div className="flex gap-4">
          <Button type="submit" className="flex-1" isLoading={isSubmitting}>
            {isSubmitting && <Loader2 className="w-5 h-5 mr-2" />}
            Submit Report
          </Button>
          <Button type="button" variant="secondary" onClick={() => navigate('/dashboard')}>
            Cancel
          </Button>
        </div>
      </form>

      <div className="mt-8 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <h3 className="font-medium text-gray-900 dark:text-white mb-2">What happens next?</h3>
        <ol className="space-y-2 text-sm text-gray-600 dark:text-gray-400 list-decimal list-inside">
          <li>Your report is submitted and gets a unique tracking ID (e.g., CP12345678)</li>
          <li>AI analyzes your photos and description to categorize the issue</li>
          <li>System checks for duplicate reports in the same area</li>
          <li>Priority score is calculated based on severity, risk, and community impact</li>
          <li>Report is routed to the appropriate municipal department</li>
          <li>You'll receive updates as the status changes</li>
        </ol>
      </div>
    </div>
  );
}