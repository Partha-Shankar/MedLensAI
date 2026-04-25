import React, { useState } from 'react';
import type { ExtractionResponse, Medication } from '../lib/types';
import { CheckCircle2, AlertTriangle, Edit3 } from 'lucide-react';

interface Props {
  data: ExtractionResponse;
  onConfirm: (updatedPrescription: any) => void;
}

export function ConfirmationScreen({ data, onConfirm }: Props) {
  const [medications, setMedications] = useState<Medication[]>(data.prescription.Medications);
  const pendingCount = medications.filter(m => m.ConfidenceLevel === 'LOW' && !(m as any).confirmed).length;

  const handleConfirmRow = (index: number) => {
    const updated = [...medications];
    (updated[index] as any).confirmed = true;
    setMedications(updated);
  };

  return (
    <div className="space-y-6 animate-fadeSlideUp">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900 tracking-tight">Review extraction</h1>
          <p className="text-sm text-gray-500 mt-1">Verify low-confidence items before running safety checks.</p>
        </div>
        {pendingCount > 0 && (
          <div className="flex items-center gap-2 bg-amber-50 border border-amber-200 text-amber-700 text-xs font-semibold px-3 py-2 rounded-lg">
            <AlertTriangle className="w-3.5 h-3.5" />
            {pendingCount} item{pendingCount > 1 ? 's' : ''} need review
          </div>
        )}
      </div>

      <div className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                <th className="px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Raw OCR</th>
                <th className="px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Confidence</th>
                <th className="px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Resolved Drug</th>
                <th className="px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wider text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {medications.map((med, idx) => {
                const rawLine = data.raw_ocr_lines[idx]?.raw_text || '—';
                const isLow = med.ConfidenceLevel === 'LOW';
                const isConfirmed = (med as any).confirmed;
                return (
                  <tr key={idx} className={`${isLow && !isConfirmed ? 'bg-amber-50/50' : 'hover:bg-gray-50'} transition-colors`}>
                    <td className="px-5 py-4">
                      <code className="text-xs text-gray-500 font-mono bg-gray-100 px-2 py-1 rounded">{rawLine}</code>
                    </td>
                    <td className="px-5 py-4">
                      <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full ${
                        med.ConfidenceLevel === 'HIGH' ? 'bg-emerald-50 text-emerald-700' :
                        med.ConfidenceLevel === 'MEDIUM' ? 'bg-blue-50 text-blue-700' :
                        'bg-amber-50 text-amber-700'
                      }`}>
                        {med.ConfidenceLevel === 'LOW' && <AlertTriangle className="w-3 h-3" />}
                        {med.ConfidenceLevel}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      {isLow && !isConfirmed ? (
                        <input
                          type="text"
                          value={med.DrugName}
                          onChange={e => {
                            const updated = [...medications];
                            updated[idx].DrugName = e.target.value;
                            setMedications(updated);
                          }}
                          className="border border-amber-300 focus:border-gray-900 focus:ring-2 focus:ring-gray-900 rounded-lg px-3 py-1.5 text-sm text-gray-900 outline-none transition-all"
                        />
                      ) : (
                        <span className="text-sm font-medium text-gray-900">{med.DrugName}</span>
                      )}
                    </td>
                    <td className="px-5 py-4 text-right">
                      {isLow && !isConfirmed ? (
                        <button onClick={() => handleConfirmRow(idx)} className="text-xs font-semibold bg-gray-900 text-white px-3 py-1.5 rounded-lg hover:bg-gray-800 transition-colors">
                          Confirm
                        </button>
                      ) : (
                        <CheckCircle2 className="w-5 h-5 text-emerald-500 ml-auto" />
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="flex justify-end pt-2">
        <button
          onClick={() => onConfirm({ ...data.prescription, Medications: medications })}
          disabled={pendingCount > 0}
          className={`px-6 py-3 rounded-xl text-sm font-semibold transition-all ${
            pendingCount === 0
              ? 'bg-gray-900 text-white hover:bg-gray-800 shadow-sm hover:-translate-y-0.5'
              : 'bg-gray-100 text-gray-400 cursor-not-allowed'
          }`}
        >
          Confirm & Run Safety Checks
        </button>
      </div>
    </div>
  );
}
