import React from 'react';
import { cn } from '../../utils/helpers';

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
  maxLength?: number;
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, error, helperText, maxLength, id, ...props }, ref) => {
    const textareaId = id || label?.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={textareaId} className="block text-sm font-medium text-gray-700 mb-1">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={textareaId}
          className={cn(
            'w-full px-3 py-2 border rounded-lg shadow-sm placeholder-gray-400',
            'focus:outline-none focus:ring-2 focus:ring-civic-teal focus:border-civic-teal',
            'transition-colors resize-y min-h-[100px]',
            error ? 'border-civic-red focus:ring-civic-red focus:border-civic-red' : 'border-gray-300',
            className
          )}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? `${textareaId}-error` : helperText ? `${textareaId}-helper` : maxLength ? `${textareaId}-count` : undefined}
          {...props}
        />
        <div className="mt-1 flex justify-between">
          {error && (
            <p id={`${textareaId}-error`} className="text-sm text-civic-red" role="alert">
              {error}
            </p>
          )}
          {helperText && !error && (
            <p id={`${textareaId}-helper`} className="text-sm text-gray-500">
              {helperText}
            </p>
          )}
          {maxLength && (
            <p id={`${textareaId}-count`} className="text-sm text-gray-500">
              {(typeof props.value === 'string' ? props.value.length : 0) || 0}/{maxLength}
            </p>
          )}
        </div>
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';