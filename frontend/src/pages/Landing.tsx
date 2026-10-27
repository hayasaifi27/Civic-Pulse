import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { ArrowRight, MapPin, Bot, Search, BarChart3, Users, Shield } from 'lucide-react';
import { ThemeToggle } from '../components/ui/ThemeToggle';

const features = [
  {
    icon: MapPin,
    title: 'Location-Aware Reporting',
    description: 'Capture GPS coordinates automatically or pin locations manually on an interactive map with OpenStreetMap.',
  },
  {
    icon: Bot,
    title: 'AI-Powered Classification',
    description: 'Automatic categorization of civic issues from photos and descriptions with confidence scores and explanations.',
  },
  {
    icon: Search,
    title: 'Smart Duplicate Detection',
    description: 'Geospatial and semantic analysis to identify related reports and prevent duplicate work orders.',
  },
  {
    icon: BarChart3,
    title: 'Explainable Priority Scoring',
    description: 'Transparent priority calculation based on severity, risk, time, and community corroboration with full audit trail.',
  },
  {
    icon: Users,
    title: 'Community Participation',
    description: 'Citizen feedback loops, resolution confirmation, and quality-based recognition for verified contributions.',
  },
  {
    icon: Shield,
    title: 'Fetch.ai Agent Coordination',
    description: 'Autonomous agents for classification, deduplication, priority scoring, and department routing with human oversight.',
  },
];

