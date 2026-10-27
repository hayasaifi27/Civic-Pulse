"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from geoalchemy2 import Geometry

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "postgis"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')

    op.create_table(
        'profiles',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('full_name', sa.String(255)),
        sa.Column('phone', sa.String(50)),
        sa.Column('avatar_url', sa.String(500)),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('role', sa.Enum('citizen', 'admin', 'field_worker', 'supervisor', name='userrole'), nullable=False, server_default='citizen'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('department_id', UUID(as_uuid=True)),
        sa.Column('service_zone_id', UUID(as_uuid=True)),
        sa.Column('preferences', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_profiles_email', 'profiles', ['email'])
    op.create_index('ix_profiles_role', 'profiles', ['role'])

    op.create_table(
        'departments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(255), unique=True, nullable=False),
        sa.Column('code', sa.String(50), unique=True, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('contact_email', sa.String(255)),
        sa.Column('contact_phone', sa.String(50)),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('sla_hours', sa.Integer, nullable=False, server_default='72'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'service_zones',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(50), unique=True, nullable=False),
        sa.Column('boundary', Geometry(geometry_type='POLYGON', srid=4326), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_service_zones_boundary', 'service_zones', ['boundary'], postgresql_using='gist')

    op.create_table(
        'configurable_categories',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('code', sa.String(50), unique=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('icon', sa.String(100)),
        sa.Column('color', sa.String(7)),
        sa.Column('severity_base', sa.Integer, nullable=False, server_default='50'),
        sa.Column('risk_base', sa.Integer, nullable=False, server_default='50'),
        sa.Column('department_id', UUID(as_uuid=True)),
        sa.Column('sla_hours', sa.Integer, nullable=False, server_default='72'),
        sa.Column('duplicate_distance_meters', sa.Integer, nullable=False, server_default='100'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('sort_order', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'routing_rules',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('category_id', UUID(as_uuid=True), nullable=False),
        sa.Column('department_id', UUID(as_uuid=True), nullable=False),
        sa.Column('service_zone_id', UUID(as_uuid=True)),
        sa.Column('priority_band', sa.Enum('low', 'medium', 'high', 'critical', 'safety_escalation', name='priorityband')),
        sa.Column('is_default', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_foreign_key('fk_routing_rules_category', 'routing_rules', 'configurable_categories', ['category_id'], ['id'])
    op.create_foreign_key('fk_routing_rules_department', 'routing_rules', 'departments', ['department_id'], ['id'])
    op.create_foreign_key('fk_routing_rules_service_zone', 'routing_rules', 'service_zones', ['service_zone_id'], ['id'])

    op.create_table(
        'scoring_rules',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('version', sa.String(50), unique=True, nullable=False),
        sa.Column('severity_weight', sa.Float, nullable=False, server_default='0.35'),
        sa.Column('risk_weight', sa.Float, nullable=False, server_default='0.25'),
        sa.Column('time_weight', sa.Float, nullable=False, server_default='0.20'),
        sa.Column('corroboration_weight', sa.Float, nullable=False, server_default='0.20'),
        sa.Column('safety_escalation_threshold', sa.Float, nullable=False, server_default='85.0'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('description', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', UUID(as_uuid=True)),
    )

    op.create_table(
        'reports',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('tracking_id', sa.String(20), unique=True, nullable=False),
        sa.Column('title', sa.String(500)),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('category', sa.Enum('pothole', 'garbage', 'streetlight', 'water_leakage', 'drainage', 'footpath', 'obstruction', 'property_damage', 'sanitation', 'other', name='issuecategory'), nullable=False),
        sa.Column('category_confidence', sa.Float),
        sa.Column('category_source', sa.String(50)),
        sa.Column('coordinates', Geometry(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('address', sa.String(500)),
        sa.Column('landmark', sa.String(500)),
        sa.Column('status', sa.Enum('reported', 'under_review', 'needs_more_info', 'verified', 'assigned', 'in_progress', 'resolved_pending_confirmation', 'closed', 'rejected', 'reopened', name='reportstatus'), nullable=False, server_default='reported'),
        sa.Column('priority_score', sa.Float, nullable=False, server_default='0.0'),
        sa.Column('priority_band', sa.Enum('low', 'medium', 'high', 'critical', 'safety_escalation', name='priorityband'), nullable=False, server_default='low'),
        sa.Column('priority_version', sa.String(50)),
        sa.Column('assigned_department_id', UUID(as_uuid=True)),
        sa.Column('reporter_id', UUID(as_uuid=True)),
        sa.Column('assignee_id', UUID(as_uuid=True)),
        sa.Column('is_anonymous', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_public', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('duplicate_primary_id', UUID(as_uuid=True)),
        sa.Column('metadata', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('verified_at', sa.DateTime(timezone=True)),
        sa.Column('assigned_at', sa.DateTime(timezone=True)),
        sa.Column('resolved_at', sa.DateTime(timezone=True)),
        sa.Column('closed_at', sa.DateTime(timezone=True)),
    )
    op.create_index('ix_reports_tracking_id', 'reports', ['tracking_id'])
    op.create_index('ix_reports_category', 'reports', ['category'])
    op.create_index('ix_reports_status', 'reports', ['status'])
    op.create_index('ix_reports_priority_band', 'reports', ['priority_band'])
    op.create_index('ix_reports_created_at', 'reports', ['created_at'])
    op.create_index('ix_reports_assigned_department_id', 'reports', ['assigned_department_id'])
    op.create_index('ix_reports_reporter_id', 'reports', ['reporter_id'])
    op.create_index('ix_reports_assignee_id', 'reports', ['assignee_id'])
    op.create_index('ix_reports_coordinates', 'reports', ['coordinates'], postgresql_using='gist')
    op.create_index('ix_reports_category_status', 'reports', ['category', 'status'])
    op.create_foreign_key('fk_reports_assigned_department', 'reports', 'departments', ['assigned_department_id'], ['id'])
    op.create_foreign_key('fk_reports_reporter', 'reports', 'profiles', ['reporter_id'], ['id'])
    op.create_foreign_key('fk_reports_assignee', 'reports', 'profiles', ['assignee_id'], ['id'])
    op.create_foreign_key('fk_reports_duplicate_primary', 'reports', 'reports', ['duplicate_primary_id'], ['id'])

    op.create_table(
        'report_media',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('report_id', UUID(as_uuid=True), nullable=False),
        sa.Column('storage_path', sa.String(500), nullable=False),
        sa.Column('file_name', sa.String(255)),
        sa.Column('mime_type', sa.String(100)),
        sa.Column('file_size', sa.Integer),
        sa.Column('width', sa.Integer),
        sa.Column('height', sa.Integer),
        sa.Column('is_primary', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('sort_order', sa.Integer, nullable=False, server_default='0'),
        sa.Column('analysis_result', JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_foreign_key('fk_report_media_report', 'report_media', 'reports', ['report_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_report_media_report_id', 'report_media', ['report_id'])

    op.create_table(
        'report_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('report_id', UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('previous_status', sa.Enum('reported', 'under_review', 'needs_more_info', 'verified', 'assigned', 'in_progress', 'resolved_pending_confirmation', 'closed', 'rejected', 'reopened', name='reportstatus')),
        sa.Column('new_status', sa.Enum('reported', 'under_review', 'needs_more_info', 'verified', 'assigned', 'in_progress', 'resolved_pending_confirmation', 'closed', 'rejected', 'reopened', name='reportstatus')),
        sa.Column('actor_id', UUID(as_uuid=True)),
        sa.Column('actor_role', sa.Enum('citizen', 'admin', 'field_worker', 'supervisor', name='userrole')),
        sa.Column('reason', sa.Text),
        sa.Column('metadata', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_foreign_key('fk_report_events_report', 'report_events', 'reports', ['report_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_report_events_actor', 'report_events', 'profiles', ['actor_id'], ['id'])
    op.create_index('ix_report_events_report_id', 'report_events', ['report_id'])
    op.create_index('ix_report_events_created_at', 'report_events', ['created_at'])

    op.create_table(
        'report_comments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('report_id', UUID(as_uuid=True), nullable=False),
        sa.Column('author_id', UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('is_internal', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_foreign_key('fk_report_comments_report', 'report_comments', 'reports', ['report_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_report_comments_author', 'report_comments', 'profiles', ['author_id'], ['id'])
    op.create_index('ix_report_comments_report_id', 'report_comments', ['report_id'])

    op.create_table(
        'duplicate_candidates',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('report_id', UUID(as_uuid=True), nullable=False),
        sa.Column('candidate_report_id', UUID(as_uuid=True), nullable=False),
        sa.Column('distance_meters', sa.Float),
        sa.Column('category_match', sa.Boolean),
        sa.Column('description_similarity', sa.Float),
        sa.Column('image_similarity', sa.Float),
        sa.Column('time_proximity_hours', sa.Float),
        sa.Column('match_score', sa.Float),
        sa.Column('match_explanation', sa.Text),
        sa.Column('suggested_action', sa.String(50)),
        sa.Column('status', sa.Enum('pending', 'confirmed', 'rejected', 'unlinked', name='duplicatestatus'), nullable=False, server_default='pending'),
        sa.Column('reviewed_by', UUID(as_uuid=True)),
        sa.Column('reviewed_at', sa.DateTime(timezone=True)),
        sa.Column('review_reason', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_foreign_key('fk_duplicate_candidates_report', 'duplicate_candidates', 'reports', ['report_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_duplicate_candidates_candidate', 'duplicate_candidates', 'reports', ['candidate_report_id'], ['id'])
    op.create_foreign_key('fk_duplicate_candidates_reviewed_by', 'duplicate_candidates', 'profiles', ['reviewed_by'], ['id'])
    op.create_index('ix_duplicate_candidates_report_id', 'duplicate_candidates', ['report_id'])
    op.create_index('ix_duplicate_candidates_candidate_report_id', 'duplicate_candidates', ['candidate_report_id'])

    op.create_table(
        'report_links',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('primary_report_id', UUID(as_uuid=True), nullable=False),
        sa.Column('duplicate_report_id', UUID(as_uuid=True), nullable=False),
        sa.Column('linked_by', UUID(as_uuid=True)),
        sa.Column('link_reason', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_foreign_key('fk_report_links_primary', 'report_links', 'reports', ['primary_report_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_report_links_duplicate', 'report_links', 'reports', ['duplicate_report_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_report_links_linked_by', 'report_links', 'profiles', ['linked_by'], ['id'])
    op.create_unique_constraint('uq_report_link', 'report_links', ['primary_report_id', 'duplicate_report_id'])
    op.create_index('ix_report_links_primary', 'report_links', ['primary_report_id'])
    op.create_index('ix_report_links_duplicate', 'report_links', ['duplicate_report_id'])

    op.create_table(
        'assignments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('report_id', UUID(as_uuid=True), nullable=False),
        sa.Column('department_id', UUID(as_uuid=True), nullable=False),
        sa.Column('worker_id', UUID(as_uuid=True)),
        sa.Column('assigned_by', UUID(as_uuid=True)),
        sa.Column('status', sa.Enum('pending', 'accepted', 'in_progress', 'completed', 'rejected', name='assignmentstatus'), nullable=False, server_default='pending'),
        sa.Column('priority', sa.Integer, nullable=False, server_default='0'),
        sa.Column('instructions', sa.Text),
        sa.Column('sla_deadline', sa.DateTime(timezone=True)),
        sa.Column('accepted_at', sa.DateTime(timezone=True)),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_foreign_key('fk_assignments_report', 'assignments', 'reports', ['report_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_assignments_department', 'assignments', 'departments', ['department_id'], ['id'])
    op.create_foreign_key('fk_assignments_worker', 'assignments', 'profiles', ['worker_id'], ['id'])
    op.create_foreign_key('fk_assignments_assigned_by', 'assignments', 'profiles', ['assigned_by'], ['id'])
    op.create_index('ix_assignments_report_id', 'assignments', ['report_id'])
    op.create_index('ix_assignments_department_id', 'assignments', ['department_id'])
    op.create_index('ix_assignments_worker_id', 'assignments', ['worker_id'])
    op.create_index('ix_assignments_status', 'assignments', ['status'])

    op.create_table(
        'resolution_evidence',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('report_id', UUID(as_uuid=True), nullable=False),
        sa.Column('assignment_id', UUID(as_uuid=True)),
        sa.Column('submitted_by_id', UUID(as_uuid=True), nullable=False),
        sa.Column('before_media', JSONB),
        sa.Column('after_media', JSONB),
        sa.Column('work_notes', sa.Text),
        sa.Column('status', sa.Enum('submitted', 'approved', 'rejected', 'needs_rework', name='resolutionstatus'), nullable=False, server_default='submitted'),
        sa.Column('reviewed_by', UUID(as_uuid=True)),
        sa.Column('reviewed_at', sa.DateTime(timezone=True)),
        sa.Column('review_notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_foreign_key('fk_resolution_evidence_report', 'resolution_evidence', 'reports', ['report_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_resolution_evidence_assignment', 'resolution_evidence', 'assignments', ['assignment_id'], ['id'])
    op.create_foreign_key('fk_resolution_evidence_submitted_by', 'resolution_evidence', 'profiles', ['submitted_by_id'], ['id'])
    op.create_foreign_key('fk_resolution_evidence_reviewed_by', 'resolution_evidence', 'profiles', ['reviewed_by'], ['id'])
    op.create_index('ix_resolution_evidence_report_id', 'resolution_evidence', ['report_id'])
    op.create_index('ix_resolution_evidence_status', 'resolution_evidence', ['status'])

    op.create_table(
        'priority_assessments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('report_id', UUID(as_uuid=True), nullable=False),
        sa.Column('severity_score', sa.Float),
        sa.Column('risk_score', sa.Float),
        sa.Column('time_score', sa.Float),
        sa.Column('corroboration_score', sa.Float),
        sa.Column('total_score', sa.Float),
        sa.Column('priority_band', sa.Enum('low', 'medium', 'high', 'critical', 'safety_escalation', name='priorityband')),
        sa.Column('rule_version', sa.String(50)),
        sa.Column('factor_details', JSONB),
        sa.Column('escalation_recommended', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('escalation_reason', sa.Text),
        sa.Column('assessed_by', sa.String(50)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_foreign_key('fk_priority_assessments_report', 'priority_assessments', 'reports', ['report_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_priority_assessments_report_id', 'priority_assessments', ['report_id'])

    op.create_table(
        'agent_runs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('report_id', UUID(as_uuid=True), nullable=False),
        sa.Column('agent_type', sa.String(50), nullable=False),
        sa.Column('agent_version', sa.String(50)),
        sa.Column('input_data', JSONB),
        sa.Column('output_data', JSONB),
        sa.Column('status', sa.String(50)),
        sa.Column('error_message', sa.Text),
        sa.Column('duration_ms', sa.Integer),
        sa.Column('correlation_id', sa.String(100)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_foreign_key('fk_agent_runs_report', 'agent_runs', 'reports', ['report_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_agent_runs_report_id', 'agent_runs', ['report_id'])
    op.create_index('ix_agent_runs_correlation_id', 'agent_runs', ['correlation_id'])

    op.create_table(
        'notifications',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('report_id', UUID(as_uuid=True)),
        sa.Column('channel', sa.Enum('in_app', 'email', 'sms', 'push', name='notificationchannel'), nullable=False, server_default='in_app'),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('title', sa.String(255)),
        sa.Column('message', sa.Text),
        sa.Column('data', JSONB, nullable=False, server_default='{}'),
        sa.Column('is_read', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('read_at', sa.DateTime(timezone=True)),
        sa.Column('sent_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_foreign_key('fk_notifications_user', 'notifications', 'profiles', ['user_id'], ['id'])
    op.create_foreign_key('fk_notifications_report', 'notifications', 'reports', ['report_id'], ['id'])
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_is_read', 'notifications', ['is_read'])

    op.create_table(
        'feedback',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('report_id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True)),
        sa.Column('rating', sa.Integer),
        sa.Column('comment', sa.Text),
        sa.Column('is_public', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_foreign_key('fk_feedback_report', 'feedback', 'reports', ['report_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_feedback_user', 'feedback', 'profiles', ['user_id'], ['id'])
    op.create_index('ix_feedback_report_id', 'feedback', ['report_id'])

    op.create_table(
        'audit_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('actor_id', UUID(as_uuid=True)),
        sa.Column('actor_role', sa.Enum('citizen', 'admin', 'field_worker', 'supervisor', name='userrole')),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(100)),
        sa.Column('resource_id', UUID(as_uuid=True)),
        sa.Column('previous_state', JSONB),
        sa.Column('new_state', JSONB),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.String(500)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_foreign_key('fk_audit_logs_actor', 'audit_logs', 'profiles', ['actor_id'], ['id'])
    op.create_index('ix_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('ix_audit_logs_actor_created', 'audit_logs', ['actor_id', 'created_at'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])

    op.create_table(
        'moderation_actions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('reporter_id', UUID(as_uuid=True)),
        sa.Column('target_user_id', UUID(as_uuid=True)),
        sa.Column('target_report_id', UUID(as_uuid=True)),
        sa.Column('action_type', sa.String(50)),
        sa.Column('reason', sa.Text),
        sa.Column('duration_days', sa.Integer),
        sa.Column('created_by', UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
    )
    op.create_foreign_key('fk_moderation_reporter', 'moderation_actions', 'profiles', ['reporter_id'], ['id'])
    op.create_foreign_key('fk_moderation_target_user', 'moderation_actions', 'profiles', ['target_user_id'], ['id'])
    op.create_foreign_key('fk_moderation_target_report', 'moderation_actions', 'reports', ['target_report_id'], ['id'])
    op.create_foreign_key('fk_moderation_created_by', 'moderation_actions', 'profiles', ['created_by'], ['id'])


def downgrade():
    op.drop_table('moderation_actions')
    op.drop_table('audit_logs')
    op.drop_table('feedback')
    op.drop_table('notifications')
    op.drop_table('agent_runs')
    op.drop_table('priority_assessments')
    op.drop_table('resolution_evidence')
    op.drop_table('assignments')
    op.drop_table('report_links')
    op.drop_table('duplicate_candidates')
    op.drop_table('report_comments')
    op.drop_table('report_events')
    op.drop_table('report_media')
    op.drop_table('reports')
    op.drop_table('scoring_rules')
    op.drop_table('routing_rules')
    op.drop_table('configurable_categories')
    op.drop_table('service_zones')
    op.drop_table('departments')
    op.drop_table('profiles')
    
    op.execute('DROP TYPE IF EXISTS userrole')
    op.execute('DROP TYPE IF EXISTS reportstatus')
    op.execute('DROP TYPE IF EXISTS priorityband')
    op.execute('DROP TYPE IF EXISTS issuecategory')
    op.execute('DROP TYPE IF EXISTS duplicatestatus')
    op.execute('DROP TYPE IF EXISTS assignmentstatus')
    op.execute('DROP TYPE IF EXISTS resolutionstatus')
    op.execute('DROP TYPE IF EXISTS notificationchannel')