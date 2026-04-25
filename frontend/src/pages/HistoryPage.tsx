import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Calendar, User, Clock, Loader2, AlertCircle, FileSearch, CheckCircle2, ShieldAlert, MessageSquare, Plus } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
interface Medication { DrugName: string; DoseValue: string; DoseUnit: string; Frequency: string; Duration: string; }
interface PrescriptionRecord { id: number; patient_name: string; patient_age: string; prescriber: string; prescription_date: string; medications: Medication[]; interactions: any[]; validity_score: string; overall_confidence: number; image_thumbnail_b64: string; created_at: string; }

export const HistoryPage: React.FC = () => {
  const [history, setHistory] = useState<PrescriptionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchHistory = async () => {
      const token = localStorage.getItem('medlens_token');
      if (!token) { navigate('/login'); return; }
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/history`, { headers: { 'Authorization': `Bearer ${token}` } });
        if (!response.ok) throw new Error('Failed to load history.');
        setHistory(await response.json());
      } catch (err: any) { setError(err.message); }
      finally { setLoading(false); }
    };
    fetchHistory();
  }, [navigate]);

  if (loading) return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="text-center"><Loader2 className="w-8 h-8 text-gray-400 animate-spin mx-auto mb-3" /><p className="text-sm text-gray-500">Loading analysis history...</p></div>
    </div>
  );

  return (
    <div className="space-y-6 animate-fadeSlideUp">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900 tracking-tight">Analysis History</h1>
          <p className="text-sm text-gray-500 mt-1">All previous prescription analyses, securely stored.</p>
        </div>
        <button onClick={() => navigate('/app')} className="flex items-center gap-2 bg-gray-900 text-white px-4 py-2.5 rounded-xl text-sm font-semibold hover:bg-gray-800 transition-colors shadow-sm">
          <Plus className="w-4 h-4" /> New analysis
        </button>
      </div>

      {error ? (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-8 text-center">
          <AlertCircle className="w-10 h-10 text-red-400 mx-auto mb-3" />
          <p className="text-sm font-semibold text-red-700">Failed to load history</p>
          <p className="text-xs text-red-500 mt-1">{error}</p>
        </div>
      ) : history.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-2xl p-16 text-center shadow-sm">
          <FileSearch className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-base font-semibold text-gray-900 mb-1">No analyses yet</h3>
          <p className="text-sm text-gray-500 mb-6 max-w-sm mx-auto">Upload your first prescription to build your analysis history.</p>
          <button onClick={() => navigate('/app')} className="bg-gray-900 text-white px-5 py-2.5 rounded-xl text-sm font-semibold hover:bg-gray-800 transition-colors">
            Start first analysis
          </button>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {history.map(record => <HistoryCard key={record.id} record={record} />)}
        </div>
      )}
    </div>
  );
};

const HistoryCard: React.FC<{ record: PrescriptionRecord }> = ({ record }) => {
  const navigate = useNavigate();
  const conflicts = record.interactions?.length || 0;

  return (
    <div className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden hover:border-gray-300 hover:shadow-md transition-all group">
      {/* Thumbnail */}
      <div className="h-36 bg-gray-50 border-b border-gray-100 relative overflow-hidden flex items-center justify-center">
        {record.image_thumbnail_b64
          ? <img src={record.image_thumbnail_b64} alt="Prescription" className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 opacity-80" />
          : <FileText className="w-10 h-10 text-gray-300" />
        }
        <div className="absolute top-3 left-3 flex gap-1.5">
          <span className={`flex items-center gap-1 text-[10px] font-semibold px-2 py-1 rounded-md ${conflicts > 0 ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-700'}`}>
            {conflicts > 0 ? <ShieldAlert className="w-3 h-3" /> : <CheckCircle2 className="w-3 h-3" />}
            {conflicts > 0 ? `${conflicts} conflict${conflicts > 1 ? 's' : ''}` : 'Clear'}
          </span>
        </div>
        <div className="absolute top-3 right-3">
          <span className="text-[10px] font-semibold bg-white border border-gray-200 text-gray-600 px-2 py-1 rounded-md">{record.validity_score}</span>
        </div>
      </div>

      <div className="p-4 space-y-3">
        <div className="flex items-start justify-between">
          <div className="min-w-0">
            <h3 className="text-sm font-semibold text-gray-900 truncate group-hover:text-violet-700 transition-colors">{record.patient_name || 'Unknown patient'}</h3>
            <p className="text-xs text-gray-400 mt-0.5 flex items-center gap-1"><Calendar className="w-3 h-3" />{new Date(record.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}</p>
          </div>
          <div className="shrink-0 text-right bg-gray-50 border border-gray-100 px-2 py-1 rounded-lg">
            <p className="text-base font-bold text-gray-900">{record.medications?.length || 0}</p>
            <p className="text-[9px] text-gray-400 font-semibold uppercase tracking-wider">Meds</p>
          </div>
        </div>

        <div className="space-y-1.5">
          <div className="flex items-center gap-2 text-xs text-gray-500"><User className="w-3.5 h-3.5 text-gray-300" /><span className="truncate">Dr. {record.prescriber || 'Unknown'}</span></div>
          <div className="flex items-center gap-2 text-xs text-gray-500"><Clock className="w-3.5 h-3.5 text-gray-300" /><span>Age: {record.patient_age || '—'}</span></div>
        </div>

        <div className="pt-3 border-t border-gray-100">
          <button
            onClick={() => navigate('/app', { state: { openChat: true, prescription: { ...record, Medications: record.medications } } })}
            className="w-full flex items-center justify-center gap-1.5 text-xs font-semibold text-gray-600 hover:text-gray-900 bg-gray-50 hover:bg-gray-100 border border-gray-200 py-2 rounded-lg transition-all"
          >
            <MessageSquare className="w-3.5 h-3.5" /> Ask Clinical Consultant
          </button>
        </div>
      </div>
    </div>
  );
};