export function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-950">
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/95 dark:bg-gray-900/95 backdrop-blur-sm border-b border-gray-100 dark:border-gray-800">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8" aria-label="Main navigation">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-civic-navy dark:text-white">CivicPulse</h1>
            </div>
            <div className="hidden md:flex items-center gap-8">
              <Link to="/login" className="text-gray-600 dark:text-gray-300 hover:text-civic-navy dark:hover:text-civic-teal font-medium transition-colors">
                Sign In
              </Link>
              <ThemeToggle variant="dropdown" />
              <Link to="/register" className="btn-primary">
                Get Started
              </Link>
            </div>
            <div className="md:hidden flex items-center gap-4">
              <ThemeToggle variant="simple" />
              <Link to="/register" className="btn-primary text-sm px-3 py-1.5">
                Get Started
              </Link>
            </div>
          </div>
        </nav>
      </header>

      <main className="pt-16">
        <section className="relative overflow-hidden bg-gradient-to-br from-civic-navy via-civic-navy/90 to-civic-teal/80 text-white">
          <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg%20width%3D%2260%22%20height%3D%2260%22%20viewBox%3D%220%200%2060%2060%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Cg%20fill%3D%22none%22%20fill-rule%3D%22evenodd%22%3E%3Cg%20fill%3D%22%23ffffff%22%20fill-opacity%3D%220.03%22%3E%3Cpath%20d%3D%22M36%2034v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6%2034v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6%204V0H4v4H0v2h4v4h2V6h4V4H6z%22%2F%3E%3C%2Fg%3E%3C%2Fg%3E%3C%2Fsvg%3E')]" aria-hidden="true" />
          <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 sm:py-32">
            <div className="max-w-3xl">
              <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 text-white/90 text-sm font-medium mb-6">
                <span className="w-2 h-2 rounded-full bg-civic-teal animate-pulse" />
                AI-Powered Civic Intelligence Platform
              </span>
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight mb-6">
                Every Report Matters.
                <br />
                <span className="text-civic-teal">Every Issue Has a Path to Resolution.</span>
              </h1>
              <p className="text-lg sm:text-xl text-white/80 mb-8 max-w-2xl">
                Transform citizen complaints into structured, verified, and traceable maintenance workflows using AI, geospatial analytics, and autonomous agents.
              </p>
              <div className="flex flex-wrap gap-4">
                <Link to="/register">
                  <Button size="lg" className="bg-white text-civic-navy hover:bg-white/90 gap-2">
                    Start Reporting
                    <ArrowRight className="w-5 h-5" />
                  </Button>
                </Link>
                <Link to="/map">
                  <Button size="lg" variant="secondary" className="bg-transparent border-white text-white hover:bg-white/10 gap-2">
                    Explore Map
                    <ArrowRight className="w-5 h-5" />
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </section>

        <section className="py-20 bg-white dark:bg-gray-900">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white mb-4">Built for Modern Civic Management</h2>
              <p className="text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
                Comprehensive tools for citizens, administrators, field workers, and supervisors to collaborate on civic issue resolution.
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {features.map((feature, index) => (
                <article key={index} className="card-hover p-6">
                  <div className="w-12 h-12 rounded-xl bg-civic-teal/10 flex items-center justify-center mb-4">
                    <feature.icon className="w-6 h-6 text-civic-teal" aria-hidden="true" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">{feature.title}</h3>
                  <p className="text-gray-600 dark:text-gray-400">{feature.description}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="py-20 bg-gray-50 dark:bg-gray-800">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid lg:grid-cols-2 gap-12 items-center">
              <div>
                <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white mb-6">Complete Complaint Lifecycle Management</h2>
                <p className="text-gray-600 dark:text-gray-300 mb-8">
                  From initial report submission through verification, assignment, field investigation, resolution evidence, and closure — every step is tracked, auditable, and transparent.
                </p>
                <ul className="space-y-4">
                  {[
                    'Reported → Under Review → Verified',
                    'Verified → Assigned → In Progress',
                    'In Progress → Resolved → Closed',
                    'Citizen confirmation & dispute resolution',
                    'Full audit trail with role-based access',
                  ].map((step, i) => (
                    <li key={i} className="flex items-center gap-3">
                      <span className="w-8 h-8 rounded-full bg-civic-teal flex items-center justify-center text-white font-medium text-sm">{i + 1}</span>
                      <span className="text-gray-700 dark:text-gray-300">{step}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="relative">
                <div className="aspect-square rounded-xl bg-gradient-to-br from-civic-navy to-civic-teal p-1">
                  <div className="w-full h-full rounded-lg bg-gray-900/50 dark:bg-gray-900/70 flex items-center justify-center">
                    <div className="text-center p-8">
                      <div className="w-32 h-32 mx-auto mb-6 rounded-full bg-civic-teal/20 flex items-center justify-center">
                        <Bot className="w-16 h-16 text-civic-teal" />
                      </div>
                      <h3 className="text-xl font-semibold text-white mb-2">Agent Workflow</h3>
                      <p className="text-white/70">Classification → Verification → Duplicate Detection → Priority Scoring → Department Routing</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="py-20 bg-civic-navy text-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h2 className="text-3xl sm:text-4xl font-bold mb-6">Ready to Improve Your Community?</h2>
            <p className="text-lg text-white/80 mb-8 max-w-2xl mx-auto">
              Join cities and communities using CivicPulse to streamline civic issue reporting and resolution.
            </p>
            <Link to="/register">
              <Button size="lg" className="bg-white text-civic-navy hover:bg-white/90 gap-2 w-auto">
                Create Free Account
                <ArrowRight className="w-5 h-5" />
              </Button>
            </Link>
          </div>
        </section>
      </main>

      <footer className="bg-gray-900 text-white/60 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
            <div>
              <h3 className="font-bold text-white mb-4">CivicPulse</h3>
              <p className="text-sm">AI-powered civic issue intelligence and resolution platform.</p>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Product</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/map" className="hover:text-white">Explore Map</Link></li>
                <li><Link to="/dashboard" className="hover:text-white">Dashboard</Link></li>
                <li><Link to="/submit" className="hover:text-white">Submit Report</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Resources</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/docs" className="hover:text-white">Documentation</Link></li>
                <li><Link to="/api" className="hover:text-white">API Reference</Link></li>
                <li><Link to="/help" className="hover:text-white">Help Center</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Legal</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/privacy" className="hover:text-white">Privacy Policy</Link></li>
                <li><Link to="/terms" className="hover:text-white">Terms of Service</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-white/10 pt-8 text-center text-sm">
            © 2024 CivicPulse. Built for smarter cities.
          </div>
        </div>
      </footer>
    </div>
  );
}