import React, { useRef, useState } from 'react';
import {
  AlertCircle,
  Eye,
  EyeOff,
  Lock,
  ShieldCheck,
  User,
  ArrowRight
} from 'lucide-react';
import { api } from '../api/client';
import { AuthTokenResponse, UserRole } from '../types';
import { ProvenanceBadge } from '../components/common/ProvenanceBadge';

interface LoginPageProps {
  onLoginSuccess: (auth: AuthTokenResponse) => void;
}

interface DemoAccount {
  username: string;
  password: string;
  fullName: string;
  role: UserRole;
  responsibility: string;
}

const DEMO_ACCOUNTS: DemoAccount[] = [
  {
    username: 'operator',
    password: 'operator123',
    fullName: 'John Doe (Shift Operator)',
    role: 'OPERATOR',
    responsibility: 'Approve/reject simulated load shutdowns & restarts'
  },
  {
    username: 'energymgr',
    password: 'energy123',
    fullName: 'Sarah Jenkins (Plant Energy Manager)',
    role: 'ENERGY_MANAGER',
    responsibility: 'Idle loss review, savings baselines & pilot reports'
  },
  {
    username: 'maintenance',
    password: 'maint123',
    fullName: 'Carlos Gomez (Electrical Maintenance)',
    role: 'MAINTENANCE',
    responsibility: 'Sensor validation, alerts & safety interlock verification'
  },
  {
    username: 'admin',
    password: 'admin123',
    fullName: 'Admin System Controller',
    role: 'ADMIN',
    responsibility: 'Site thresholds, tariff config & governance settings'
  }
];

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string>('');

  const usernameRef = useRef<HTMLInputElement>(null);
  const submitButtonRef = useRef<HTMLButtonElement>(null);

  const handleUsernameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUsername(e.target.value);
    if (errorMessage) setErrorMessage('');
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPassword(e.target.value);
    if (errorMessage) setErrorMessage('');
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (isSubmitting) return;

    const trimmedUser = username.trim();
    if (!trimmedUser || !password) {
      setErrorMessage('Please enter both your username and password.');
      usernameRef.current?.focus();
      return;
    }

    setIsSubmitting(true);
    setErrorMessage('');

    try {
      const response = await api.login(trimmedUser, password);
      onLoginSuccess(response);
    } catch (err: any) {
      setErrorMessage(err?.message || 'Invalid username or password. Please try again.');
      usernameRef.current?.focus();
    } finally {
      setIsSubmitting(false);
    }
  };

  const handlePrefillDemo = (account: DemoAccount) => {
    setUsername(account.username);
    setPassword(account.password);
    setErrorMessage('');
    submitButtonRef.current?.focus();
  };

  return (
    <div className="min-h-screen bg-white text-slate-800 flex flex-col font-sans selection:bg-emerald-100 selection:text-emerald-900">
      {/* Main White Sign-In Workspace */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 py-8 sm:py-12 bg-slate-50/40">
        <div className="w-full max-w-md space-y-6">
          {/* Brand Header */}
          <div className="flex flex-col items-center text-center space-y-2">
            <div className="w-12 h-12 rounded-xl bg-emerald-700 flex items-center justify-center text-white shadow-sm font-bold text-lg tracking-wider">
              PP
            </div>
            <div>
              <div className="flex items-center justify-center gap-2">
                <h1 className="text-2xl font-bold text-slate-900 tracking-tight">PLANTPULSE</h1>
                <span className="text-[10px] bg-emerald-100 text-emerald-800 font-mono font-semibold px-2 py-0.5 rounded">
                  v1.0-PROTOTYPE
                </span>
              </div>
              <p className="text-xs text-slate-600 mt-1">
                Intelligent Industrial Energy Optimisation for Sustainable Manufacturing
              </p>
            </div>
          </div>

          {/* Primary Sign-In Card */}
          <section
            aria-labelledby="signin-heading"
            className="bg-white border border-slate-200 rounded-2xl shadow-sm p-6 sm:p-7"
          >
            <div className="flex items-center justify-between pb-4 mb-5 border-b border-slate-100">
              <div>
                <h2 id="signin-heading" className="text-base font-bold text-slate-900">
                  Operator &amp; Engineering Sign In
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Role-based access to simulated feeder telemetry &amp; controls
                </p>
              </div>
              <ShieldCheck className="w-5 h-5 text-emerald-700 shrink-0" aria-hidden="true" />
            </div>

            <form
              method="post"
              onSubmit={handleSubmit}
              aria-labelledby="signin-heading"
              className="space-y-5"
            >
              {/* Inline Live Error Region */}
              {errorMessage && (
                <div
                  id="login-error"
                  role="alert"
                  aria-live="polite"
                  className="bg-red-50 border border-red-300 text-red-800 rounded-lg px-3.5 py-2.5 text-xs font-medium flex items-start gap-2"
                >
                  <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" aria-hidden="true" />
                  <span>{errorMessage}</span>
                </div>
              )}

              {/* Username Field */}
              <div className="flex flex-col gap-1.5">
                <label
                  htmlFor="username"
                  className="text-sm font-semibold text-slate-800 flex items-center gap-1"
                >
                  <span>Username</span>
                  <span className="text-red-600" aria-hidden="true">*</span>
                </label>
                <div className="relative">
                  <User
                    className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none"
                    aria-hidden="true"
                  />
                  <input
                    ref={usernameRef}
                    id="username"
                    name="username"
                    type="text"
                    autoComplete="username"
                    spellCheck={false}
                    autoCorrect="off"
                    autoCapitalize="none"
                    enterKeyHint="next"
                    required
                    value={username}
                    onChange={handleUsernameChange}
                    aria-invalid={Boolean(errorMessage)}
                    aria-describedby={errorMessage ? 'login-error username-hint' : 'username-hint'}
                    placeholder="e.g. operator"
                    className="w-full min-h-12 text-base pl-10 pr-3.5 py-2.5 bg-white text-slate-900 border border-slate-400 rounded-lg placeholder:text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-700 focus-visible:border-emerald-700"
                  />
                </div>
                <span id="username-hint" className="text-[11px] text-slate-500">
                  Enter your assigned role username or pick a demo role below.
                </span>
              </div>

              {/* Password Field */}
              <div className="flex flex-col gap-1.5">
                <label
                  htmlFor="password"
                  className="text-sm font-semibold text-slate-800 flex items-center gap-1"
                >
                  <span>Password</span>
                  <span className="text-red-600" aria-hidden="true">*</span>
                </label>
                <div className="relative flex items-center">
                  <Lock
                    className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none"
                    aria-hidden="true"
                  />
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    enterKeyHint="done"
                    required
                    value={password}
                    onChange={handlePasswordChange}
                    aria-invalid={Boolean(errorMessage)}
                    aria-describedby={errorMessage ? 'login-error' : undefined}
                    placeholder="Enter password"
                    className="w-full min-h-12 text-base pl-10 pr-12 py-2.5 bg-white text-slate-900 border border-slate-400 rounded-lg placeholder:text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-700 focus-visible:border-emerald-700"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(prev => !prev)}
                    aria-pressed={showPassword}
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                    className="absolute right-1.5 top-1/2 -translate-y-1/2 min-w-11 min-h-11 flex items-center justify-center rounded-md text-slate-600 hover:text-slate-900 hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-700"
                  >
                    {showPassword ? (
                      <EyeOff className="w-4 h-4" aria-hidden="true" />
                    ) : (
                      <Eye className="w-4 h-4" aria-hidden="true" />
                    )}
                  </button>
                </div>
              </div>

              {/* Submit Button */}
              <button
                ref={submitButtonRef}
                type="submit"
                disabled={isSubmitting}
                className="w-full min-h-12 px-4 py-3 bg-emerald-700 hover:bg-emerald-800 disabled:bg-emerald-400 text-white text-sm font-bold rounded-lg shadow-xs transition-colors flex items-center justify-center gap-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-emerald-700 cursor-pointer"
              >
                <span>{isSubmitting ? 'Signing In...' : 'Sign In'}</span>
                {!isSubmitting && <ArrowRight className="w-4 h-4" aria-hidden="true" />}
              </button>
            </form>
          </section>

          {/* Demo Role Credentials Reference (placed below form for mobile keyboard ergonomics) */}
          <section
            aria-labelledby="demo-roles-heading"
            className="bg-white border border-slate-200 rounded-2xl p-5 space-y-3"
          >
            <div className="flex items-center justify-between gap-2">
              <h3 id="demo-roles-heading" className="text-xs font-bold uppercase tracking-wider text-slate-700">
                Demonstration Accounts (Click to Autofill)
              </h3>
              <ProvenanceBadge type="SIMULATED" size="xs" />
            </div>

            <div className="grid grid-cols-1 gap-2">
              {DEMO_ACCOUNTS.map(account => {
                const isSelected = username === account.username;
                return (
                  <button
                    key={account.username}
                    type="button"
                    onClick={() => handlePrefillDemo(account)}
                    className={`w-full min-h-12 text-left px-3.5 py-2.5 rounded-lg border transition-colors flex items-center justify-between gap-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-700 ${
                      isSelected
                        ? 'bg-emerald-50 border-emerald-400'
                        : 'bg-slate-50/60 border-slate-200 hover:bg-slate-100/70'
                    }`}
                  >
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-900 truncate">
                          {account.fullName}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-600 truncate mt-0.5">
                        {account.responsibility}
                      </div>
                    </div>
                    <div className="shrink-0 text-right">
                      <span className="inline-block font-mono text-[11px] font-semibold bg-white border border-slate-300 text-slate-800 px-2 py-0.5 rounded">
                        {account.username} / {account.password}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          </section>
        </div>
      </main>
    </div>
  );
};
