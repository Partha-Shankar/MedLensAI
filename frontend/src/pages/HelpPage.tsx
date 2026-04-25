import React, { useState } from 'react';
import { Search, ChevronRight, MessageCircle, Mail, BookOpen, Shield, Pill, Camera, Clock, CreditCard } from 'lucide-react';


const faqs = [
  {
    question: 'How do I upload a prescription?',
    answer: 'Go to Prescription Analyzer from the sidebar. Click "Browse files" or drag and drop your prescription image (JPG, PNG, PDF). The AI will read it automatically.',
  },
  {
    question: 'What if a drug name is read incorrectly?',
    answer: 'After extraction, you\'ll see a Confirmation screen. Low-confidence drugs show 3 alternative suggestions to pick from. You can also type the correct name manually.',
  },
  {
    question: 'How does the insurance check work?',
    answer: 'MedLens checks each drug against PMJAY, CGHS, and ESI formularies. It shows whether the drug is covered, needs prior authorisation, or is not covered — plus the price difference with generics.',
  },
  {
    question: 'What is the Emergency QR Card?',
    answer: 'It\'s a public link to your medical summary (blood group, allergies, current medications). Emergency responders can scan the QR code to access it instantly — no login needed.',
  },
  {
    question: 'Is my health data secure?',
    answer: 'Yes. Passwords are bcrypt-hashed, sessions use JWT tokens with 30-day expiry, and the app follows HIPAA-aligned practices. No health data is shared with third parties.',
  },
  {
    question: 'What is RxGuard?',
    answer: 'RxGuard is the built-in AI safety chatbot. Ask it things like "Can I take Disprin with Warfarin?" and it checks against your current medication profile to give a personalised answer.',
  },
];

const topics = [
  { icon: Camera, label: 'Upload & OCR', color: 'text-violet-500', bg: 'bg-violet-50' },
  { icon: Pill, label: 'Drug Safety', color: 'text-red-500', bg: 'bg-red-50' },
  { icon: CreditCard, label: 'Insurance', color: 'text-blue-500', bg: 'bg-blue-50' },
  { icon: Clock, label: 'Dosage Schedule', color: 'text-amber-500', bg: 'bg-amber-50' },
  { icon: Shield, label: 'Account & Security', color: 'text-emerald-500', bg: 'bg-emerald-50' },
  { icon: BookOpen, label: 'Clinical Data', color: 'text-indigo-500', bg: 'bg-indigo-50' },
];

export const HelpPage: React.FC = () => {
  const [search, setSearch] = useState('');
  const [expanded, setExpanded] = useState<number | null>(null);

  const filtered = faqs.filter(f =>
    search === '' ||
    f.question.toLowerCase().includes(search.toLowerCase()) ||
    f.answer.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="max-w-2xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Help & Support</h1>
        <p className="text-sm text-gray-500 mt-1">Quick answers about MedLens AI features.</p>
      </div>

      {/* Search */}
      <div className="relative mb-8">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search help topics..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full pl-11 pr-4 py-3 bg-white border border-gray-200 rounded-2xl text-sm text-gray-700 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-transparent shadow-sm transition-all"
        />
      </div>

      {/* Topic grid */}
      {search === '' && (
        <div className="mb-8">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Browse by topic</p>
          <div className="grid grid-cols-3 gap-3">
            {topics.map(t => {
              const Icon = t.icon;
              return (
                <button
                  key={t.label}
                  className="flex flex-col items-center gap-2 p-4 bg-white border border-gray-100 rounded-2xl hover:border-violet-200 hover:shadow-sm transition-all duration-150 group"
                >
                  <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${t.bg}`}>
                    <Icon className={`w-4.5 h-4.5 ${t.color}`} />
                  </div>
                  <span className="text-xs font-medium text-gray-600 group-hover:text-gray-900 transition-colors text-center leading-tight">{t.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* FAQs */}
      <div>
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
          {search ? `${filtered.length} result${filtered.length !== 1 ? 's' : ''}` : 'Frequently asked questions'}
        </p>
        <div className="space-y-2">
          {filtered.map((faq, i) => (
            <div
              key={i}
              className="bg-white border border-gray-100 rounded-2xl overflow-hidden shadow-sm"
            >
              <button
                className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-gray-50 transition-colors"
                onClick={() => setExpanded(expanded === i ? null : i)}
              >
                <span className="text-sm font-medium text-gray-800 pr-4">{faq.question}</span>
                <ChevronRight className={`w-4 h-4 text-gray-300 shrink-0 transition-transform duration-200 ${expanded === i ? 'rotate-90' : ''}`} />
              </button>
              {expanded === i && (
                <div className="px-5 pb-4">
                  <p className="text-sm text-gray-500 leading-relaxed border-t border-gray-50 pt-3">{faq.answer}</p>
                </div>
              )}
            </div>
          ))}
          {filtered.length === 0 && (
            <div className="text-center py-10">
              <p className="text-sm text-gray-400">No results for "{search}"</p>
            </div>
          )}
        </div>
      </div>

      {/* Contact */}
      <div className="mt-8 p-5 bg-gradient-to-br from-violet-50 to-blue-50 rounded-2xl border border-violet-100">
        <p className="text-sm font-semibold text-gray-800 mb-1">Still need help?</p>
        <p className="text-xs text-gray-500 mb-4">Reach our team directly.</p>
        <div className="flex gap-3">
          <a
            href="mailto:support@medlens.ai"
            className="flex items-center gap-2 px-4 py-2.5 bg-white text-gray-700 text-xs font-semibold rounded-xl border border-gray-200 hover:border-violet-300 hover:shadow-sm transition-all"
          >
            <Mail className="w-3.5 h-3.5 text-violet-500" />
            Email support
          </a>
          <button className="flex items-center gap-2 px-4 py-2.5 bg-violet-600 text-white text-xs font-semibold rounded-xl hover:bg-violet-700 transition-all shadow-sm">
            <MessageCircle className="w-3.5 h-3.5" />
            Live chat
          </button>
        </div>
      </div>
    </div>
  );
};
