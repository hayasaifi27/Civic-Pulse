import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(dateString: string | null | undefined, options?: Intl.DateTimeFormatOptions): string {
  if (!dateString) return 'N/A'
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      ...options,
    })
  } catch {
    return 'Invalid date'
  }
}

export function formatDateTime(dateString: string | null | undefined): string {
  if (!dateString) return 'N/A'
  try {
    const date = new Date(dateString)
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return 'Invalid date'
  }
}

export function formatRelativeTime(dateString: string | null | undefined): string {
  if (!dateString) return 'N/A'
  try {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return formatDate(dateString)
  } catch {
    return 'Invalid date'
  }
}

export function getStatusLabel(status: string): string {
  return status.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
}

export function getCategoryLabel(category: string): string {
  const labels: Record<string, string> = {
    pothole: 'Pothole / Road Damage',
    garbage: 'Garbage Accumulation',
    streetlight: 'Broken Streetlight',
    water_leakage: 'Water Leakage',
    drainage: 'Drainage Blockage',
    footpath: 'Damaged Footpath',
    obstruction: 'Unsafe Road Obstruction',
    property_damage: 'Public Property Damage',
    sanitation: 'Sanitation Concern',
    other: 'Other / Uncertain',
  }
  return labels[category] || category
}

export function getCategoryIcon(category: string): string {
  const icons: Record<string, string> = {
    pothole: '🕳️',
    garbage: '🗑️',
    streetlight: '💡',
    water_leakage: '💧',
    drainage: '🚰',
    footpath: '🚶',
    obstruction: '🚧',
    property_damage: '🔨',
    sanitation: '🚻',
    other: '❓',
  }
  return icons[category] || '📍'
}

export function getCategoryColor(category: string): string {
  const colors: Record<string, string> = {
    pothole: '#E74C3C',
    garbage: '#F39C12',
    streetlight: '#F1C40F',
    water_leakage: '#3498DB',
    drainage: '#2C3E50',
    footpath: '#95A5A6',
    obstruction: '#C0392B',
    property_damage: '#8E44AD',
    sanitation: '#27AE60',
    other: '#7F8C8D',
  }
  return colors[category] || '#7F8C8D'
}

export function getPriorityColor(band: string): string {
  const colors: Record<string, string> = {
    low: '#6B7280',
    medium: '#3B82F6',
    high: '#F59E0B',
    critical: '#F97316',
    safety_escalation: '#EF4444',
  }
  return colors[band] || '#6B7280'
}

export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength).trim() + '...'
}

export function generateTrackingId(): string {
  return 'CP' + Math.random().toString(36).substring(2, 10).toUpperCase()
}

export function validateCoordinates(lat: number, lng: number): boolean {
  return lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180
}

export function calculateDistance(
  lat1: number, lng1: number,
  lat2: number, lng2: number
): number {
  const R = 6371000
  const toRad = (deg: number) => deg * Math.PI / 180
  const dLat = toRad(lat2 - lat1)
  const dLng = toRad(lng2 - lng1)
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

export function debounce<T extends (...args: any[]) => any>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout>
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => fn(...args), delay)
  }
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export function isValidImageType(file: File): boolean {
  const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/heic']
  return allowedTypes.includes(file.type)
}

export function isValidFileSize(file: File, maxSize: number = 10 * 1024 * 1024): boolean {
  return file.size <= maxSize
}