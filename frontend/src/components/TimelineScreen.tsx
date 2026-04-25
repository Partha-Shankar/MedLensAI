import React from 'react';
import type { TimelineResult, Medication } from '../lib/types';
import { ArrowLeft, Clock, AlertTriangle, CheckCircle2 } from 'lucide-react';

interface Props { timelineResult: TimelineResult; medications: Medication[]; onBack: () => void; }

const DRUG_COLORS = [
  { bg: 'bg-violet-500', text: 'text-violet-700', light: 'bg-violet-50 border-violet-200' },
  { bg: 'bg-blue-500', text: 'text-blue-700', light: 'bg-blue-50 border-blue-200' },
  { bg: 'bg-emerald-500', text: 'text-emerald-700', light: 'bg-emerald-50 border-emerald-200' },
  { bg: 'bg-amber-500', text: 'text-amber-700', light: 'bg-amber-50 border-amber-200' },
  { bg: 'bg-rose-500', text: 'text-rose-700', light: 'bg-rose-50 border-rose-200' },
  { bg: 'bg-cyan-500', text: 'text-cyan-700', light: 'bg-cyan-50 border-cyan-200' },
  { bg: 'bg-fuchsia-500', text: 'text-fuchsia-700', light: 'bg-fuchsia-50 border-fuchsia-200' },
  { bg: 'bg-teal-500', text: 'text-teal-700', light: 'bg-teal-50 border-teal-200' },
];

export function TimelineScreen({ timelineResult, medications, onBack }: Props) {
  const drugColorMap: Record<string, typeof DRUG_COLORS[0]> = {};
  medications.forEach((m, i) => { drugColorMap[m.DrugName] = DRUG_COLORS[i % DRUG_COLORS.length]; });

  const hours = Array.from({ length: 24 }, (_, i) => i);
  const conflicts = timelineResult.conflict_windows || [];
  const prn = timelineResult.as_needed_drugs || [];

  return (
    <div className="space-y-6 animate-fadeSlideUp">
      <div>
        <button onClick={onBack} className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-900 font-medium mb-4 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to analysis
        </button>
        <h1 className="text-xl font-semibold text-gray-900 tracking-tight flex items-center gap-2">
          <Clock className="w-5 h-5 text-gray-500" /> 24-Hour Dosing Schedule
        </h1>
        <p className="text-sm text-gray-500 mt-1">Visual timeline of administration windows with conflict identification.</p>
      </div>

      {/* Timeline chart */}
      <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5 overflow-x-auto">
        <div className="min-w-[720px]">
          {/* Hour labels */}
          <div className="flex border-b border-gray-100 pb-2 mb-3">
            {hours.map(h => (
              <div key={h} className="flex-1 text-center text-[10px] font-mono font-medium text-gray-400">
                {h.toString().padStart(2, '0')}
              </div>
            ))}
          </div>

          {/* Grid + entries */}
          <div className="relative h-64">
            {/* Grid lines */}
            <div className="absolute inset-0 flex pointer-events-none">
              {hours.map(h => (
                <div key={h} className={`flex-1 border-r ${h % 6 === 0 ? 'border-gray-200' : 'border-gray-100'} h-full`} />
              ))}
            </div>

            {/* Conflict windows */}
            {conflicts.map((cw, i) => {
              const s = cw.start_time.split(':'), e = cw.end_time.split(':');
              const sm = +s[0] * 60 + +s[1], em = +e[0] * 60 + +e[1];
              return (
                <div key={i} className="absolute top-0 bottom-0 bg-red-50 border-x border-red-200 opacity-60"
                  style={{ left: `${(sm / 1440) * 100}%`, width: `${((em - sm) / 1440) * 100}%` }}>
                  <div className="absolute -top-5 left-1/2 -translate-x-1/2 text-[9px] text-red-600 font-bold bg-red-50 px-1.5 py-0.5 rounded border border-red-200 whitespace-nowrap">Conflict</div>
                </div>
              );
            })}

            {/* Drug entries */}
            {timelineResult.timeline.filter(e => !e.as_needed).map((entry, i) => {
              const [h, m] = entry.time_24h.split(':').map(Number);
              const leftPct = ((h * 60 + m) / 1440) * 100;
              const yOffset = 20 + (i % 5) * 46;
              const color = drugColorMap[entry.drug_name] || DRUG_COLORS[0];
              return (
                <div key={i} className={`absolute text-white text-[11px] font-semibold px-2.5 py-1.5 rounded-lg shadow-sm whitespace-nowrap transform -translate-x-1/2 -translate-y-1/2 ${color.bg}`}
                  style={{ left: `${leftPct}%`, top: yOffset }}
                  title={`${entry.drug_name} · ${entry.dose} at ${entry.time_24h}`}>
                  {entry.drug_name.length > 10 ? entry.drug_name.substring(0, 9) + '…' : entry.drug_name}
                  <span className="opacity-75 ml-1 font-mono">{entry.time_24h}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-5">
        {/* Legend */}
        <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Compound legend</h3>
          <div className="flex flex-wrap gap-2">
            {medications.map(m => {
              const color = drugColorMap[m.DrugName] || DRUG_COLORS[0];
              return (
                <div key={m.DrugName} className={`flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-full border ${color.light} ${color.text}`}>
                  <div className={`w-2 h-2 rounded-full ${color.bg}`} />{m.DrugName}
                </div>
              );
            })}
          </div>
        </div>

        {/* Notes */}
        <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Scheduling notes</h3>
          {conflicts.length > 0 ? (
            <div className="space-y-3">
              {conflicts.map((cw, i) => (
                <div key={i} className="flex items-start gap-2.5 text-xs text-red-700 bg-red-50 border border-red-200 rounded-xl p-3">
                  <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                  <span>{cw.drug_a} and {cw.drug_b} overlap between {cw.start_time}–{cw.end_time}.{cw.time_separation_required ? ` Impose ${cw.time_separation_required} separation.` : ' Consider staggering doses.'}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center gap-2 text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-xl p-3">
              <CheckCircle2 className="w-3.5 h-3.5" /> No scheduling conflicts detected.
            </div>
          )}
          {prn.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-100">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">As-needed (PRN)</p>
              <div className="flex flex-wrap gap-1.5">
                {prn.map((d, i) => <span key={i} className="text-xs bg-gray-100 text-gray-600 px-2.5 py-1 rounded-full border border-gray-200">{d}</span>)}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
