import React from 'react';
import { useTheme } from '../../hooks/useTheme';
import { Button } from './Button';
import { Sun, Moon, Monitor, ChevronDown } from 'lucide-react';
import { cn } from '../../utils/helpers';
import { Modal } from './Modal';

export function ThemeToggle({ variant = 'dropdown' }: { variant?: 'dropdown' | 'button' | 'simple' }) {
  const { theme, resolvedTheme, setTheme, toggleTheme } = useTheme();
  const [isOpen, setIsOpen] = React.useState(false);

  const themeOptions = [
    { value: 'light' as const, label: 'Light', icon: Sun, description: 'Always use light mode' },
    { value: 'dark' as const, label: 'Dark', icon: Moon, description: 'Always use dark mode' },
    { value: 'system' as const, label: 'System', icon: Monitor, description: 'Match system preference' },
  ];

  if (variant === 'simple') {
    return (
      <Button
        variant="ghost"
        size="sm"
        onClick={toggleTheme}
        aria-label={`Switch to ${resolvedTheme === 'light' ? 'dark' : 'light'} mode`}
        className="relative"
      >
        {resolvedTheme === 'light' ? (
          <Moon className="w-5 h-5" />
        ) : (
          <Sun className="w-5 h-5" />
        )}
      </Button>
    );
  }

  if (variant === 'button') {
    return (
      <Button
        variant="secondary"
        size="sm"
        onClick={toggleTheme}
        aria-label={`Cycle theme: ${theme} → ${theme === 'light' ? 'dark' : theme === 'dark' ? 'system' : 'light'}`}
        className="gap-2"
      >
        {theme === 'light' && <Sun className="w-4 h-4" />}
        {theme === 'dark' && <Moon className="w-4 h-4" />}
        {theme === 'system' && <Monitor className="w-4 h-4" />}
        <span className="hidden sm:inline capitalize">{theme}</span>
        <ChevronDown className="w-4 h-4" />
      </Button>
    );
  }

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Theme options"
        aria-expanded={isOpen}
        aria-haspopup="true"
        className="relative"
      >
        {resolvedTheme === 'light' ? (
          <Sun className="w-5 h-5 text-civic-amber" />
        ) : (
          <Moon className="w-5 h-5 text-civic-blue" />
        )}
      </Button>

      <Modal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        size="sm"
        showCloseButton={false}
        closeOnOverlayClick
        closeOnEscape
      >
        <div className="p-2">
          <p className="px-3 py-2 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
            Appearance
          </p>
          {themeOptions.map((option) => (
            <button
              key={option.value}
              onClick={() => {
                setTheme(option.value);
                setIsOpen(false);
              }}
              className={cn(
                'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors',
                'hover:bg-gray-100 dark:hover:bg-gray-700',
                theme === option.value && 'bg-civic-teal/10 dark:bg-civic-teal/20 text-civic-teal'
              )}
              aria-current={theme === option.value ? 'true' : 'false'}
            >
              <option.icon className={cn('w-5 h-5 flex-shrink-0', theme === option.value ? 'text-civic-teal' : 'text-gray-400')} aria-hidden="true" />
              <div className="flex-1 text-left">
                <p className={cn('font-medium', theme === option.value ? 'text-gray-900 dark:text-white' : 'text-gray-700 dark:text-gray-300')}>
                  {option.label}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">{option.description}</p>
              </div>
              {theme === option.value && (
                <svg className="w-5 h-5 text-civic-teal flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </button>
          ))}
        </div>
      </Modal>
    </div>
  );
}

export function ThemeToggleCompact() {
  const { resolvedTheme, toggleTheme } = useTheme();

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={toggleTheme}
      aria-label={`Switch to ${resolvedTheme === 'light' ? 'dark' : 'light'} mode`}
      className="p-2"
    >
      {resolvedTheme === 'light' ? (
        <Moon className="w-5 h-5" />
      ) : (
        <Sun className="w-5 h-5" />
      )}
    </Button>
  );
}