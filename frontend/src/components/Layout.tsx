import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import {
  LayoutDashboard, History, User, LogOut,
  ChevronRight, FileText, Shield,
  BarChart3, Clock, Apple, BadgeCheck, Database,
  QrCode, FileSearch, Settings, HelpCircle,
  Bell, Search, ChevronLeft, Menu, X
} from 'lucide-react';


interface LayoutProps {
  children: React.ReactNode;
}

interface NavSection {
  title?: string;
  items: {
    path?: string;
    icon: any;
    label: string;
    badge?: string | number;
    badgeColor?: string;
    dot?: string;
  }[];
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const user = (() => { try { return JSON.parse(localStorage.getItem('medlens_user') || '{}'); } catch { return {}; } })();

  const handleLogout = () => {
    localStorage.removeItem('medlens_token');
    localStorage.removeItem('medlens_user');
    navigate('/');
  };

  const navSections: NavSection[] = [
    {
      items: [
        { path: '/app', icon: LayoutDashboard, label: 'Dashboard' },
      ]
    },
    {
      title: 'Analysis',
      items: [
        { path: '/app', icon: FileText, label: 'Prescription Analyzer' },
        { path: '/history', icon: History, label: 'Analysis History' },
        { path: '/app?tab=report', icon: BarChart3, label: 'Clinical Reports' },
        { path: '/app?tab=timeline', icon: Clock, label: 'Dosage Timelines' },
      ]
    },
    {
      title: 'Clinical Intelligence',
      items: [
        { path: '/app?tab=interactions', icon: Shield, label: 'Drug Interactions', badge: 'Live', badgeColor: 'bg-red-50 text-red-500 border border-red-100' },
        { path: '/app?tab=dosage', icon: BadgeCheck, label: 'Dosage Validation' },
        { path: '/app?tab=food', icon: Apple, label: 'Dietary Restrictions' },
        { path: '/app?tab=insurance', icon: Database, label: 'Insurance Mapping', badge: 'CGHS', badgeColor: 'bg-blue-50 text-blue-600 border border-blue-100' },
      ]
    },
    {
      title: 'Patient',
      items: [
        { path: '/profile', icon: User, label: 'Identity Profile' },
        { path: '/profile#qr', icon: QrCode, label: 'Emergency Card', badge: 'QR', badgeColor: 'bg-violet-50 text-violet-600 border border-violet-100' },
        { path: '/history', icon: FileSearch, label: 'Prescription Vault' },
      ]
    },
    {
      title: 'System',
      items: [
        { path: '/settings', icon: Settings, label: 'Settings' },
        { path: '/help', icon: HelpCircle, label: 'Help & Support' },
      ]
    }
  ];

  const isActive = (path?: string) => {
    if (!path) return false;
    const cleanPath = path.split('?')[0];
    if (cleanPath === '/app') return location.pathname === '/app';
    return location.pathname.startsWith(cleanPath);
  };

