import { useState, useCallback, useEffect, useRef } from 'react';
import { Coordinates } from '../types';

export function useMap(initialCenter?: Coordinates, initialZoom = 13) {
  const [center, setCenter] = useState<Coordinates>(initialCenter || { latitude: 12.9716, longitude: 77.5946 });
  const [zoom, setZoom] = useState(initialZoom);
  const [markerPosition, setMarkerPosition] = useState<Coordinates | null>(initialCenter || null);
  const [isLocating, setIsLocating] = useState(false);
  const mapRef = useRef<L.Map | null>(null);

  const locateUser = useCallback(async () => {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser');
      return;
    }

    setIsLocating(true);
    try {
      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0,
        });
      });

      const coords: Coordinates = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
      };
      setCenter(coords);
      setMarkerPosition(coords);
      setZoom(16);
    } catch (error) {
      console.error('Geolocation error:', error);
      alert('Unable to retrieve your location. Please enable location permissions or select manually.');
    } finally {
      setIsLocating(false);
    }
  }, []);

  const setMapRef = useCallback((map: L.Map | null) => {
    mapRef.current = map;
  }, []);

  const flyTo = useCallback((coordinates: Coordinates, zoomLevel = 16) => {
    if (mapRef.current) {
      mapRef.current.flyTo([coordinates.latitude, coordinates.longitude], zoomLevel);
    }
    setCenter(coordinates);
    setZoom(zoomLevel);
  }, []);

  return {
    center,
    setCenter,
    zoom,
    setZoom,
    markerPosition,
    setMarkerPosition,
    isLocating,
    locateUser,
    setMapRef,
    flyTo,
    mapInstance: mapRef.current,
  };
}

export function useGeolocation() {
  const [position, setPosition] = useState<Coordinates | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const requestLocation = useCallback(async () => {
    if (!navigator.geolocation) {
      setError('Geolocation is not supported');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const pos = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0,
        });
      });

      setPosition({
        latitude: pos.coords.latitude,
        longitude: pos.coords.longitude,
      });
    } catch (err) {
      setError(err instanceof GeolocationPositionError 
        ? (err.code === err.PERMISSION_DENIED ? 'Location permission denied' : 'Unable to get location')
        : 'Location error');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    requestLocation();
  }, [requestLocation]);

  return { position, error, isLoading, requestLocation };
}