import React, { useState, useEffect, useRef } from 'react';
import { X, Send, AlertTriangle, MessageSquare } from 'lucide-react';

interface Medication { name: string; dose: string; frequency: string; indication: string; }
interface RxGuardPatient { name: string; age: number; gender: string; weight_kg: number; conditions: string[]; allergies: string[]; medications: Medication[]; renal_impairment: boolean; pregnant: boolean; notes: string; }
interface Message { role: 'user' | 'assistant'; content: string; requiresDoctor?: boolean; followUp?: string; }
interface Props { rxguardPatient: RxGuardPatient; prescriptionSummary: string; onClose: () => void; }

const SUGGESTIONS = ['Is it safe to take all these together?', 'What foods should I avoid?', 'Explain the main side effects.'];

const RxGuardChat: React.FC<Props> = ({ rxguardPatient, prescriptionSummary, onClose }) => {
  const [messages, setMessages] = useState<Message[]>([{
    role: 'assistant',
    content: `Hello${rxguardPatient.name ? `, ${rxguardPatient.name}` : ''}. I've reviewed the prescription containing ${rxguardPatient.medications?.length || 0} medications. How can I help you?`
  }]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, loading]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || loading) return;
    setMessages(prev => [...prev, { role: 'user', content: text }]);
    setInput('');
    setLoading(true);
    setShowSuggestions(false);
    const history = messages.slice(1, 11).map(m => ({ role: m.role, content: m.content }));

    try {
      const res = await fetch(`${import.meta.env.VITE_RXGUARD_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text, language: 'Auto-detect', patient: rxguardPatient, history }),
      });
      if (!res.ok) throw new Error();
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.answer, requiresDoctor: data.requires_doctor, followUp: data.follow_up }]);
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'The advisory service is temporarily unavailable. Please try again shortly.' }]);
    } finally { setLoading(false); }
  };

  return (
    <div className="fixed right-0 top-0 bottom-0 w-full sm:w-[420px] bg-white border-l border-gray-200 shadow-2xl z-50 flex flex-col font-sans">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 bg-white shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-gray-900 rounded-xl flex items-center justify-center">
            <MessageSquare className="w-4.5 h-4.5 text-white" />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-900">Clinical Consultant</p>
            <p className="text-xs text-gray-400">Prescription-aware advisory</p>
          </div>
        </div>
        <button onClick={onClose} className="p-1.5 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Context bar */}
      <div className="px-5 py-3 bg-gray-50 border-b border-gray-100 shrink-0">
        <p className="text-xs text-gray-500 font-medium">Context: {prescriptionSummary}</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.map((m, i) => (
          <div key={i} className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}>
            <div className={`max-w-[85%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
              m.role === 'user'
                ? 'bg-gray-900 text-white rounded-tr-sm'
                : 'bg-gray-100 text-gray-800 rounded-tl-sm'
            }`}>
              {m.content}
            </div>
            {m.requiresDoctor && (
              <div className="mt-1.5 flex items-center gap-1.5 text-[11px] text-amber-700 bg-amber-50 border border-amber-200 px-3 py-1.5 rounded-lg">
                <AlertTriangle className="w-3 h-3" /> Consult your physician before acting on this.
              </div>
            )}
            {m.followUp && <p className="text-[11px] text-gray-400 mt-1 px-1 italic">{m.followUp}</p>}
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-1.5 bg-gray-100 px-4 py-3 rounded-2xl rounded-tl-sm w-fit">
            {[0, 150, 300].map(d => <div key={d} className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: `${d}ms` }} />)}
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Suggestions */}
      {showSuggestions && (
        <div className="px-4 pb-3 flex flex-wrap gap-2 shrink-0">
          {SUGGESTIONS.map((s, i) => (
            <button key={i} onClick={() => sendMessage(s)} className="text-xs px-3 py-1.5 border border-gray-200 rounded-full text-gray-600 hover:border-gray-400 hover:bg-gray-50 transition-all">
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-gray-100 shrink-0 bg-white">
        <div className="flex items-end gap-2">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage(input)}
            placeholder="Ask about your medications..."
            disabled={loading}
            className="flex-1 border border-gray-200 rounded-xl px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent transition-all resize-none"
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={loading || !input.trim()}
            className="p-3 bg-gray-900 text-white rounded-xl hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default RxGuardChat;
