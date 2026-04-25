import React, { useState, useRef } from 'react';
import { UploadCloud, File as FileIcon, X, User, ChevronDown, Info } from 'lucide-react';
import type { PatientProfile } from '../App';

interface Props {
  onAnalyze: (file: File, profile: PatientProfile) => void;
}

const CONDITIONS = ['Diabetes', 'Hypertension', 'Kidney Disease', 'Pregnancy', 'Heart Disease', 'Liver Disease', 'Asthma'];

export function UploadScreen({ onAnalyze }: Props) {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [profile, setProfile] = useState<PatientProfile>({ name: '', age: '', sex: '', conditions: [], allergies: '' });

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation();
    setDragActive(e.type === 'dragenter' || e.type === 'dragover');
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files?.[0]) handleFile(e.dataTransfer.files[0]);
  };

  const handleFile = (f: File) => {
    setFile(f);
    setPreview(f.type.startsWith('image/') ? URL.createObjectURL(f) : null);
  };

  const toggleCondition = (c: string) =>
    setProfile(p => ({ ...p, conditions: p.conditions.includes(c) ? p.conditions.filter(x => x !== c) : [...p.conditions, c] }));

  return (
    <div className="space-y-6 animate-fadeSlideUp">
      {/* Page header */}
      <div>
        <h1 className="text-xl font-semibold text-gray-900 tracking-tight">New Analysis</h1>
        <p className="text-sm text-gray-500 mt-1">Upload a prescription document and optionally provide patient context for personalised safety checks.</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Upload zone */}
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-700">Prescription document</h2>
            <span className="text-xs text-gray-400">JPG, PNG, PDF · max 10 MB</span>
          </div>

          {!file ? (
            <div
              className={`flex-1 min-h-64 border-2 border-dashed rounded-2xl flex flex-col items-center justify-center cursor-pointer transition-all duration-200 ${
                dragActive ? 'border-violet-400 bg-violet-50' : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50'
              }`}
              onDragEnter={handleDrag} onDragLeave={handleDrag}
              onDragOver={handleDrag} onDrop={handleDrop}
              onClick={() => inputRef.current?.click()}
            >
              <div className={`w-14 h-14 rounded-2xl flex items-center justify-center mb-4 transition-colors ${dragActive ? 'bg-violet-100' : 'bg-gray-100'}`}>
                <UploadCloud className={`w-7 h-7 transition-colors ${dragActive ? 'text-violet-600' : 'text-gray-400'}`} />
              </div>
              <p className="text-sm font-medium text-gray-700 mb-1">
                {dragActive ? 'Release to upload' : 'Drag & drop your file here'}
              </p>
              <p className="text-xs text-gray-400 mb-5">or click to browse</p>
              <button
                type="button"
                className="text-xs font-medium bg-white border border-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-all shadow-sm"
                onClick={e => { e.stopPropagation(); inputRef.current?.click(); }}
              >
                Browse files
              </button>
              <input ref={inputRef} type="file" className="hidden" accept="image/jpeg,image/png,application/pdf" onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])} />
            </div>
          ) : (
            <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden shadow-sm flex-1">
              <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 bg-blue-50 rounded-lg flex items-center justify-center">
                    <FileIcon className="w-4.5 h-4.5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900 max-w-[200px] truncate">{file.name}</p>
                    <p className="text-xs text-gray-400">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                </div>
                <button onClick={() => { setFile(null); setPreview(null); }} className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors">
                  <X className="w-4 h-4" />
                </button>
              </div>
              <div className="bg-gray-50 min-h-56 flex items-center justify-center">
                {preview
                  ? <img src={preview} alt="Preview" className="max-h-72 object-contain p-4" />
                  : <div className="text-center text-gray-400"><FileIcon className="w-10 h-10 mx-auto mb-2 opacity-40" /><p className="text-xs">PDF document ready</p></div>
                }
              </div>
            </div>
          )}
        </div>

        {/* Patient profile */}
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-700">Patient context</h2>
            <span className="text-xs text-gray-400 flex items-center gap-1"><Info className="w-3 h-3" />Optional but recommended</span>
          </div>

          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm space-y-5 flex-1">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">Full name</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-300" />
                <input
                  type="text"
                  value={profile.name}
                  onChange={e => setProfile({ ...profile, name: e.target.value })}
                  className="w-full pl-9 pr-3 py-2.5 bg-white border border-gray-200 rounded-xl text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent transition-all"
                  placeholder="Patient name"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1.5">Age</label>
                <input
                  type="text"
                  value={profile.age}
                  onChange={e => setProfile({ ...profile, age: e.target.value })}
                  className="w-full px-3 py-2.5 bg-white border border-gray-200 rounded-xl text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent transition-all"
                  placeholder="e.g. 45"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1.5">Biological sex</label>
                <div className="relative">
                  <select
                    value={profile.sex}
                    onChange={e => setProfile({ ...profile, sex: e.target.value })}
                    className="w-full appearance-none px-3 py-2.5 bg-white border border-gray-200 rounded-xl text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent transition-all"
                  >
                    <option value="">Select</option>
                    <option value="M">Male</option>
                    <option value="F">Female</option>
                    <option value="Other">Other</option>
                  </select>
                  <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                </div>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-600 mb-2">Known comorbidities</label>
              <div className="flex flex-wrap gap-2">
                {CONDITIONS.map(c => (
                  <button
                    key={c}
                    type="button"
                    onClick={() => toggleCondition(c)}
                    className={`text-xs px-3 py-1.5 rounded-full border font-medium transition-all ${
                      profile.conditions.includes(c)
                        ? 'bg-gray-900 text-white border-gray-900'
                        : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    {c}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">Known drug allergies</label>
              <input
                type="text"
                value={profile.allergies}
                onChange={e => setProfile({ ...profile, allergies: e.target.value })}
                className="w-full px-3 py-2.5 bg-white border border-gray-200 rounded-xl text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent transition-all"
                placeholder="e.g. Penicillin, Sulfa drugs"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Submit */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-100">
        <p className="text-xs text-gray-400">
          {file ? `Ready · ${file.name}` : 'No document selected'}
        </p>
        <button
          disabled={!file}
          onClick={() => file && onAnalyze(file, profile)}
          className={`flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold transition-all shadow-sm ${
            file
              ? 'bg-gray-900 text-white hover:bg-gray-800 hover:shadow-md hover:-translate-y-0.5'
              : 'bg-gray-100 text-gray-400 cursor-not-allowed'
          }`}
        >
          Run Analysis
        </button>
      </div>
    </div>
  );
}
