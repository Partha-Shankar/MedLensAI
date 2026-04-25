import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../lib/api';

export function PublicMedicalCardPage() {
  const { userId } = useParams();
  const [cardData, setCardData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchCard = async () => {
      try {
        if (!userId) return;
        const res = await api.getPublicMedicalCard(userId);
        setCardData(res.medical_card);
      } catch (err) {
        console.error(err);
        setError('Failed to load medical card or card does not exist.');
      } finally {
        setLoading(false);
      }
    };
    fetchCard();
  }, [userId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-red-50 flex items-center justify-center">
        <div className="animate-pulse flex flex-col items-center">
          <div className="w-16 h-16 border-4 border-red-500 border-t-transparent rounded-full animate-spin mb-4"></div>
          <p className="text-red-600 font-semibold">Retrieving Emergency Medical Data...</p>
        </div>
      </div>
    );
  }

  if (error || !cardData) {
    return (
      <div className="min-h-screen bg-red-50 flex items-center justify-center p-4">
        <div className="bg-white p-8 rounded-2xl shadow-xl max-w-md w-full text-center border-t-4 border-red-500">
          <h2 className="text-2xl font-bold text-slate-800 mb-2">Access Denied</h2>
          <p className="text-slate-600">{error || 'Invalid Medical Card URL.'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 py-8 px-4 sm:px-6 flex justify-center items-start">
      <div className="max-w-2xl w-full bg-white rounded-3xl shadow-2xl overflow-hidden relative border-4 border-red-600">
        
        {/* Header Ribbon */}
        <div className="bg-red-600 text-white py-6 px-8 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-black tracking-tight uppercase">Emergency Medical Card</h1>
            <p className="text-red-100 font-medium tracking-wide">CONFIDENTIAL & CRITICAL INFO</p>
          </div>
          <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 text-red-600" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clipRule="evenodd" />
            </svg>
          </div>
        </div>

        <div className="p-8 space-y-8">
          {/* Identity & Vitals */}
          <div className="flex flex-wrap md:flex-nowrap justify-between gap-6 pb-6 border-b-2 border-slate-100">
            <div>
              <p className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-1">Patient Name</p>
              <h2 className="text-4xl font-extrabold text-slate-900">{cardData.patient_name}</h2>
            </div>
            <div className="flex gap-6">
              <div className="text-center bg-red-50 rounded-xl px-6 py-3 border border-red-100">
                <p className="text-xs font-bold text-red-400 uppercase tracking-wider mb-1">Blood Group</p>
                <p className="text-3xl font-black text-red-600">{cardData.blood_group || 'N/A'}</p>
              </div>
            </div>
          </div>

          {/* Critical Warnings */}
          {cardData.critical_warnings && cardData.critical_warnings.length > 0 && (
            <div className="bg-red-100 border-l-4 border-red-600 p-5 rounded-r-xl">
              <h3 className="flex items-center text-red-800 font-bold mb-2 uppercase tracking-wide">
                <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                Critical Warnings
              </h3>
              <ul className="list-disc list-inside text-red-700 font-medium space-y-1">
                {cardData.critical_warnings.map((w: string, i: number) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Grid Layout for Details */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-2 border-b pb-1">Known Allergies</h3>
                {cardData.known_allergies && cardData.known_allergies.length > 0 && cardData.known_allergies[0] ? (
                  <div className="flex flex-wrap gap-2">
                    {cardData.known_allergies.map((a: string, i: number) => (
                      <span key={i} className="bg-amber-100 text-amber-800 px-3 py-1 rounded-full text-sm font-bold">{a}</span>
                    ))}
                  </div>
                ) : <p className="text-slate-500 italic">None reported</p>}
              </div>

              <div>
                <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-2 border-b pb-1">Chronic Conditions</h3>
                {cardData.chronic_conditions && cardData.chronic_conditions.length > 0 && cardData.chronic_conditions[0] ? (
                  <ul className="list-disc list-inside text-slate-800 font-medium">
                    {cardData.chronic_conditions.map((c: string, i: number) => (
                      <li key={i}>{c}</li>
                    ))}
                  </ul>
                ) : <p className="text-slate-500 italic">None reported</p>}
              </div>
            </div>

            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-2 border-b pb-1">Emergency Contact</h3>
                <p className="text-slate-900 font-bold text-lg bg-slate-100 p-3 rounded-lg">{cardData.emergency_contact || 'None reported'}</p>
              </div>

              <div>
                <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-2 border-b pb-1">Recent Medical History</h3>
                <p className="text-slate-700 text-sm leading-relaxed">{cardData.recent_medical_history_summary}</p>
              </div>
            </div>
          </div>

          {/* Current Medications Table */}
          {cardData.current_medications && cardData.current_medications.length > 0 && (
            <div>
              <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3 border-b pb-1">Current Medications</h3>
              <div className="overflow-hidden rounded-xl border border-slate-200">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50 text-slate-600 font-bold">
                    <tr>
                      <th className="px-4 py-3">Drug Name</th>
                      <th className="px-4 py-3">Dosage</th>
                      <th className="px-4 py-3">Frequency</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {cardData.current_medications.map((med: any, i: number) => (
                      <tr key={i} className="bg-white">
                        <td className="px-4 py-3 font-semibold text-slate-900">{med.drug_name}</td>
                        <td className="px-4 py-3 text-slate-600">{med.dosage}</td>
                        <td className="px-4 py-3 text-slate-600">{med.frequency}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

        </div>
        
        {/* Footer */}
        <div className="bg-slate-100 text-center py-4 border-t border-slate-200">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-widest">Powered by MedLens AI</p>
        </div>
      </div>
    </div>
  );
}
