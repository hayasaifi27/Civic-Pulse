import React, { useState } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useNotifications } from '../hooks/useNotifications';
import { Bell, Menu, X, User, LogOut, LayoutDashboard, MapPin, Settings, HelpCircle, ChevronDown } from 'lucide-react';
import { cn } from '../utils/helpers';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Modal } from '../components/ui/Modal';
import { ThemeToggle } from '../components/ui/ThemeToggle';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, roles: ['citizen', 'admin', 'field_worker', 'supervisor'] },
  { name: 'Submit Report', href: '/submit', icon: MapPin, roles: ['citizen'] },
  { name: 'My Reports', href: '/my-reports', icon: MapPin, roles: ['citizen'] },
  { name: 'Map View', href: '/map', icon: MapPin, roles: ['citizen', 'admin', 'supervisor'] },
  { name: 'Admin Dashboard', href: '/admin', icon: LayoutDashboard, roles: ['admin'] },
  { name: 'Field Tasks', href: '/field', icon: MapPin, roles: ['field_worker'] },
  { name: 'Supervisor Queue', href: '/supervisor', icon: LayoutDashboard, roles: ['supervisor'] },
];

export function MainLayout() {
  const { user, logout, hasRole } = useAuth();
  const { notifications, unreadCount, markAsRead } = useNotifications();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  const filteredNav = navigation.filter(item => 
    item.roles.includes(user?.role || '')
  );

  const handleNotificationClick = async (notification: any) => {
    if (!notification.is_read) {
      await markAsRead(notification.id);
    }
    if (notification.data?.report_id) {
      window.location.href = `/reports/${notification.data.report_id}`;
    }
    setNotificationsOpen(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transform transition-transform duration-300 ease-in-out lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
        aria-label="Sidebar"
      >
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-between h-16 px-6 border-b border-gray-100 dark:border-gray-700">
            <h1 className="text-xl font-bold text-civic-navy dark:text-white">CivicPulse</h1>
            <button
              className="lg:hidden p-2 text-gray-500 hover:text-gray-700"
              onClick={() => setSidebarOpen(false)}
              aria-label="Close sidebar"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
          
          <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto" aria-label="Main navigation">
            {filteredNav.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) => cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-civic-navy text-white'
                    : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white'
                )}
                onClick={() => setSidebarOpen(false)}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
                {item.name}
              </NavLink>
            ))}
          </nav>

          <div className="p-4 border-t border-gray-100 dark:border-gray-700">
            <NavLink
              to="/profile"
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white"
              onClick={() => setSidebarOpen(false)}
            >
              <Settings className="w-5 h-5" aria-hidden="true" />
              Settings
            </NavLink>
            <NavLink
              to="/help"
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white"
              onClick={() => setSidebarOpen(false)}
            >
              <HelpCircle className="w-5 h-5" aria-hidden="true" />
              Help
            </NavLink>
            <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700">
              <ThemeToggle variant="button" />
            </div>
          </div>
        </div>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-40 bg-white/95 dark:bg-gray-900/95 backdrop-blur-sm border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between h-16 px-4 sm:px-6">
            <button
              className="lg:hidden p-2 text-gray-500 hover:text-gray-700"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open sidebar"
            >
              <Menu className="w-6 h-6" />
            </button>

            <div className="flex-1 lg:flex-none" />

            <div className="flex items-center gap-4">
              <div className="relative hidden sm:block">
                <ThemeToggle variant="dropdown" />
              </div>
              <div className="relative">
                <button
                  onClick={() => setNotificationsOpen(!notificationsOpen)}
                  className="relative p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                  aria-label={`Notifications${unreadCount > 0 ? `, ${unreadCount} unread` : ''}`}
                  aria-expanded={notificationsOpen}
                >
                  <Bell className="w-5 h-5" />
                  {unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 w-5 h-5 bg-civic-red text-white text-xs font-medium rounded-full flex items-center justify-center">
                      {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                  )}
                </button>

                <Modal isOpen={notificationsOpen} onClose={() => setNotificationsOpen(false)} size="lg" title="Notifications" closeOnOverlayClick>
                  <div className="max-h-96 overflow-y-auto">
                    {notifications.length === 0 ? (
                      <div className="text-center py-8 text-gray-500">No notifications</div>
                    ) : (
                      <ul className="space-y-2" role="list">
                        {notifications.slice(0, 20).map((notification) => (
                          <li key={notification.id} onClick={() => handleNotificationClick(notification)} className={cn(
                            'p-3 rounded-lg cursor-pointer transition-colors',
                            notification.is_read ? 'hover:bg-gray-50' : 'bg-civic-navy/5 hover:bg-civic-navy/10'
                          )}>
                            <p className={cn('text-sm font-medium', notification.is_read ? 'text-gray-700' : 'text-gray-900')}>
                              {notification.title}
                            </p>
                            <p className="text-sm text-gray-500 mt-0.5 line-clamp-1">{notification.message}</p>
                            <p className="text-xs text-gray-400 mt-1">{formatRelativeTime(notification.created_at)}</p>
                          </li>
                        ))}
                      </ul>
                    )}
                    <div className="mt-4 pt-4 border-t border-gray-100 text-center">
                      <button onClick={() => setNotificationsOpen(false)} className="text-civic-teal text-sm font-medium hover:underline">
                        View all notifications
                      </button>
                    </div>
                  </div>
                </Modal>
              </div>

              <div className="relative">
                <button
                  onClick={() => setProfileMenuOpen(!profileMenuOpen)}
                  className="flex items-center gap-2 p-1.5 hover:bg-gray-100 rounded-lg"
                  aria-expanded={profileMenuOpen}
                  aria-haspopup="true"
                >
                  <div className="w-8 h-8 rounded-full bg-civic-teal/10 flex items-center justify-center">
                    <User className="w-5 h-5 text-civic-teal" />
                  </div>
                  <span className="hidden sm:block text-sm font-medium text-gray-700">{user?.full_name || user?.email}</span>
                  <ChevronDown className="w-4 h-4 text-gray-500 hidden sm:block" />
                </button>

                <Modal isOpen={profileMenuOpen} onClose={() => setProfileMenuOpen(false)} size="sm" closeOnOverlayClick>
                  <div className="space-y-1">
                    <div className="px-4 py-2 border-b border-gray-100">
                      <p className="text-sm font-medium text-gray-900">{user?.full_name || 'User'}</p>
                      <p className="text-xs text-gray-500">{user?.email}</p>
                      <Badge variant="primary" className="mt-1 capitalize">{user?.role?.replace('_', ' ')}</Badge>
                    </div>
                    <a href="/profile" className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50" onClick={() => setProfileMenuOpen(false)}>
                      <User className="w-4 h-4" />
                      Profile
                    </a>
                    <a href="/settings" className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50" onClick={() => setProfileMenuOpen(false)}>
                      <Settings className="w-4 h-4" />
                      Settings
                    </a>
                    <hr className="my-1 border-gray-100" />
                    <button onClick={logout} className="flex items-center gap-2 w-full px-4 py-2 text-sm text-civic-red hover:bg-red-50">
                      <LogOut className="w-4 h-4" />
                      Sign out
                    </button>
                  </div>
                </Modal>
              </div>
            </div>
          </div>
        </header>

        <main className="p-4 sm:p-6 lg:p-8" role="main">
          <Outlet />
        </main>
      </div>

      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}
    </div>
  );
}

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}