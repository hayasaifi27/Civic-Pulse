import React from 'react';
import { cn } from '../../utils/helpers';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'primary' | 'teal' | 'green' | 'amber' | 'red' | 'status' | 'priority';
  status?: string;
  priority?: string;
}

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', status, priority, children, ...props }, ref) => {
    const variants = {
      default: 'bg-gray-100 text-gray-700',
      primary: 'bg-civic-navy/10 text-civic-navy',
      teal: 'bg-civic-teal/10 text-civic-teal',
      green: 'bg-civic-green/10 text-civic-green',
      amber: 'bg-civic-amber/10 text-civic-amber',
      red: 'bg-civic-red/10 text-civic-red',
      status: '',
      priority: '',
    };

    let statusClass = '';
    if (variant === 'status' && status) {
      const statusClasses: Record<string, string> = {
        reported: 'bg-blue-50 text-blue-700',
        under_review: 'bg-amber-50 text-amber-700',
        needs_more_info: 'bg-orange-50 text-orange-700',
        verified: 'bg-teal-50 text-teal-700',
        assigned: 'bg-indigo-50 text-indigo-700',
        in_progress: 'bg-purple-50 text-purple-700',
        resolved_pending_confirmation: 'bg-green-50 text-green-700',
        closed: 'bg-gray-50 text-gray-700',
        rejected: 'bg-red-50 text-red-700',
        reopened: 'bg-pink-50 text-pink-700',
      };
      statusClass = statusClasses[status] || 'bg-gray-50 text-gray-700';
    }

    let priorityClass = '';
    if (variant === 'priority' && priority) {
      const priorityClasses: Record<string, string> = {
        low: 'bg-gray-100 text-gray-700',
        medium: 'bg-blue-50 text-blue-700',
        high: 'bg-amber-50 text-amber-700',
        critical: 'bg-orange-50 text-orange-700',
        safety_escalation: 'bg-red-50 text-red-700',
      };
      priorityClass = priorityClasses[priority] || 'bg-gray-100 text-gray-700';
    }

    return (
      <span
        ref={ref}
        className={cn(
          'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
          variants[variant],
          statusClass,
          priorityClass,
          className
        )}
        {...props}
      >
        {children}
      </span>
    );
  }
);

Badge.displayName = 'Badge';