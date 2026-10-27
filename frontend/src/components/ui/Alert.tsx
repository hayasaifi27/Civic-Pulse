import React from 'react';
import { cn } from '../../utils/helpers';
import { AlertCircle, CheckCircle, Info, XCircle, X } from 'lucide-react';

interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  onDismiss?: () => void;
}

export function Alert({ className, variant = 'info', title, children, onDismiss, ...props }: AlertProps) {
  const variants = {
    info: 'bg-blue-50 border-blue-200 text-blue-800',
    success: 'bg-green-50 border-green-200 text-green-800',
    warning: 'bg-amber-50 border-amber-200 text-amber-800',
    error: 'bg-red-50 border-red-200 text-red-800',
  };

  const icons = {
    info: <Info className="w-5 h-5" />,
    success: <CheckCircle className="w-5 h-5" />,
    warning: <AlertCircle className="w-5 h-5" />,
    error: <XCircle className="w-5 h-5" />,
  };

  return (
    <div
      className={cn(
        'relative flex gap-3 p-4 rounded-lg border',
        variants[variant],
        className
      )}
      role="alert"
      {...props}
    >
      <div className="flex-shrink-0">{icons[variant]}</div>
      <div className="flex-1 min-w-0">
        {title && <h3 className="text-sm font-medium">{title}</h3>}
        <div className={cn('text-sm', title && 'mt-1')}>{children}</div>
      </div>
      {onDismiss && (
        <button
          type="button"
          className={cn(
            'flex-shrink-0 text-current opacity-50 hover:opacity-75 focus:outline-none focus:ring-2 focus:ring-offset-2',
            variant === 'error' && 'focus:ring-red-500',
            variant === 'success' && 'focus:ring-green-500',
            variant === 'warning' && 'focus:ring-amber-500',
            variant === 'info' && 'focus:ring-blue-500'
          )}
          onClick={onDismiss}
          aria-label="Dismiss"
        >
          <X className="w-5 h-5" />
        </button>
      )}
    </div>
  );
}