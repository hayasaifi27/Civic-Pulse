import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { reportsApi } from '../services/api';
import { ReportListItem, ReportStatus, PriorityBand, IssueCategory } from '../types';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Spinner } from '../components/ui/Spinner';
import { Alert } from '../components/ui/Alert';
import { MapPin, Clock, AlertCircle, CheckCircle, Plus, Eye, MoreVertical } from 'lucide-react';
import { formatRelativeTime, getStatusLabel, getCategoryLabel, getCategoryIcon, cn } from '../utils/helpers';

const statusOrder: Record<ReportStatus, number> = {
  in_progress: 1,
  resolved_pending_confirmation: 2,
  assigned: 3,
  under_review: 4,
  needs_more_info: 5,
  reported: 6,
  verified: 7,
  reopened: 8,
  closed: 9,
  rejected: 10,
};

export function CitizenDashboard() {
  const { user, isLoading: authLoading } = useAuth();
  const [reports, setReports] = useState<ReportListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'active' | 'all'>('active');
  const navigate = useNavigate();

  useEffect(() => {
    if (user) {
      fetchReports();
    }
  }, [user]);

  const fetchReports = async () => {
    try {
      setIsLoading(true);
      const response = await reportsApi.list({ page_size: 50 });
      setReports(response.data.items);
    } catch (err) {
      setError('Failed to load reports');
    } finally {
      setIsLoading(false);
    }
  };

  const activeReports = reports.filter(r => 
    !['closed', 'rejected'].includes(r.status)
  ).sort((a, b) => statusOrder[a.status] - statusOrder[b.status]);

  const closedReports = reports.filter(r => 
    ['closed', 'rejected'].includes(r.status)
  ).sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());

  if (authLoading) {
    return <Spinner className="mx-auto" size="lg" />;
  }

  return (
    <div className="page-container">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="section-title">My Reports</h1>
          <p className="text-gray-600 dark:text-gray-400">Track and manage your civic issue reports</p>
        </div>
        <Link to="/submit">
          <Button>
            <Plus className="w-5 h-5 mr-2" />
            Submit New Report
          </Button>
        </Link>
      </div>

      {error && <Alert variant="error" className="mb-6">{error}</Alert>}

      <div className="mb-6 border-b border-gray-200 dark:border-gray-700">
        <nav className="flex gap-4" aria-label="Report tabs">
          <button
            onClick={() => setActiveTab('active')}
            className={cn(
              'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
              activeTab === 'active'
                ? 'border-civic-teal text-civic-teal'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
            )}
          >
            Active ({activeReports.length})
          </button>
          <button
            onClick={() => setActiveTab('all')}
            className={cn(
              'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
              activeTab === 'all'
                ? 'border-civic-teal text-civic-teal'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
            )}
          >
            All Reports ({reports.length})
          </button>
        </nav>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="card animate-pulse h-24" />
          ))}
        </div>
      ) : activeTab === 'active' && activeReports.length === 0 ? (
        <Card className="text-center py-12">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
            <MapPin className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No active reports</h3>
          <p className="text-gray-500 dark:text-gray-400 mb-6">You don't have any active civic issue reports at the moment.</p>
          <Link to="/submit">
            <Button>
              <Plus className="w-5 h-5 mr-2" />
              Submit Your First Report
            </Button>
          </Link>
        </Card>
      ) : (
        <div className="space-y-4">
          {(activeTab === 'active' ? activeReports : closedReports).map((report) => (
            <ReportCard key={report.id} report={report} onClick={() => navigate(`/reports/${report.id}`)} />
          ))}
        </div>
      )}
    </div>
  );
}

function ReportCard({ report, onClick }: { report: ReportListItem; onClick: () => void }) {
  const hasMedia = report.media_count > 0;
  const primaryMedia = report.primary_media;

  return (
    <Card variant="hover" className="cursor-pointer" onClick={onClick}>
      <div className="flex flex-col sm:flex-row gap-4">
        {hasMedia && primaryMedia && (
          <div className="relative w-full sm:w-32 h-24 sm:h-auto rounded-lg overflow-hidden flex-shrink-0 bg-gray-100 dark:bg-gray-800">
            <img
              src={primaryMedia.storage_path.startsWith('http') ? primaryMedia.storage_path : `/api/v1/media/${primaryMedia.id}`}
              alt={`Report ${report.tracking_id}`}
              className="w-full h-full object-cover"
              loading="lazy"
            />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap mb-1">
                <Badge variant="primary">{report.tracking_id}</Badge>
                <Badge variant="status" status={report.status}>{getStatusLabel(report.status)}</Badge>
                <Badge variant="priority" priority={report.priority_band}>{report.priority_band.replace('_', ' ')}</Badge>
              </div>
              <h3 className="font-medium text-gray-900 dark:text-white truncate mb-1">
                {report.title || getCategoryLabel(report.category)}
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-2">{report.description}</p>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 flex-shrink-0">
              <span className="flex items-center gap-1">
                <MapPin className="w-4 h-4" />
                {report.address || 'Map location'}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400 mt-2">
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              {formatRelativeTime(report.created_at)}
            </span>
            <span className="flex items-center gap-1">
              {getCategoryIcon(report.category)}
              {getCategoryLabel(report.category)}
            </span>
            {report.media_count > 0 && (
              <span className="flex items-center gap-1">
                <Eye className="w-3.5 h-3.5" />
                {report.media_count} photo{report.media_count > 1 ? 's' : ''}
              </span>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}