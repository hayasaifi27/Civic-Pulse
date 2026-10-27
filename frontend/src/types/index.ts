export type UserRole = 'citizen' | 'admin' | 'field_worker' | 'supervisor';

export type ReportStatus = 
  | 'reported' 
  | 'under_review' 
  | 'needs_more_info' 
  | 'verified' 
  | 'assigned' 
  | 'in_progress' 
  | 'resolved_pending_confirmation' 
  | 'closed' 
  | 'rejected' 
  | 'reopened';

export type PriorityBand = 'low' | 'medium' | 'high' | 'critical' | 'safety_escalation';

export type IssueCategory = 
  | 'pothole' 
  | 'garbage' 
  | 'streetlight' 
  | 'water_leakage' 
  | 'drainage' 
  | 'footpath' 
  | 'obstruction' 
  | 'property_damage' 
  | 'sanitation' 
  | 'other';

export type DuplicateStatus = 'pending' | 'confirmed' | 'rejected' | 'unlinked';

export type AssignmentStatus = 'pending' | 'accepted' | 'in_progress' | 'completed' | 'rejected';

export type ResolutionStatus = 'submitted' | 'approved' | 'rejected' | 'needs_rework';

export type NotificationChannel = 'in_app' | 'email' | 'sms' | 'push';

