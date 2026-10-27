import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { getAuthToken, clearAuth } from '../hooks/useAuth';
import type { 
  User, 
  Coordinates, 
  ReportStatus, 
  Assignment, 
  ReportEvent, 
  ReportComment, 
  DuplicateCandidate, 
  ResolutionEvidence, 
  MediaUploadResponse, 
  AnalyticsOverview, 
  CategoryDistribution, 
  DepartmentWorkload, 
  HotspotData, 
  TimeSeriesData, 
  Category, 
  Department, 
  ServiceZone, 
  HealthCheck,
  PaginatedResponse,
  Report,
  ReportListItem,
  IssueCategory
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAuthToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      clearAuth();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  register: (data: { email: string; password: string; full_name?: string; phone?: string }) =>
    api.post('/auth/register', data),
  refresh: (refresh_token: string) =>
    api.post('/auth/refresh', { refresh_token }),
  me: () => api.get('/auth/me'),
  updateProfile: (data: Partial<User>) => api.patch('/auth/me', data),
  logout: () => api.post('/auth/logout'),
};

export const reportsApi = {
  list: (params?: {
    page?: number;
    page_size?: number;
    status?: string[];
    category?: string[];
    department_id?: string;
    priority_band?: string[];
    date_from?: string;
    date_to?: string;
    lat?: number;
    lng?: number;
    radius?: number;
    sort_by?: string;
    sort_order?: string;
  }) => api.get<PaginatedResponse<ReportListItem>>('/reports', { params }),

  get: (id: string) => api.get<Report>(`/reports/${id}`),

  create: (data: {
    title?: string;
    description: string;
    category: IssueCategory;
    coordinates: Coordinates;
    address?: string;
    landmark?: string;
    is_anonymous?: boolean;
    media_ids?: string[];
  }) => api.post<Report>('/reports', data),

  update: (id: string, data: Partial<Report>) => api.patch<Report>(`/reports/${id}`, data),

  updateStatus: (id: string, status: ReportStatus, reason?: string) =>
    api.post<Report>(`/reports/${id}/status`, { status, reason }),

  assign: (id: string, data: {
    department_id: string;
    worker_id?: string;
    instructions?: string;
    sla_deadline?: string;
  }) => api.post<Assignment>(`/reports/${id}/assign`, data),

  getTimeline: (id: string) => api.get<ReportEvent[]>(`/reports/${id}/timeline`),

  getComments: (id: string) => api.get<ReportComment[]>(`/reports/${id}/comments`),

  addComment: (id: string, content: string, is_internal?: boolean) =>
    api.post<ReportComment>(`/reports/${id}/comments`, { content, is_internal }),

  getDuplicates: (id: string) => api.get<DuplicateCandidate[]>(`/reports/${id}/duplicates`),

  reviewDuplicate: (id: string, candidateId: string, action: 'confirm' | 'reject' | 'unlink', reason?: string) =>
    api.post<DuplicateCandidate>(`/reports/${id}/duplicates/${candidateId}/review`, { action, reason }),

  submitResolution: (id: string, data: {
    assignment_id?: string;
    before_media?: Array<Record<string, any>>;
    after_media?: Array<Record<string, any>>;
    work_notes?: string;
  }) => api.post<ResolutionEvidence>(`/reports/${id}/resolution`, data),

  reviewResolution: (id: string, action: 'approve' | 'reject' | 'needs_rework', notes?: string) =>
    api.post<ResolutionEvidence>(`/reports/${id}/resolution/review`, { action, notes }),

  getAnalysis: (id: string) => api.get(`/reports/${id}/analysis`),
};

export const mediaApi = {
  upload: (file: File, reportId?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (reportId) formData.append('report_id', reportId);
    return api.post<MediaUploadResponse>('/media/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  get: (id: string) => api.get(`/media/${id}`),
};

export const analyticsApi = {
  overview: (date_from?: string, date_to?: string) =>
    api.get<AnalyticsOverview>('/analytics/overview', { params: { date_from, date_to } }),

  categories: (date_from?: string, date_to?: string) =>
    api.get<CategoryDistribution[]>('/analytics/categories', { params: { date_from, date_to } }),

  departments: () => api.get<DepartmentWorkload[]>('/analytics/departments'),

  hotspots: (radius?: number, min_count?: number, date_from?: string) =>
    api.get<HotspotData[]>('/analytics/hotspots', { params: { radius, min_count, date_from } }),

  trends: (granularity?: 'day' | 'week' | 'month', days?: number, category?: string) =>
    api.get<TimeSeriesData>('/analytics/trends', { params: { granularity, days, category } }),

  priorityDistribution: () => api.get<Record<string, number>>('/analytics/priority-distribution'),

  duplicateRate: () => api.get('/analytics/duplicate-rate'),
};

export const adminApi = {
  listCategories: (active_only?: boolean) =>
    api.get<Category[]>('/admin/categories', { params: { active_only } }),

  createCategory: (data: Omit<Category, 'id' | 'created_at' | 'updated_at'>) =>
    api.post<Category>('/admin/categories', data),

  updateCategory: (id: string, data: Partial<Category>) =>
    api.patch<Category>(`/admin/categories/${id}`, data),

  listDepartments: (active_only?: boolean) =>
    api.get<Department[]>('/admin/departments', { params: { active_only } }),

  createDepartment: (data: Omit<Department, 'id' | 'created_at' | 'updated_at'>) =>
    api.post<Department>('/admin/departments', data),

  updateDepartment: (id: string, data: Partial<Department>) =>
    api.patch<Department>(`/admin/departments/${id}`, data),

  listServiceZones: (active_only?: boolean) =>
    api.get<ServiceZone[]>('/admin/service-zones', { params: { active_only } }),

  createServiceZone: (data: Omit<ServiceZone, 'id' | 'created_at' | 'updated_at'>) =>
    api.post<ServiceZone>('/admin/service-zones', data),

  listRoutingRules: (category_id?: string) =>
    api.get('/admin/routing-rules', { params: { category_id } }),

  createRoutingRule: (data: {
    category_id: string;
    department_id: string;
    service_zone_id?: string;
    priority_band?: string;
    is_default?: boolean;
  }) => api.post('/admin/routing-rules', data),

  listScoringRules: () => api.get('/admin/scoring-rules'),

  createScoringRule: (data: {
    version: string;
    severity_weight?: number;
    risk_weight?: number;
    time_weight?: number;
    corroboration_weight?: number;
    safety_escalation_threshold?: number;
    description?: string;
  }) => api.post('/admin/scoring-rules', data),

  getAuditLogs: (params?: {
    page?: number;
    page_size?: number;
    actor_id?: string;
    resource_type?: string;
    action?: string;
    date_from?: string;
    date_to?: string;
  }) => api.get('/admin/audit-logs', { params }),

  listUsers: (role?: string, page?: number, page_size?: number) =>
    api.get<User[]>('/admin/users', { params: { role, page, page_size } }),
};

export const notificationsApi = {
  list: (unread_only?: boolean, limit?: number) =>
    api.get<Notification[]>('/notifications', { params: { unread_only, limit } }),

  unreadCount: () => api.get<{ count: number }>('/notifications/unread-count'),

  markRead: (id: string) => api.post(`/notifications/${id}/read`),

  markAllRead: () => api.post('/notifications/read-all'),
};

export const healthApi = {
  check: () => api.get<HealthCheck>('/health'),
  db: () => api.get('/health/db'),
  agents: () => api.get('/health/agents'),
  ready: () => api.get('/health/ready'),
};

export default api;