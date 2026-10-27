import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { reportsApi } from '../services/api';
import { Report, ReportStatus, ReportEvent, ReportComment, IssueCategory, PriorityBand, UserRole } from '../types';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Textarea } from '../components/ui/Textarea';
import { Select } from '../components/ui/Select';
import { Modal } from '../components/ui/Modal';
import { Alert } from '../components/ui/Alert';
import { Spinner } from '../components/ui/Spinner';
import { MapPin, Clock, Camera, MessageSquare, AlertCircle, CheckCircle, MoreVertical, Edit, Trash2, Loader2, ArrowLeft } from 'lucide-react';
import { formatRelativeTime, formatDateTime, getStatusLabel, getCategoryLabel, getCategoryIcon, cn } from '../utils/helpers';

const statusTransitions: Record<ReportStatus, ReportStatus[]> = {
  reported: ['under_review', 'rejected'],
  under_review: ['verified', 'needs_more_info', 'rejected'],
  needs_more_info: ['under_review', 'rejected'],
  verified: ['assigned'],
  assigned: ['in_progress'],
  in_progress: ['resolved_pending_confirmation'],
  resolved_pending_confirmation: ['closed', 'reopened'],
  closed: ['reopened'],
  reopened: ['under_review'],
  rejected: [],
};