export interface Coordinates {
  latitude: number;
  longitude: number;
}

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  phone: string | null;
  avatar_url: string | null;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  department_id: string | null;
  service_zone_id: string | null;
  preferences: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Category {
  id: string;
  code: string;
  name: string;
  description: string | null;
  icon: string | null;
  color: string | null;
  severity_base: number;
  risk_base: number;
  department_id: string | null;
  sla_hours: number;
  duplicate_distance_meters: number;
  is_active: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface Department {
  id: string;
  name: string;
  code: string;
  description: string | null;
  contact_email: string | null;
  contact_phone: string | null;
  is_active: boolean;
  sla_hours: number;
  created_at: string;
  updated_at: string;
}

export interface ServiceZone {
  id: string;
  name: string;
  code: string;
  boundary: GeoJSON.Polygon;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ReportMedia {
  id: string;
  storage_path: string;
  file_name: string;
  mime_type: string;
  file_size: number;
  width: number | null;
  height: number | null;
  is_primary: boolean;
  sort_order: number;
  analysis_result: Record<string, any> | null;
  created_at: string;
}

export interface Report {
  id: string;
  tracking_id: string;
  title: string | null;
  description: string;
  category: IssueCategory;
  category_confidence: number | null;
  category_source: string | null;
  coordinates: Coordinates;
  address: string | null;
  landmark: string | null;
  status: ReportStatus;
  priority_score: number;
  priority_band: PriorityBand;
  priority_version: string | null;
  assigned_department_id: string | null;
  reporter_id: string | null;
  assignee_id: string | null;
  is_anonymous: boolean;
  is_public: boolean;
  duplicate_primary_id: string | null;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  verified_at: string | null;
  assigned_at: string | null;
  resolved_at: string | null;
  closed_at: string | null;
  media: ReportMedia[];
  assigned_department: Department | null;
  reporter: User | null;
  assignee: User | null;
  resolution_evidence: ResolutionEvidence[];
}

export interface ReportListItem {
  id: string;
  tracking_id: string;
  title: string | null;
  description: string;
  category: IssueCategory;
  coordinates: Coordinates;
  address: string | null;
  status: ReportStatus;
  priority_score: number;
  priority_band: PriorityBand;
  created_at: string;
  updated_at: string;
  media_count: number;
  primary_media: ReportMedia | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface MediaUploadResponse {
  id: string;
  storage_path: string;
  file_name: string;
  mime_type: string;
  file_size: number;
  width: number | null;
  height: number | null;
  upload_url: string | null;
}

export interface ReportEvent {
  id: string;
  event_type: string;
  previous_status: ReportStatus | null;
  new_status: ReportStatus | null;
  actor_id: string | null;
  actor_role: UserRole | null;
  reason: string | null;
  metadata: Record<string, any>;
  created_at: string;
}

export interface ReportComment {
  id: string;
  report_id: string;
  author_id: string;
  author_name: string | null;
  author_role: UserRole;
  content: string;
  is_internal: boolean;
  created_at: string;
  updated_at: string;
}

export interface DuplicateCandidate {
  id: string;
  report_id: string;
  candidate_report_id: string;
  candidate_tracking_id: string;
  candidate_title: string | null;
  candidate_category: IssueCategory;
  candidate_coordinates: Coordinates;
  candidate_status: ReportStatus;
  distance_meters: number | null;
  category_match: boolean;
  description_similarity: number | null;
  image_similarity: number | null;
  time_proximity_hours: number | null;
  match_score: number;
  match_explanation: string;
  suggested_action: string;
  status: DuplicateStatus;
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_reason: string | null;
  created_at: string;
}

export interface Assignment {
  id: string;
  report_id: string;
  department_id: string;
  worker_id: string | null;
  assigned_by: string | null;
  status: AssignmentStatus;
  priority: number;
  instructions: string | null;
  sla_deadline: string | null;
  accepted_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  department: Department | null;
  worker: User | null;
}

export interface ResolutionEvidence {
  id: string;
  report_id: string;
  assignment_id: string | null;
  submitted_by_id: string;
  before_media: Array<Record<string, any>> | null;
  after_media: Array<Record<string, any>> | null;
  work_notes: string | null;
  status: ResolutionStatus;
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_notes: string | null;
  created_at: string;
  updated_at: string;
  submitted_by: User | null;
}

export interface PriorityAssessment {
  id: string;
  report_id: string;
  severity_score: number;
  risk_score: number;
  time_score: number;
  corroboration_score: number;
  total_score: number;
  priority_band: PriorityBand;
  rule_version: string;
  factor_details: Record<string, any>;
  escalation_recommended: boolean;
  escalation_reason: string | null;
  assessed_by: string;
  created_at: string;
}

export interface Notification {
  id: string;
  report_id: string | null;
  channel: NotificationChannel;
  event_type: string;
  title: string;
  message: string;
  data: Record<string, any>;
  is_read: boolean;
  read_at: string | null;
  sent_at: string | null;
  created_at: string;
}

export interface AnalyticsOverview {
  total_reports: number;
  reports_awaiting_review: number;
  active_assignments: number;
  overdue_issues: number;
  resolved_closed: number;
  median_time_to_acknowledgment_hours: number | null;
  median_time_to_resolution_hours: number | null;
  resolution_rate: number;
  reopened_rate: number;
}

export interface CategoryDistribution {
  category: IssueCategory;
  count: number;
  percentage: number;
}

export interface DepartmentWorkload {
  department_id: string;
  department_name: string;
  assigned: number;
  in_progress: number;
  completed: number;
  overdue: number;
  avg_resolution_hours: number | null;
}

export interface HotspotData {
  coordinates: Coordinates;
  count: number;
  categories: IssueCategory[];
  avg_priority: number;
  radius_meters: number;
}

export interface TimeSeriesPoint {
  date: string;
  count: number;
}

export interface TimeSeriesData {
  series: TimeSeriesPoint[];
  granularity: string;
}

export interface ClassificationResult {
  predicted_category: IssueCategory;
  confidence: number;
  alternatives: Array<{ category: IssueCategory; confidence: number }>;
  explanation: string;
  evidence_quality: 'good' | 'fair' | 'poor';
  needs_human_review: boolean;
  model_version: string;
  is_mock: boolean;
}

export interface VerificationResult {
  status: 'valid' | 'needs_info' | 'needs_review' | 'rejected';
  missing_fields: string[];
  evidence_quality: 'good' | 'fair' | 'poor';
  review_recommendation: string;
  issues: string[];
}

export interface PriorityScoreResult {
  priority_score: number;
  priority_band: PriorityBand;
  severity_score: number;
  risk_score: number;
  time_score: number;
  corroboration_score: number;
  factor_details: Record<string, any>;
  escalation_recommended: boolean;
  escalation_reason: string | null;
  rule_version: string;
}

export interface RoutingRecommendation {
  department_id: string;
  department_name: string;
  queue: string;
  reason: string;
  needs_manual_review: boolean;
}

export interface HealthCheck {
  status: string;
  version: string;
  database: string;
  agents: Record<string, string>;
  demo_mode: boolean;
}