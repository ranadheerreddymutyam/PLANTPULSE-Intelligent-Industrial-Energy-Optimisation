import React, { useState, useEffect } from 'react';
import { HeaderBanner } from './components/common/HeaderBanner';
import { Sidebar, PageId } from './components/common/Sidebar';
import { DashboardPage } from './pages/DashboardPage';
import { EquipmentMonitoringPage } from './pages/EquipmentMonitoringPage';
import { IdleAnalysisPage } from './pages/IdleAnalysisPage';
import { OptimisationPage } from './pages/OptimisationPage';
import { ControlSafetyPage } from './pages/ControlSafetyPage';
import { SavingsBaselinePage } from './pages/SavingsBaselinePage';
import { EventsAlertsPage } from './pages/EventsAlertsPage';
import { ReportsPage } from './pages/ReportsPage';
import { DataImportPage } from './pages/DataImportPage';
import { SettingsPage } from './pages/SettingsPage';
import { LoginPage } from './pages/LoginPage';
import { AuthTokenResponse, AuthUser, UserRole } from './types';
import { api } from './api/client';
import { Menu } from 'lucide-react';

const AUTH_STORAGE_KEY = 'plantpulse_auth_session';

function loadStoredSession(): { user: AuthUser; role: UserRole } | null {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (parsed?.user?.username && parsed?.user?.role && parsed?.access_token) {
      return { user: parsed.user as AuthUser, role: parsed.user.role as UserRole };
    }
  } catch {
    // ignore malformed storage
  }
  return null;
}

export const App: React.FC = () => {
  const initialSession = loadStoredSession();
  const [authUser, setAuthUser] = useState<AuthUser | null>(initialSession?.user ?? null);
  const [currentPage, setCurrentPage] = useState<PageId>('dashboard');
  const [currentRole, setCurrentRole] = useState<UserRole>(initialSession?.role ?? 'OPERATOR');
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState<boolean>(false);
  const [pendingApprovalsCount, setPendingApprovalsCount] = useState<number>(0);
  const [activeEventsCount, setActiveEventsCount] = useState<number>(0);
  const [refreshTrigger, setRefreshTrigger] = useState<number>(0);

  useEffect(() => {
    if (authUser) {
      loadBadgeCounts();
    }
  }, [refreshTrigger, authUser]);

  const loadBadgeCounts = async () => {
    try {
      const [apps, evts] = await Promise.all([
        api.listApprovals('PENDING'),
        api.listEvents({ status: 'ACTIVE' })
      ]);
      setPendingApprovalsCount(apps.length);
      setActiveEventsCount(evts.length);
    } catch {
      // ignore
    }
  };

  const handleLoginSuccess = (auth: AuthTokenResponse) => {
    try {
      localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(auth));
    } catch {
      // ignore storage failure
    }
    setAuthUser(auth.user);
    setCurrentRole(auth.user.role);
    setCurrentPage('dashboard');
    setRefreshTrigger(prev => prev + 1);
  };

  const handleLogout = () => {
    try {
      localStorage.removeItem(AUTH_STORAGE_KEY);
    } catch {
      // ignore
    }
    setAuthUser(null);
    setCurrentPage('dashboard');
    setMobileSidebarOpen(false);
  };

  const handleScenarioSwitched = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  if (!authUser) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="min-h-screen bg-white text-slate-800 flex flex-col font-sans selection:bg-emerald-100 selection:text-emerald-900">
      {/* Topmost persistent banner and navbar */}
      <HeaderBanner
        currentRole={currentRole}
        onRoleChange={setCurrentRole}
        onScenarioSwitched={handleScenarioSwitched}
        authenticatedUser={authUser}
        onLogout={handleLogout}
      />

      {/* Main Layout: Left Sidebar + White Canvas Area */}
      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          currentPage={currentPage}
          onPageChange={setCurrentPage}
          pendingApprovalsCount={pendingApprovalsCount}
          activeEventsCount={activeEventsCount}
          mobileOpen={mobileSidebarOpen}
          onMobileToggle={() => setMobileSidebarOpen(!mobileSidebarOpen)}
        />

        {/* Content Area */}
        <main className="flex-1 overflow-y-auto bg-white p-4 sm:p-6 lg:p-8">
          {/* Mobile top bar to toggle sidebar */}
          <div className="lg:hidden flex items-center justify-between pb-4 mb-4 border-b border-slate-100">
            <button
              onClick={() => setMobileSidebarOpen(true)}
              className="flex items-center gap-2 text-xs font-bold text-slate-700 bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200"
            >
              <Menu className="w-4 h-4" />
              Menu (10 Pages)
            </button>
            <span className="text-xs font-bold text-emerald-800 uppercase tracking-wider">
              {currentPage.toUpperCase()}
            </span>
          </div>

          <div key={`${currentPage}-${refreshTrigger}`} className="max-w-7xl mx-auto">
            {currentPage === 'dashboard' && <DashboardPage onNavigate={setCurrentPage} />}
            {currentPage === 'equipment' && <EquipmentMonitoringPage />}
            {currentPage === 'idle' && <IdleAnalysisPage />}
            {currentPage === 'optimisation' && <OptimisationPage />}
            {currentPage === 'control' && <ControlSafetyPage currentRole={currentRole} />}
            {currentPage === 'savings' && <SavingsBaselinePage />}
            {currentPage === 'events' && <EventsAlertsPage currentRole={currentRole} />}
            {currentPage === 'reports' && <ReportsPage />}
            {currentPage === 'import' && <DataImportPage />}
            {currentPage === 'settings' && <SettingsPage />}
          </div>
        </main>
      </div>
    </div>
  );
};

export default App;