function ReportMedia({ media }: { media: Report['media'] }) {
  if (media.length === 0) return null;
  
  return (
    <div>
      <h3 className="font-medium text-gray-900 dark:text-white mb-3 flex items-center gap-2">
        <Camera className="w-5 h-5 text-civic-teal" />
        Photos
      </h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
        {media.map((mediaItem) => (
          <div key={mediaItem.id} className="relative aspect-square rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
            <img
              src={mediaItem.storage_path.startsWith('http') ? mediaItem.storage_path : `/api/v1/media/${mediaItem.id}`}
              alt={`Report photo ${mediaItem.sort_order + 1}`}
              className="w-full h-full object-cover"
              loading="lazy"
            />
            {mediaItem.is_primary && (
              <div className="absolute top-1 left-1 bg-civic-teal text-white text-xs px-1.5 py-0.5 rounded">Primary</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function ReportDetails({ report }: { report: Report }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="label">Category</label>
          <div className="flex items-center gap-2">
            <span className="text-2xl">{getCategoryIcon(report.category)}</span>
            <span className="font-medium text-gray-900 dark:text-white">{getCategoryLabel(report.category)}</span>
          </div>
        </div>
        <div>
          <label className="label">Priority Score</label>
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold text-gray-900 dark:text-white">{report.priority_score}</span>
            <Badge variant="priority" priority={report.priority_band}>{report.priority_band.replace('_', ' ')}</Badge>
          </div>
        </div>
      </div>

      <div>
        <label className="label flex items-center gap-1">
          <MapPin className="w-4 h-4" />
          Location
        </label>
        <p className="text-gray-700 dark:text-gray-300 font-mono text-sm">
          {report.coordinates.latitude.toFixed(6)}, {report.coordinates.longitude.toFixed(6)}
        </p>
        {report.address && <p className="text-gray-600 dark:text-gray-400 mt-1">{report.address}</p>}
        {report.landmark && <p className="text-gray-500 dark:text-gray-400 text-sm">{report.landmark}</p>}
      </div>

      <div className="pt-4 border-t border-gray-100 dark:border-gray-700">
        <label className="label">Description</label>
        <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{report.description}</p>
      </div>

      {report.assigned_department && (
        <div className="pt-4 border-t border-gray-100 dark:border-gray-700">
          <label className="label flex items-center gap-1">
            <MapPin className="w-4 h-4" />
            Assigned Department
          </label>
          <p className="font-medium text-gray-900 dark:text-white">{report.assigned_department.name}</p>
          {report.assigned_department.contact_email && (
            <p className="text-sm text-gray-500 dark:text-gray-400">{report.assigned_department.contact_email}</p>
          )}
        </div>
      )}

      {report.resolution_evidence && report.resolution_evidence.length > 0 && (
        <div className="pt-4 border-t border-gray-100 dark:border-gray-700">
          <label className="label flex items-center gap-1">
            <CheckCircle className="w-4 h-4" />
            Resolution Evidence
          </label>
          {report.resolution_evidence.map((evidence, idx) => (
            <Card key={evidence.id} className="mt-2 p-4" variant="hover">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium">Submitted by {evidence.submitted_by?.full_name || 'Field Worker'}</span>
                <Badge variant={evidence.status === 'approved' ? 'green' : evidence.status === 'rejected' ? 'red' : 'amber'}>
                  {evidence.status.replace('_', ' ')}
                </Badge>
              </div>
              {evidence.work_notes && <p className="text-gray-700 dark:text-gray-300 mb-2">{evidence.work_notes}</p>}
              {evidence.after_media && evidence.after_media.length > 0 && (
                <div className="grid grid-cols-2 gap-2">
                  {evidence.after_media.map((media: any, i: number) => (
                    <img key={i} src={media.url} alt="After photo" className="rounded-lg h-32 w-full object-cover" />
                  ))}
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

function ReportTimeline({ 
  timeline, 
  comments, 
  sortedTimelineItems, 
  isStaff, 
  user, 
  report, 
  onAddComment 
}: {
  timeline: ReportEvent[];
  comments: ReportComment[];
  sortedTimelineItems: (ReportEvent | ReportComment)[];
  isStaff: boolean;
  user: any;
  report: Report;
  onAddComment: () => void;
}) {
  return (
    <Card>
      <div className="p-6 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
        <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-civic-teal" />
          Timeline & Comments
        </h3>
        {(isStaff || user?.id === report.reporter_id) && (
          <Button variant="secondary" size="sm" onClick={onAddComment}>
            Add Comment
          </Button>
        )}
      </div>
      <div className="p-6">
        <div className="space-y-4">
          {sortedTimelineItems.map((item, idx) => (
            <TimelineItem item={item} idx={idx} total={sortedTimelineItems.length} />
          ))}
          {timeline.length === 0 && comments.length === 0 && (
            <p className="text-center text-gray-500 dark:text-gray-400 py-8">No timeline events or comments yet</p>
          )}
        </div>
      </div>
    </Card>
  );
}

function ReportInfo({ report, formatDateTime }: { report: Report; formatDateTime: (date: string) => string }) {
  return (
    <Card>
      <div className="p-6 border-b border-gray-100 dark:border-gray-700">
        <h3 className="font-semibold text-gray-900 dark:text-white">Report Info</h3>
      </div>
      <div className="p-6 space-y-4">
        <div>
          <label className="label text-xs text-gray-500">Submitted</label>
          <p className="font-medium">{formatDateTime(report.created_at)}</p>
        </div>
        {report.verified_at && (
          <div>
            <label className="label text-xs text-gray-500">Verified</label>
            <p className="font-medium">{formatDateTime(report.verified_at)}</p>
          </div>
        )}
        {report.assigned_at && (
          <div>
            <label className="label text-xs text-gray-500">Assigned</label>
            <p className="font-medium">{formatDateTime(report.assigned_at)}</p>
          </div>
        )}
        {report.resolved_at && (
          <div>
            <label className="label text-xs text-gray-500">Resolved</label>
            <p className="font-medium">{formatDateTime(report.resolved_at)}</p>
          </div>
        )}
        {report.closed_at && (
          <div>
            <label className="label text-xs text-gray-500">Closed</label>
            <p className="font-medium">{formatDateTime(report.closed_at)}</p>
          </div>
        )}
        <div className="pt-4 border-t border-gray-100 dark:border-gray-700">
          <label className="label text-xs text-gray-500">Reporter</label>
          <p className="font-medium">{report.is_anonymous ? 'Anonymous' : (report.reporter?.full_name || 'Citizen')}</p>
        </div>
      </div>
    </Card>
  );
}

function ReportActions({ report, isStaff, navigate, id }: { report: Report; isStaff: boolean; navigate: any; id: string }) {
  if (!isStaff) return null;
  
  return (
    <Card>
      <div className="p-6 border-b border-gray-100 dark:border-gray-700">
        <h3 className="font-semibold text-gray-900 dark:text-white">Admin Actions</h3>
      </div>
      <div className="p-6 space-y-3">
        <Button variant="secondary" className="w-full justify-start" onClick={() => navigate(`/admin/reports/${id}`)}>
          View in Admin Panel
        </Button>
        <Button variant="secondary" className="w-full justify-start" onClick={() => navigate(`/reports/${id}/analysis`)}>
          View AI Analysis
        </Button>
      </div>
    </Card>
  );
}

function StatusModal({ isOpen, onClose, availableTransitions, onStatusChange }: {
  isOpen: boolean;
  onClose: () => void;
  availableTransitions: ReportStatus[];
  onStatusChange: (status: ReportStatus) => void;
}) {
  if (!isOpen) return null;
  
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Update Status">
      <div className="space-y-4">
        <p className="text-gray-600 dark:text-gray-400">Select the new status for this report:</p>
        <div className="space-y-2 max-h-60 overflow-y-auto">
          {availableTransitions.map((status) => (
            <button
              key={status}
              onClick={() => onStatusChange(status)}
              className="w-full text-left p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="capitalize">{status.replace('_', ' ')}</span>
                <Badge variant="status" status={status} className="text-xs">{status.replace('_', ' ')}</Badge>
              </div>
            </button>
          ))}
        </div>
      </div>
    </Modal>
  );
}

function CommentModal({ isOpen, onClose, newComment, onCommentChange, onSubmit, isSubmitting }: {
  isOpen: boolean;
  onClose: () => void;
  newComment: string;
  onCommentChange: (value: string) => void;
  onSubmit: () => void;
  isSubmitting: boolean;
}) {
  if (!isOpen) return null;
  
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Add Comment">
      <div className="space-y-4">
        <Textarea
          value={newComment}
          onChange={(e) => onCommentChange(e.target.value)}
          placeholder="Write your comment..."
          maxLength={2000}
          rows={4}
        />
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button onClick={onSubmit} disabled={isSubmitting || !newComment.trim()}>
            {isSubmitting ? 'Posting...' : 'Post Comment'}
          </Button>
        </div>
      </div>
    </Modal>
  );
}

function TimelineItem({ item, idx, total }: { item: ReportEvent | ReportComment; idx: number; total: number }) {
  const isEvent = 'event_type' in item;
  
  return (
    <div key={`${item.id}-${idx}`} className="flex gap-3">
      <div className="relative">
        <div className="w-2 h-2 rounded-full bg-civic-teal mt-2 flex-shrink-0" />
        {idx < total - 1 && (
          <div className="absolute left-1 top-4 bottom-0 w-0.5 border-l border-gray-200 dark:border-gray-700" />
        )}
      </div>
      <div className="flex-1 min-w-0 pb-4">
        {isEvent ? (
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
            <div className="flex items-center gap-2 text-sm mb-1">
              <span className="font-medium text-gray-900 dark:text-white capitalize">{item.event_type.replace('_', ' ')}</span>
              <span className="text-gray-500 dark:text-gray-400">{formatRelativeTime(item.created_at)}</span>
              {item.actor_id && (
                <>
                  <span className="text-gray-400 dark:text-gray-500">by</span>
                  <span className="font-medium">{item.actor_role}</span>
                </>
              )}
            </div>
            {item.reason && <p className="text-gray-600 dark:text-gray-400 text-sm">{item.reason}</p>}
            {item.previous_status && item.new_status && (
              <div className="flex items-center gap-2 mt-2">
                <Badge variant="status" status={item.previous_status} className="text-xs">{item.previous_status.replace('_', ' ')}</Badge>
                <span className="text-gray-400 dark:text-gray-500">→</span>
                <Badge variant="status" status={item.new_status} className="text-xs">{item.new_status.replace('_', ' ')}</Badge>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-civic-navy/5 rounded-lg p-3">
            <div className="flex items-center gap-2 text-sm mb-1">
              <span className="font-medium text-civic-navy">{item.author_name || 'Unknown'}</span>
              <Badge variant="primary" className="text-xs capitalize">{item.author_role}</Badge>
              <span className="text-gray-500 dark:text-gray-400">{formatRelativeTime(item.created_at)}</span>
            </div>
            <p className="text-gray-700 dark:text-gray-300">{item.content}</p>
            {item.is_internal && <span className="text-xs text-civic-amber">Internal comment</span>}
          </div>
        )}
      </div>
    </div>
  );
}

export function ReportDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, hasRole } = useAuth();
  const [report, setReport] = useState<Report | null>(null);
  const [timeline, setTimeline] = useState<ReportEvent[]>([]);
  const [comments, setComments] = useState<ReportComment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [showCommentModal, setShowCommentModal] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [duplicateWarning, setDuplicateWarning] = useState<{ count: number } | null>(null);

  useEffect(() => {
    if (id) fetchReport();
  }, [id]);

  const fetchReport = useCallback(async () => {
    try {
      setIsLoading(true);
      const [reportRes, timelineRes, commentsRes, duplicatesRes] = await Promise.all([
        reportsApi.get(id!),
        reportsApi.getTimeline(id!),
        reportsApi.getComments(id!),
        reportsApi.getDuplicates(id!),
      ]);
      setReport(reportRes.data);
      setTimeline(timelineRes.data);
      setComments(commentsRes.data);
      if (duplicatesRes.data.length > 0) {
        setDuplicateWarning({ count: duplicatesRes.data.length });
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load report');
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  const handleStatusChange = useCallback(async (newStatus: ReportStatus, reason?: string) => {
    if (!report) return;
    setIsSubmitting(true);
    try {
      await reportsApi.updateStatus(id!, newStatus, reason);
      fetchReport();
      setShowStatusModal(false);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to update status');
    } finally {
      setIsSubmitting(false);
    }
  }, [report, id, fetchReport]);

  const handleAddComment = useCallback(async () => {
    if (!newComment.trim()) return;
    setIsSubmitting(true);
    try {
      await reportsApi.addComment(id!, newComment, hasRole(['admin', 'field_worker', 'supervisor']));
      fetchReport();
      setNewComment('');
      setShowCommentModal(false);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to add comment');
    } finally {
      setIsSubmitting(false);
    }
  }, [id, newComment, hasRole, fetchReport]);

  const isStaff = hasRole(['admin', 'field_worker', 'supervisor']);
  const isAssignedWorker = user && report?.assignee_id === user.id;
  const canUpdateStatus = isStaff || (isAssignedWorker && report?.status === 'in_progress');
  const availableTransitions = canUpdateStatus ? statusTransitions[report?.status || 'reported'] : [];

  const sortedTimelineItems = useMemo(() => {
    return [...timeline, ...comments].sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
  }, [timeline, comments]);

  if (isLoading) {
    return <Spinner className="mx-auto my-20" size="lg" />;
  }

  if (error && !report) {
    return (
      <div className="page-container text-center py-20">
        <AlertCircle className="w-16 h-16 text-civic-red mx-auto mb-4" />
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Unable to load report</h2>
        <p className="text-gray-600 dark:text-gray-400 mb-6">{error}</p>
        <Button variant="secondary" onClick={() => navigate('/dashboard')}>
          <ArrowLeft className="w-5 h-5 mr-2" />
          Back to Dashboard
        </Button>
      </div>
    );
  }

  if (!report) return null;

  return (
    <div className="page-container">
      <div className="mb-6 flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
          <ArrowLeft className="w-5 h-5 mr-1" />
          Back
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{report.title || getCategoryLabel(report.category)}</h1>
          <p className="text-gray-600 dark:text-gray-400">{report.tracking_id} • {getCategoryLabel(report.category)}</p>
        </div>
      </div>

      {error && <Alert variant="error" className="mb-6" onDismiss={() => setError('')}>{error}</Alert>}

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <div className="p-6 border-b border-gray-100 dark:border-gray-700 flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-3 flex-wrap">
                <Badge variant="primary">{report.tracking_id}</Badge>
                <Badge variant="status" status={report.status}>{getStatusLabel(report.status)}</Badge>
                <Badge variant="priority" priority={report.priority_band}>{report.priority_band.replace('_', ' ')}</Badge>
                {report.category_confidence && (
                  <Badge variant="teal">AI: {Math.round(report.category_confidence * 100)}%</Badge>
                )}
              </div>
              {canUpdateStatus && availableTransitions.length > 0 && (
                <Button variant="secondary" size="sm" onClick={() => setShowStatusModal(true)}>
                  Update Status
                </Button>
              )}
            </div>

            <ReportMedia media={report.media} />
            <ReportDetails report={report} />
          </Card>

          <ReportTimeline
            timeline={timeline}
            comments={comments}
            sortedTimelineItems={sortedTimelineItems}
            isStaff={isStaff}
            user={user}
            report={report}
            onAddComment={() => setShowCommentModal(true)}
          />
        </div>

        <div className="lg:col-span-1 space-y-6">
          <ReportInfo report={report} formatDateTime={formatDateTime} />
          
          {duplicateWarning && (
            <Card className="border-civic-amber">
              <div className="p-4 bg-civic-amber/5 border-b border-civic-amber/20">
                <h3 className="font-semibold text-civic-amber flex items-center gap-2">
                  <AlertCircle className="w-5 h-5" />
                  Potential Duplicates
                </h3>
              </div>
              <div className="p-4">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  {duplicateWarning.count} potential duplicate report{duplicateWarning.count > 1 ? 's' : ''} found nearby.
                </p>
                <Button variant="secondary" size="sm" onClick={() => navigate(`/reports/${id}/duplicates`)}>
                  View Duplicates
                </Button>
              </div>
            </Card>
          )}

          <ReportActions report={report} isStaff={isStaff} navigate={navigate} id={id!} />
        </div>
      </div>

      <StatusModal
        isOpen={showStatusModal}
        onClose={() => setShowStatusModal(false)}
        availableTransitions={availableTransitions}
        onStatusChange={handleStatusChange}
      />

      <CommentModal
        isOpen={showCommentModal}
        onClose={() => setShowCommentModal(false)}
        newComment={newComment}
        onCommentChange={setNewComment}
        onSubmit={handleAddComment}
        isSubmitting={isSubmitting}
      />
    </div>
  );
}