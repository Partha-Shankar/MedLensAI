import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { QRCodeSVG } from 'qrcode.react';
import { User, Loader2, Save, QrCode, Info } from 'lucide-react';

export function ProfilePage() {
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    api.getProfile().then(d => { setProfile(d); setLoading(false); }).catch(() => { navigate('/login'); });
  }, [navigate]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setProfile({ ...profile, [e.target.name]: e.target.value });

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await api.updateProfile(profile);
      setProfile(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch { alert('Save failed.'); }
    finally { setSaving(false); }
  };

  if (loading) return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="text-center"><Loader2 className="w-8 h-8 text-gray-400 animate-spin mx-auto mb-3" /><p className="text-sm text-gray-500">Loading profile...</p></div>
    </div>
  );

  const publicUrl = `${window.location.origin}/card/${profile?.id}`;

  const Field = ({ label, name, placeholder, type = 'text' }: { label: string; name: string; placeholder?: string; type?: string }) => (
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1.5">{label}</label>
      <input type={type} name={name} value={profile?.[name] || ''} onChange={handleChange}
        className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent transition-all bg-white"
        placeholder={placeholder} />
    </div>
  );

  const TextArea = ({ label, name, placeholder }: { label: string; name: string; placeholder?: string }) => (
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1.5">{label}</label>
      <textarea name={name} value={profile?.[name] || ''} onChange={handleChange} rows={2}
        className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent transition-all bg-white resize-none"
        placeholder={placeholder} />
    </div>
  );

  return (
    <div className="space-y-6 animate-fadeSlideUp">
      <div>
        <h1 className="text-xl font-semibold text-gray-900 tracking-tight">Patient Profile</h1>
        <p className="text-sm text-gray-500 mt-1">Manage medical details used for personalised safety analysis.</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Main form */}
        <div className="lg:col-span-2 space-y-5">
          <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-5">
              <User className="w-4 h-4 text-gray-400" />
              <h2 className="text-sm font-semibold text-gray-900">Identity</h2>
            </div>
            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1.5">Full name</label>
                <input type="text" value={profile?.name || ''} readOnly className="w-full border border-gray-100 bg-gray-50 rounded-xl px-3.5 py-2.5 text-sm text-gray-500 cursor-not-allowed" />
              </div>
              <Field label="Blood group" name="blood_group" placeholder="e.g. O+" />
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm space-y-4">
            <h2 className="text-sm font-semibold text-gray-900">Medical information</h2>
            <Field label="Emergency contact" name="emergency_contact" placeholder="Name and phone number" />
            <TextArea label="Known allergies" name="allergies" placeholder="e.g. Penicillin, Sulfa drugs (comma separated)" />
            <TextArea label="Chronic conditions" name="conditions" placeholder="e.g. Diabetes, Hypertension (comma separated)" />
            <TextArea label="Current medications" name="current_meds" placeholder="Ongoing medications not from MedLens" />
          </div>

          <div className="flex items-center justify-between pt-2">
            {saved && <span className="text-xs text-emerald-600 font-medium">Changes saved successfully.</span>}
            <div className="ml-auto">
              <button onClick={handleSave} disabled={saving} className="flex items-center gap-2 bg-gray-900 text-white px-5 py-2.5 rounded-xl text-sm font-semibold hover:bg-gray-800 transition-all disabled:opacity-60 shadow-sm">
                {saving ? <><Loader2 className="w-4 h-4 animate-spin" />Saving...</> : <><Save className="w-4 h-4" />Save changes</>}
              </button>
            </div>
          </div>
        </div>

        {/* QR side panel */}
        <div className="space-y-5">
          <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm text-center">
            <div className="flex items-center gap-2 mb-4 justify-center">
              <QrCode className="w-4 h-4 text-gray-400" />
              <h2 className="text-sm font-semibold text-gray-900">Emergency Access Card</h2>
            </div>
            <p className="text-xs text-gray-500 mb-5 leading-relaxed">Scan to instantly surface critical medical history and allergy data in emergencies.</p>
            <div className="bg-gray-50 border border-gray-100 p-4 rounded-xl inline-block mb-4">
              <QRCodeSVG value={publicUrl} size={160} level="H" />
            </div>
            <p className="text-[10px] text-gray-400 font-mono break-all">{publicUrl}</p>
          </div>

          <div className="bg-blue-50 border border-blue-100 rounded-2xl p-5">
            <div className="flex items-start gap-2">
              <Info className="w-4 h-4 text-blue-500 shrink-0 mt-0.5" />
              <div>
                <p className="text-xs font-semibold text-blue-800 mb-1">Why complete your profile?</p>
                <ul className="text-xs text-blue-700 space-y-1 leading-relaxed">
                  <li>· Enables personalised drug interaction alerts</li>
                  <li>· Supports age-specific dosage validation</li>
                  <li>· Provides instant context to emergency responders</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