  // Accent color per section
  const sectionAccent: Record<string, string> = {
    'Analysis': 'bg-blue-500',
    'Clinical Intelligence': 'bg-violet-500',
    'Patient': 'bg-emerald-500',
    'System': 'bg-gray-400',
  };

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className={`h-16 flex items-center border-b border-gray-100 shrink-0 ${sidebarCollapsed ? 'px-4 justify-center' : 'px-5 justify-between'}`}>
        {!sidebarCollapsed && (
          <Link to="/app" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl flex items-center justify-center bg-gradient-to-br from-violet-600 to-indigo-600 shadow-md shadow-violet-200">
              <span className="text-white font-black text-base leading-none">M</span>
            </div>
            <span className="font-bold text-gray-900 text-base tracking-tight">MedLens</span>
          </Link>
        )}
        <button
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="hidden lg:flex p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
        >
          {sidebarCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
        {sidebarCollapsed && (
          <div className="w-8 h-8 rounded-xl flex items-center justify-center bg-gradient-to-br from-violet-600 to-indigo-600 shadow-md shadow-violet-200">
            <span className="text-white font-black text-base leading-none">M</span>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-5">
        {navSections.map((section, si) => (
          <div key={si}>
            {section.title && !sidebarCollapsed && (
              <div className="flex items-center gap-2 px-2 mb-2">
                {section.title !== undefined && (
                  <div className={`w-1.5 h-1.5 rounded-full shrink-0 ${sectionAccent[section.title] || 'bg-gray-300'}`} />
                )}
                <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">
                  {section.title}
                </p>
              </div>
            )}
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const active = isActive(item.path);
                return (
                  <Link
                    key={item.label}
                    to={item.path || '#'}
                    onClick={() => setMobileOpen(false)}
                    title={sidebarCollapsed ? item.label : undefined}
                    className={`
                      flex items-center gap-2.5 rounded-xl transition-all duration-150 group relative
                      ${sidebarCollapsed ? 'px-2.5 py-2 justify-center' : 'px-2.5 py-2'}
                      ${active
                        ? 'bg-violet-50 text-violet-700'
                        : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'
                      }
                    `}
                  >
                    {active && (
                      <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-violet-500 rounded-r-full" />
                    )}
                    <item.icon className={`w-4 h-4 shrink-0 ${active ? 'text-violet-600' : 'text-gray-400 group-hover:text-gray-600'}`} />
                    {!sidebarCollapsed && (
                      <>
                        <span className={`text-sm font-medium flex-1 truncate ${active ? 'text-violet-700' : ''}`}>{item.label}</span>
                        {item.badge && (
                          <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-md ${item.badgeColor || 'bg-gray-100 text-gray-500'}`}>
                            {item.badge}
                          </span>
                        )}
                      </>
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* User Footer */}
      <div className={`shrink-0 border-t border-gray-100 p-3`}>
        {!sidebarCollapsed ? (
          <div
            className="flex items-center gap-3 p-2 rounded-xl hover:bg-gray-50 transition-colors group cursor-pointer"
            onClick={() => navigate('/profile')}
          >
            <div className="w-8 h-8 bg-gradient-to-br from-violet-500 to-indigo-500 rounded-full flex items-center justify-center shrink-0 shadow-sm">
              <span className="text-white text-xs font-bold">{(user.name || 'U').charAt(0).toUpperCase()}</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">{user.name || 'Clinician'}</p>
              <p className="text-xs text-gray-400 truncate">{user.email || 'Verified Account'}</p>
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); handleLogout(); }}
              className="p-1.5 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-lg opacity-0 group-hover:opacity-100 transition-all"
              title="Sign out"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <button
            onClick={handleLogout}
            title="Sign out"
            className="w-full flex justify-center p-2 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 font-sans text-gray-900 flex flex-col selection:bg-violet-100">
      {/* Top Header */}
      <header className="h-14 bg-white border-b border-gray-100 flex items-center justify-between px-4 lg:px-6 z-30 shrink-0 fixed inset-x-0 top-0 shadow-sm">
        <div className="flex items-center gap-3">
          <button
            className="lg:hidden p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          <div className="hidden sm:flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 w-64 focus-within:border-violet-300 focus-within:ring-2 focus-within:ring-violet-100 transition-all">
            <Search className="w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search analyses, drugs, patients..."
              className="bg-transparent text-sm text-gray-600 placeholder-gray-400 outline-none w-full"
            />
            <kbd className="text-[10px] bg-white border border-gray-200 text-gray-400 px-1.5 py-0.5 rounded font-mono">⌘K</kbd>
          </div>
        </div>

        <div className="flex items-center gap-1">
          {/* Notification bell → /notifications */}
          <button
            onClick={() => navigate('/notifications')}
            className="relative p-2 text-gray-400 hover:text-violet-600 hover:bg-violet-50 rounded-xl transition-colors"
          >
            <Bell className="w-5 h-5" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full ring-2 ring-white" />
          </button>

          <button
            onClick={() => navigate('/settings')}
            className="p-2 text-gray-400 hover:text-violet-600 hover:bg-violet-50 rounded-xl transition-colors"
          >
            <Settings className="w-5 h-5" />
          </button>

          <div className="h-5 w-px bg-gray-100 mx-1" />

          {/* Avatar → /profile */}
          <button
            onClick={() => navigate('/profile')}
            className="flex items-center gap-2.5 px-2 py-1.5 rounded-xl hover:bg-violet-50 transition-colors cursor-pointer"
          >
            <div className="w-7 h-7 bg-gradient-to-br from-violet-500 to-indigo-500 rounded-full flex items-center justify-center shadow-sm">
              <span className="text-white text-xs font-bold">{(user.name || 'U').charAt(0).toUpperCase()}</span>
            </div>
            <div className="hidden sm:block text-right">
              <p className="text-xs font-semibold text-gray-900 leading-none">{user.name || 'Clinician'}</p>
              <p className="text-[10px] text-gray-400 mt-0.5">Verified</p>
            </div>
          </button>
        </div>
      </header>

      <div className="flex flex-1 pt-14">
        {/* Mobile Overlay */}
        {mobileOpen && (
          <div
            className="lg:hidden fixed inset-0 bg-black/20 z-30 pt-14"
            onClick={() => setMobileOpen(false)}
          />
        )}

        {/* Sidebar */}
        <aside className={`
          fixed top-14 bottom-0 left-0 z-30 bg-white border-r border-gray-100 flex flex-col
          transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]
          ${sidebarCollapsed ? 'w-16' : 'w-60'}
          ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}>
          <SidebarContent />
        </aside>

        {/* Main Content */}
        <main className={`flex-1 flex flex-col min-h-[calc(100vh-3.5rem)] transition-all duration-300 ${sidebarCollapsed ? 'lg:pl-16' : 'lg:pl-60'}`}>
          <div className="flex-1 p-6 md:p-8 max-w-[1400px] w-full mx-auto">
            {children}
          </div>

          {/* Footer */}
          <footer className="border-t border-gray-100 bg-white px-8 py-4 flex flex-col sm:flex-row items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 rounded-lg bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center shadow-sm">
                <span className="text-white font-black text-[10px] leading-none">M</span>
              </div>
              <span className="text-xs text-gray-500 font-medium">MedLens Clinical Intelligence Platform</span>
              <span className="text-gray-200 mx-1">·</span>
              <span className="text-xs text-gray-400 font-mono">v2.4.1</span>
            </div>
            <p className="text-[11px] text-gray-400 text-center sm:text-right">
              Core Division: Partha Shankar Captain <span className="text-gray-300">·</span> Anupama B M <span className="text-gray-300">·</span> Maithri M <span className="text-gray-300">·</span> Nirmith M Jain
            </p>
          </footer>
        </main>
      </div>
    </div>
  );
};
