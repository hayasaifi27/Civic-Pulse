import React from 'react';
import { Outlet } from 'react-router-dom';
import { cn } from '../utils/helpers';
import { ThemeToggle } from '../components/ui/ThemeToggle';

export function AuthLayout() {
  return (
    <div className="min-h-screen flex">
      <div className="hidden lg:flex lg:w-1/2 bg-civic-navy p-12 flex-col justify-between relative overflow-hidden">
        <div className="z-10 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-white mb-4">CivicPulse</h1>
            <p className="text-civic-teal/80 text-lg">Every Report Matters. Every Issue Has a Path to Resolution.</p>
          </div>
          <ThemeToggle variant="button" />
        </div>
        <div className="z-10 space-y-6 text-white/70">
          <div className="flex items-center gap-3">
            <span className="w-8 h-8 rounded-full bg-civic-teal flex items-center justify-center font-bold">📍</span>
            <span>Location-aware reporting</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="w-8 h-8 rounded-full bg-civic-teal flex items-center justify-center font-bold">🤖</span>
            <span>AI-powered classification</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="w-8 h-8 rounded-full bg-civic-teal flex items-center justify-center font-bold">🔍</span>
            <span>Duplicate detection</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="w-8 h-8 rounded-full bg-civic-teal flex items-center justify-center font-bold">📊</span>
            <span>Explainable priority scoring</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="w-8 h-8 rounded-full bg-civic-teal flex items-center justify-center font-bold">🤝</span>
            <span>Fetch.ai agent coordination</span>
          </div>
        </div>
        <div className="z-10 text-white/50 text-sm">
          CivicPulse v1.0.0 — Smart City Civic Intelligence Platform
        </div>
      </div>
      
      <div className="flex-1 flex items-center justify-center p-8 bg-gray-50 dark:bg-gray-900">
        <div className="w-full max-w-md">
          <div className="lg:hidden mb-8 text-center flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-civic-navy dark:text-white">CivicPulse</h1>
              <p className="text-civic-teal mt-1">Every Report Matters.</p>
            </div>
            <ThemeToggle variant="simple" />
          </div>
          <Outlet />
        </div>
      </div>
    </div>
  );
}