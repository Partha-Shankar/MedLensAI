import React from 'react';
import { Pill, User, LogOut, History, LogIn } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

interface Props {
  patientName: string;
  onNavigate: (state: string) => void;
  currentState: string;
}

export function NavigationBar({ patientName, onNavigate, currentState }: Props) {
  const { user, isLoggedIn, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <nav className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between sticky top-0 z-50">
      <div className="flex items-center gap-2 cursor-pointer" onClick={() => {
        if (window.location.pathname !== '/') {
          navigate('/');
        } else {
          onNavigate('landing');
        }
      }}>
        <div className="bg-indigo-600 w-8 h-8 rounded-lg flex items-center justify-center">
          <Pill className="w-5 h-5 text-white" />
        </div>
        <span className="font-bold text-xl text-slate-900 tracking-tight">MedLens AI</span>
      </div>

      <div className="flex items-center gap-4">
        {patientName && (
          <div className="hidden md:flex text-sm font-medium text-slate-600 bg-slate-100 px-3 py-1.5 rounded-full">
            Patient: <span className="text-slate-900 ml-1">{patientName}</span>
          </div>
        )}
        
        {isLoggedIn ? (
          <div className="flex items-center gap-2 md:gap-4">
            <button 
              onClick={() => navigate('/profile')}
              className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg hover:bg-slate-100 transition-colors"
              title="View Profile"
            >
              <User className="w-4 h-4 text-slate-400" />
              <span className="text-sm font-medium text-slate-700">{user?.name}</span>
            </button>
            <button 
              onClick={() => navigate('/history')}
              className="flex items-center gap-2 text-sm font-semibold text-slate-600 hover:text-indigo-600 px-3 py-1.5 rounded-lg transition-colors"
            >
              <History className="w-4 h-4" />
              <span className="hidden sm:inline">History</span>
            </button>
            <button 
              onClick={logout}
              className="flex items-center gap-2 text-sm font-semibold text-red-600 hover:text-red-700 px-3 py-1.5 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        ) : (
          <button 
            onClick={() => navigate('/login')}
            className="flex items-center gap-2 text-sm font-bold text-indigo-600 hover:text-indigo-700 bg-indigo-50 px-5 py-2 rounded-xl transition-all"
          >
            <LogIn className="w-4 h-4" />
            Sign In
          </button>
        )}
      </div>
    </nav>
  );
}
