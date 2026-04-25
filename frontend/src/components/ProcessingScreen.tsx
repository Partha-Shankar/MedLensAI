import React, { useEffect, useState } from 'react';
import { CheckCircle2, Circle } from 'lucide-react';

const STEPS = [
  {
    title: 'Optical character recognition',
    desc: 'Parsing handwritten script via neural visual extraction pipeline...',
    duration: 2800,
  },
  {
    title: 'Pharmacological entity resolution',
    desc: 'Cross-referencing extracted tokens against the regional drug index with fuzzy matching...',
    duration: 5200,
  },
  {
    title: 'Clinical safety validation',
    desc: 'Executing interaction checks, dosage plausibility, and formulary coverage queries...',
    duration: 7800,
  },
];

const LOG_LINES = [
  { t: 300,  msg: '[OCR]     Initialising visual extraction model...' },
  { t: 900,  msg: '[OCR]     Document loaded · 1 page detected' },
  { t: 1500, msg: '[OCR]     Handwriting confidence threshold: 0.82' },
  { t: 2200, msg: '[DRUG]    Running RapidFuzz against local drug index...' },
  { t: 3000, msg: '[DRUG]    22 entries in pharmacological corpus' },
  { t: 3800, msg: '[DRUG]    Levenshtein distance threshold: 3' },
  { t: 4500, msg: '[SAFE]    Loading interaction matrix (54 318 pairs)...' },
  { t: 5300, msg: '[SAFE]    Executing pairwise conflict detection...' },
  { t: 6100, msg: '[SAFE]    Dosage plausibility check: patient age applied' },
  { t: 6900, msg: '[INS]     Querying CGHS/PMJAY formulary coverage...' },
  { t: 7500, msg: '[INS]     Generic alternatives resolved' },
  { t: 8000, msg: '[DONE]    Analysis complete · results ready' },
];

export function ProcessingScreen() {
  const [activeStep, setActiveStep] = useState(0);
  const [visibleLogs, setVisibleLogs] = useState<string[]>([]);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const start = Date.now();
    const interval = setInterval(() => setElapsed(Date.now() - start), 100);

    const stepTimers = STEPS.map((s, i) =>
      setTimeout(() => setActiveStep(i + 1), s.duration)
    );

    const logTimers = LOG_LINES.map(l =>
      setTimeout(() => setVisibleLogs(prev => [...prev, l.msg]), l.t)
    );

    return () => {
      clearInterval(interval);
      stepTimers.forEach(clearTimeout);
      logTimers.forEach(clearTimeout);
    };
  }, []);

  const logsEndRef = React.useRef<HTMLDivElement>(null);
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [visibleLogs]);

  return (
    <div className="min-h-[calc(100vh-7rem)] flex items-start justify-center pt-12 px-4 animate-fadeSlideUp">
      <div className="w-full max-w-2xl space-y-5">

        {/* Header card */}
        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-1">Analysing prescription</h2>
              <p className="text-sm text-gray-500">Please wait while the clinical engine processes your document.</p>
            </div>
            <div className="text-right shrink-0">
              <span className="text-xs font-mono text-gray-400">{(elapsed / 1000).toFixed(1)}s</span>
              <div className="flex items-center gap-1.5 mt-1">
                <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                <span className="text-xs text-gray-500 font-medium">Processing</span>
              </div>
            </div>
          </div>

          {/* Steps */}
          <div className="space-y-4">
            {STEPS.map((step, idx) => {
              const done    = idx < activeStep;
              const active  = idx === activeStep;
              const pending = idx > activeStep;
              return (
                <div key={idx} className={`flex items-start gap-4 transition-opacity duration-500 ${pending ? 'opacity-35' : ''}`}>
                  <div className="mt-0.5 shrink-0">
                    {done ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                    ) : active ? (
                      <div className="w-5 h-5 rounded-full border-2 border-gray-300 border-t-gray-800 animate-spin" />
                    ) : (
                      <Circle className="w-5 h-5 text-gray-300" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-medium ${done ? 'text-gray-900 line-through decoration-gray-400' : active ? 'text-gray-900' : 'text-gray-400'}`}>
                      {step.title}
                    </p>
                    {active && (
                      <p className="text-xs text-gray-500 mt-0.5 animate-fadeSlideUp">{step.desc}</p>
                    )}
                    {done && (
                      <p className="text-xs text-emerald-600 mt-0.5">Complete</p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Progress bar */}
          <div className="mt-6 h-1 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-gray-900 rounded-full transition-all duration-700"
              style={{ width: `${(activeStep / STEPS.length) * 100}%` }}
            />
          </div>
        </div>

        {/* System Logs — shown while loading */}
        <div className="bg-gray-950 border border-gray-800 rounded-2xl overflow-hidden shadow-sm">
          <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-800">
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full bg-red-500/60" />
              <div className="w-3 h-3 rounded-full bg-amber-500/60" />
              <div className="w-3 h-3 rounded-full bg-emerald-500/60" />
            </div>
            <span className="text-xs text-gray-500 font-mono ml-2">medlens · engine.log</span>
          </div>
          <div className="p-4 font-mono text-xs text-emerald-400 h-48 overflow-y-auto space-y-1">
            {visibleLogs.map((line, i) => (
              <div key={i} className="animate-fadeSlideUp leading-relaxed whitespace-nowrap overflow-x-auto">
                <span className="text-gray-600 select-none mr-3">{String(i + 1).padStart(2, '0')}</span>
                {line}
              </div>
            ))}
            {activeStep < STEPS.length && (
              <div className="flex items-center gap-2 text-gray-600">
                <span className="text-gray-700 select-none mr-3">{String(visibleLogs.length + 1).padStart(2, '0')}</span>
                <span className="animate-pulse">▋</span>
              </div>
            )}
            <div ref={logsEndRef} />
          </div>
        </div>
      </div>
    </div>
  );
}
