import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Mail, Lock, AlertTriangle, Shield, ArrowRight } from 'lucide-react';


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Invalid credentials. Please verify and retry.');
      }

      const data = await response.json();
      localStorage.setItem('medlens_token', data.token);
      localStorage.setItem('medlens_user', JSON.stringify(data.user));
      navigate('/app');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white font-sans selection:bg-violet-100 flex">
      {/* Left Panel */}
      <div className="hidden lg:flex lg:w-1/2 xl:w-2/5 flex-col bg-gray-950 p-12 relative overflow-hidden">
        {/* Gradient blobs */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_70%_60%_at_30%_70%,rgba(139,92,246,0.18),transparent)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_50%_40%_at_80%_20%,rgba(99,102,241,0.12),transparent)]" />

        <Link to="/" className="relative z-10 flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-violet-500 to-indigo-500 flex items-center justify-center shadow-lg shadow-violet-900/30">
            <span className="text-white font-black text-base leading-none">M</span>
          </div>
          <span className="text-white font-bold text-lg tracking-tight">MedLens</span>
        </Link>

        <div className="flex-1 flex flex-col justify-center relative z-10">
          <div className="mb-8">
            <div className="inline-flex items-center gap-2 bg-violet-500/15 border border-violet-500/20 rounded-full px-3 py-1.5 mb-6">
              <Shield className="w-3.5 h-3.5 text-violet-400" />
              <span className="text-xs text-violet-300 font-medium">Secure Access</span>
            </div>
            <h2 className="text-4xl font-bold text-white tracking-tight leading-tight mb-4">
              Smarter prescriptions.<br />Safer patients.
            </h2>
            <p className="text-gray-400 text-sm leading-relaxed max-w-sm">
              India's first AI-powered prescription safety tool — built for patients, pharmacists, and clinicians.
            </p>
          </div>

          <div className="space-y-3.5 max-w-sm">
            {[
              { emoji: '📷', text: 'Reads handwritten prescriptions instantly' },
              { emoji: '⚠️', text: 'Checks 54,000+ drug interaction pairs' },
              { emoji: '💊', text: 'Shows PMJAY/CGHS insurance coverage & generic savings' },
              { emoji: '🔒', text: 'Secure health locker with emergency QR card' },
            ].map((item, i) => (
              <div key={i} className="flex items-center gap-3 bg-white/5 border border-white/8 rounded-xl px-4 py-3">
                <span className="text-lg leading-none">{item.emoji}</span>
                <span className="text-sm text-gray-300 leading-snug">{item.text}</span>
              </div>
            ))}
          </div>
        </div>

        <p className="relative z-10 text-xs text-gray-600">
          Core Division: Partha Shankar Captain · Anupama B M · Maithri M · Nirmith M Jain
        </p>
      </div>

      {/* Right Panel */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          {/* Mobile logo */}
          <Link to="/" className="lg:hidden flex items-center gap-2.5 mb-10">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center shadow-md shadow-violet-200">
              <span className="text-white font-black text-base leading-none">M</span>
            </div>
            <span className="text-gray-900 font-bold text-lg">MedLens</span>
          </Link>

          <div className="mb-8">
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight mb-1.5">Welcome back</h1>
            <p className="text-sm text-gray-500">Sign in to your clinical workspace.</p>
          </div>

          {error && (
            <div className="mb-6 flex items-start gap-3 p-4 bg-red-50 border border-red-100 rounded-xl text-red-600">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
              <p className="text-sm">{error}</p>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Email address</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-white border border-gray-200 rounded-xl text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent transition-all"
                  placeholder="you@hospital.org"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-sm font-medium text-gray-700">Password</label>
                <a href="#" className="text-xs text-gray-500 hover:text-gray-700 transition-colors">Forgot password?</a>
              </div>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-white border border-gray-200 rounded-xl text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent transition-all"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-gray-900 text-white py-3 rounded-xl text-sm font-semibold hover:bg-gray-800 transition-all disabled:opacity-60 disabled:cursor-not-allowed shadow-sm hover:shadow mt-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Authenticating...
                </>
              ) : (
                <>
                  Sign In <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-gray-100 text-center">
            <p className="text-sm text-gray-500">
              New to MedLens?{' '}
              <Link to="/signup" className="text-gray-900 font-semibold hover:underline">
                Request access
              </Link>
            </p>
          </div>

          <div className="mt-8 flex items-center gap-2 justify-center">
            <Shield className="w-3.5 h-3.5 text-gray-300" />
            <p className="text-xs text-gray-400">256-bit encrypted · HIPAA aligned</p>
          </div>
        </div>
      </div>
    </div>
  );
};
