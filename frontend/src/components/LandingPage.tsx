import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Activity, Shield, Clock, FileText, ChevronRight, Zap,
  BarChart3, Database, Lock, CheckCircle, Users, Globe
} from 'lucide-react';

const stats = [
  { value: '99.8%', label: 'Extraction Accuracy' },
  { value: '<2s', label: 'Avg. Processing Time' },
  { value: '54K+', label: 'Interaction Pairs' },
  { value: 'HIPAA', label: 'Compliant Protocol' },
];

const features = [
  {
    icon: Zap,
    color: 'text-violet-600',
    bg: 'bg-violet-50',
    title: 'Neural Optical Extraction',
    desc: 'Sub-second handwriting recognition fine-tuned on Indian medical nomenclature, resolving abbreviated and colloquial drug references with deterministic precision.',
  },
  {
    icon: Shield,
    color: 'text-red-600',
    bg: 'bg-red-50',
    title: 'Pharmacovigilance Engine',
    desc: 'Cross-references active compounds against 54,000+ interaction pairs, issuing stratified severity alerts with mechanistic rationale and pharmacist action protocols.',
  },
  {
    icon: BarChart3,
    color: 'text-blue-600',
    bg: 'bg-blue-50',
    title: 'Formulary Intelligence',
    desc: 'Automated PMJAY/CGHS coverage mapping with generic substitution recommendations, delivering out-of-pocket cost projections per prescription batch.',
  },
  {
    icon: Database,
    color: 'text-emerald-600',
    bg: 'bg-emerald-50',
    title: 'Longitudinal Health Vault',
    desc: 'Cryptographically secured patient history with QR-accessible emergency medical cards, enabling instantaneous clinical context delivery to first responders.',
  },
  {
    icon: Clock,
    color: 'text-amber-600',
    bg: 'bg-amber-50',
    title: 'Temporal Dosing Trajectories',
    desc: 'Generates 24-hour administration schedules with conflict-window identification, enforcing time-separation protocols for concurrently prescribed compounds.',
  },
  {
    icon: Users,
    color: 'text-cyan-600',
    bg: 'bg-cyan-50',
    title: 'Clinical Intelligence Dialogue',
    desc: 'Contextual advisory engine pre-loaded with extracted prescription data, delivering personalised pharmaceutical guidance within a medically constrained reasoning framework.',
  },
];

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-white font-sans text-gray-900 selection:bg-violet-100">
      {/* Navigation */}
      <header className={`fixed inset-x-0 top-0 z-50 transition-all duration-300 ${scrolled ? 'bg-white/90 backdrop-blur-md border-b border-gray-200 shadow-sm' : 'bg-transparent'}`}>
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gray-900 rounded-lg flex items-center justify-center">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <span className="text-gray-900 font-bold text-lg tracking-tight">MedLens</span>
          </div>
          <nav className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-sm text-gray-500 hover:text-gray-900 transition-colors font-medium">Features</a>
            <a href="#compliance" className="text-sm text-gray-500 hover:text-gray-900 transition-colors font-medium">Compliance</a>
            <a href="#team" className="text-sm text-gray-500 hover:text-gray-900 transition-colors font-medium">About</a>
          </nav>
          <div className="flex items-center gap-3">
            <Link to="/login" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors px-4 py-2">Sign In</Link>
            <Link to="/login" className="text-sm font-semibold bg-gray-900 text-white px-4 py-2 rounded-lg hover:bg-gray-800 transition-colors">
              Get Access
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="pt-32 pb-24 px-6 relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-10%,rgba(120,119,198,0.08),transparent)] pointer-events-none" />
        <div className="absolute inset-y-0 right-0 w-1/2 bg-[radial-gradient(ellipse_60%_80%_at_80%_50%,rgba(59,130,246,0.04),transparent)] pointer-events-none" />
        
        <div className="max-w-4xl mx-auto text-center relative">
          <div className="inline-flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-full px-4 py-1.5 mb-8">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs font-medium text-gray-500 uppercase tracking-widest">v2.4 · Clinical Intelligence Platform</span>
          </div>

          <h1 className="text-6xl md:text-7xl font-bold text-gray-900 tracking-tight leading-[1.05] mb-6">
            Prescription analysis<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-600 to-blue-600">
              at clinical grade.
            </span>
          </h1>

          <p className="text-xl text-gray-500 max-w-2xl mx-auto leading-relaxed mb-12 font-light">
            MedLens converts handwritten prescriptions into structured clinical intelligence — detecting interactions, validating dosages, mapping insurance coverage, and delivering actionable pharmaceutical guidance.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={() => navigate('/login')}
              className="group flex items-center gap-2 bg-gray-900 text-white px-7 py-3.5 rounded-xl font-semibold text-sm hover:bg-gray-800 transition-all shadow-lg shadow-gray-900/10 hover:shadow-xl hover:shadow-gray-900/20 hover:-translate-y-0.5"
            >
              Initiate Analysis
              <ChevronRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
            </button>
            <button className="flex items-center gap-2 bg-white border border-gray-200 text-gray-700 px-7 py-3.5 rounded-xl font-semibold text-sm hover:border-gray-300 hover:bg-gray-50 transition-all">
              <Lock className="w-4 h-4" />
              View Compliance Docs
            </button>
          </div>
        </div>

        {/* Stats bar */}
        <div className="max-w-3xl mx-auto mt-20">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-0 border border-gray-200 rounded-2xl overflow-hidden bg-white shadow-sm">
            {stats.map((s, i) => (
              <div key={i} className={`px-8 py-6 text-center ${i < stats.length - 1 ? 'border-r border-gray-100' : ''}`}>
                <div className="text-2xl font-bold text-gray-900 mb-1">{s.value}</div>
                <div className="text-xs text-gray-400 font-medium uppercase tracking-wider">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-24 px-6 bg-gray-50 border-y border-gray-100">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <p className="text-xs font-semibold text-violet-600 uppercase tracking-widest mb-4">Capabilities</p>
            <h2 className="text-4xl font-bold text-gray-900 tracking-tight mb-4">
              A complete clinical analysis stack.
            </h2>
            <p className="text-lg text-gray-500 max-w-xl mx-auto">
              Every layer of the prescription workflow, handled with methodical precision.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f, i) => (
              <div
                key={i}
                className="bg-white border border-gray-200 rounded-2xl p-6 hover:border-gray-300 hover:shadow-md transition-all duration-200 group"
                style={{ animationDelay: `${i * 80}ms` }}
              >
                <div className={`w-10 h-10 ${f.bg} rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                  <f.icon className={`w-5 h-5 ${f.color}`} />
                </div>
                <h3 className="font-semibold text-gray-900 text-sm mb-2 tracking-tight">{f.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Compliance */}
      <section id="compliance" className="py-24 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-xs font-semibold text-blue-600 uppercase tracking-widest mb-4">Security & Compliance</p>
          <h2 className="text-4xl font-bold text-gray-900 tracking-tight mb-6">
            Built for regulated environments.
          </h2>
          <p className="text-gray-500 text-lg mb-12 max-w-2xl mx-auto">
            MedLens is engineered with a security-first architecture. Patient data is encrypted in transit and at rest, with access controls enforced at every API boundary.
          </p>
          <div className="flex flex-wrap justify-center gap-6">
            {['256-bit AES Encryption', 'Zero-trust Access Control', 'Audit Logging', 'Data Residency Controls'].map((item, i) => (
              <div key={i} className="flex items-center gap-2.5 bg-gray-50 border border-gray-200 rounded-full px-5 py-2.5">
                <CheckCircle className="w-4 h-4 text-emerald-500" />
                <span className="text-sm font-medium text-gray-700">{item}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Team CTA */}
      <section id="team" className="py-16 px-6 border-t border-gray-100 bg-gray-50">
        <div className="max-w-2xl mx-auto text-center">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-4">Core Division</p>
          <h3 className="text-2xl font-bold text-gray-900 mb-3">Engineered by</h3>
          <p className="text-gray-600 font-medium leading-relaxed">
            Partha Shankar Captain <span className="text-gray-400">·</span> Anupama B M <span className="text-gray-400">·</span> Maithri M <span className="text-gray-400">·</span> Nirmith M Jain
          </p>
          <button onClick={() => navigate('/login')} className="mt-8 inline-flex items-center gap-2 bg-gray-900 text-white px-6 py-3 rounded-xl font-semibold text-sm hover:bg-gray-800 transition-all">
            Access Platform <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 py-6 px-6">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-gray-900 rounded flex items-center justify-center">
              <Activity className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="text-sm font-semibold text-gray-900">MedLens</span>
            <span className="text-gray-300 mx-2">·</span>
            <span className="text-xs text-gray-400">Clinical Intelligence Platform v2.4.1</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <Globe className="w-3.5 h-3.5" />
            <span>Engineered for the Indian Healthcare Ecosystem</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
