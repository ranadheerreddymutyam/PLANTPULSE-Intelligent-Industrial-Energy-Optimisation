import React from 'react';
import {
  LayoutDashboard,
  Cpu,
  Clock,
  Zap,
  ShieldAlert,
  TrendingDown,
  AlertTriangle,
  FileText,
  Upload,
  Settings,
  Menu,
  X
} from 'lucide-react';

export type PageId =
  | 'dashboard'
  | 'equipment'
  | 'idle'
  | 'optimisation'
  | 'control'
  | 'savings'
  | 'events'
  | 'reports'
  | 'import'
  | 'settings';

interface SidebarProps {
  currentPage: PageId;
  onPageChange: (page: PageId) => void;
  pendingApprovalsCount?: number;
  activeEventsCount?: number;
  mobileOpen: boolean;
  onMobileToggle: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onPageChange,
  pendingApprovalsCount = 0,
  activeEventsCount = 0,
  mobileOpen,
  onMobileToggle
}) => {
  const menuItems: Array<{
    id: PageId;
    label: string;
    icon: React.ReactNode;
    badge?: number;
    badgeColor?: string;
  }> = [
    {
      id: 'dashboard',
      label: '1. Dashboard',
      icon: <LayoutDashboard className="w-4 h-4" />
    },
    {
      id: 'equipment',
      label: '2. Equipment Monitoring',
      icon: <Cpu className="w-4 h-4" />
    },
    {
      id: 'idle',
      label: '3. Idle Analysis',
      icon: <Clock className="w-4 h-4" />
    },
    {
      id: 'optimisation',
      label: '4. Optimisation & Recom.',
      icon: <Zap className="w-4 h-4" />
    },
    {
      id: 'control',
      label: '5. Control & Safety (SIM)',
      icon: <ShieldAlert className="w-4 h-4" />,
      badge: pendingApprovalsCount,
      badgeColor: 'bg-amber-100 text-amber-800'
    },
    {
      id: 'savings',
      label: '6. Savings & Baseline',
      icon: <TrendingDown className="w-4 h-4" />
    },
    {
      id: 'events',
      label: '7. Event History & Alerts',
      icon: <AlertTriangle className="w-4 h-4" />,
      badge: activeEventsCount,
      badgeColor: 'bg-red-100 text-red-800'
    },
    {
      id: 'reports',
      label: '8. Reports & Pilot Plan',
      icon: <FileText className="w-4 h-4" />
    },
    {
      id: 'import',
      label: '9. Data Import',
      icon: <Upload className="w-4 h-4" />
    },
    {
      id: 'settings',
      label: '10. Settings & Governance',
      icon: <Settings className="w-4 h-4" />
    }
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-slate-900/50 z-40 lg:hidden"
          onClick={onMobileToggle}
        />
      )}

      {/* Sidebar container */}
      <aside
        className={`fixed lg:static top-0 bottom-0 left-0 z-40 w-64 bg-white border-r border-slate-200 flex flex-col justify-between transition-transform duration-200 ease-in-out ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="p-4 space-y-4">
          <div className="flex items-center justify-between lg:hidden border-b border-slate-100 pb-3">
            <span className="font-bold text-slate-800 text-sm">Navigation</span>
            <button
              onClick={onMobileToggle}
              className="p-1 rounded-md text-slate-500 hover:bg-slate-100"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <nav className="space-y-1">
            <div className="px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-slate-400">
              System Modules (10 Pages)
            </div>
            {menuItems.map(item => {
              const isActive = currentPage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    onPageChange(item.id);
                    if (mobileOpen) onMobileToggle();
                  }}
                  className={`w-full flex items-center justify-between px-3 py-2 text-xs font-semibold rounded-lg transition-colors text-left ${
                    isActive
                      ? 'bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  }`}
                >
                  <span className="flex items-center gap-2.5">
                    <span className={isActive ? 'text-emerald-700' : 'text-slate-400'}>
                      {item.icon}
                    </span>
                    <span>{item.label}</span>
                  </span>
                  {item.badge !== undefined && item.badge > 0 && (
                    <span
                      className={`text-[10px] font-mono px-1.5 py-0.5 rounded-full font-bold ${
                        item.badgeColor || 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Challenge Footer Info */}
        <div className="p-4 border-t border-slate-100 bg-slate-50/50 space-y-2 text-xs">
          <div className="text-[11px] font-semibold text-slate-700">L'Oréal Sustainability Challenge</div>
          <div className="text-[10px] text-slate-500">Track: Option 03 — Less Waste, Smarter Resource Use</div>
          <div className="pt-1 text-[10px] font-mono text-emerald-800 font-medium">Target: Avoidable Idle Electricity</div>
        </div>
      </aside>
    </>
  );
};
