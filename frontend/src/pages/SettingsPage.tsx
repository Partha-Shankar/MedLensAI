import React, { useState } from 'react';
import { Bell, Shield, Database, Trash2, ChevronRight, Save } from 'lucide-react';



export const SettingsPage: React.FC = () => {
  const [notifications, setNotifications] = useState(true);
  const [emailAlerts, setEmailAlerts] = useState(false);
  const [autoSave, setAutoSave] = useState(true);
  const [scheme, setScheme] = useState('CGHS');
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const Toggle = ({ value, onChange }: { value: boolean; onChange: (v: boolean) => void }) => (
    <button
      onClick={() => onChange(!value)}
      className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors duration-200 focus:outline-none ${value ? 'bg-violet-500' : 'bg-gray-200'}`}
    >
      <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform duration-200 ${value ? 'translate-x-5' : 'translate-x-1'}`} />
    </button>
  );

  return (
    <div className="max-w-2xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-sm text-gray-500 mt-1">Manage your preferences and account configuration.</p>
      </div>

      <div className="space-y-4">
        {/* Notifications */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="flex items-center gap-3 px-5 py-4 border-b border-gray-50">
            <div className="w-8 h-8 rounded-xl bg-violet-50 flex items-center justify-center">
              <Bell className="w-4 h-4 text-violet-500" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-900">Notifications</p>
              <p className="text-xs text-gray-400">Control how MedLens alerts you</p>
            </div>
          </div>
          <div className="divide-y divide-gray-50">
            <div className="flex items-center justify-between px-5 py-3.5">
              <div>
                <p className="text-sm text-gray-700">Push notifications</p>
                <p className="text-xs text-gray-400">Alert when analysis completes</p>
              </div>
              <Toggle value={notifications} onChange={setNotifications} />
            </div>
            <div className="flex items-center justify-between px-5 py-3.5">
              <div>
                <p className="text-sm text-gray-700">Email alerts</p>
                <p className="text-xs text-gray-400">Daily summary of analyses</p>
              </div>
              <Toggle value={emailAlerts} onChange={setEmailAlerts} />
            </div>
          </div>
        </div>

        {/* Analysis Preferences */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="flex items-center gap-3 px-5 py-4 border-b border-gray-50">
            <div className="w-8 h-8 rounded-xl bg-blue-50 flex items-center justify-center">
              <Database className="w-4 h-4 text-blue-500" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-900">Analysis Preferences</p>
              <p className="text-xs text-gray-400">Defaults for prescription analysis</p>
            </div>
          </div>
          <div className="divide-y divide-gray-50">
            <div className="flex items-center justify-between px-5 py-3.5">
              <div>
                <p className="text-sm text-gray-700">Auto-save analyses</p>
                <p className="text-xs text-gray-400">Save each prescription to history</p>
              </div>
              <Toggle value={autoSave} onChange={setAutoSave} />
            </div>
            <div className="flex items-center justify-between px-5 py-3.5">
              <div>
                <p className="text-sm text-gray-700">Default insurance scheme</p>
                <p className="text-xs text-gray-400">Used for formulary checks</p>
              </div>
              <select
                value={scheme}
                onChange={e => setScheme(e.target.value)}
                className="text-xs border border-gray-200 rounded-lg px-2.5 py-1.5 text-gray-700 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-violet-400"
              >
                <option>PMJAY</option>
                <option>CGHS</option>
                <option>ESI</option>
              </select>
            </div>
          </div>
        </div>

        {/* Security */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="flex items-center gap-3 px-5 py-4 border-b border-gray-50">
            <div className="w-8 h-8 rounded-xl bg-emerald-50 flex items-center justify-center">
              <Shield className="w-4 h-4 text-emerald-500" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-900">Security</p>
              <p className="text-xs text-gray-400">Manage account security settings</p>
            </div>
          </div>
          <div className="divide-y divide-gray-50">
            <button className="w-full flex items-center justify-between px-5 py-3.5 hover:bg-gray-50 transition-colors text-left">
              <div>
                <p className="text-sm text-gray-700">Change password</p>
                <p className="text-xs text-gray-400">Update your account password</p>
              </div>
              <ChevronRight className="w-4 h-4 text-gray-300" />
            </button>
            <button className="w-full flex items-center justify-between px-5 py-3.5 hover:bg-gray-50 transition-colors text-left">
              <div>
                <p className="text-sm text-gray-700">Active sessions</p>
                <p className="text-xs text-gray-400">View and revoke logged-in devices</p>
              </div>
              <ChevronRight className="w-4 h-4 text-gray-300" />
            </button>
          </div>
        </div>

        {/* Danger Zone */}
        <div className="bg-white rounded-2xl border border-red-100 shadow-sm overflow-hidden">
          <div className="flex items-center gap-3 px-5 py-4 border-b border-red-50">
            <div className="w-8 h-8 rounded-xl bg-red-50 flex items-center justify-center">
              <Trash2 className="w-4 h-4 text-red-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-900">Data</p>
              <p className="text-xs text-gray-400">Manage your stored data</p>
            </div>
          </div>
          <div className="divide-y divide-gray-50">
            <button className="w-full flex items-center justify-between px-5 py-3.5 hover:bg-red-50 transition-colors text-left group">
              <div>
                <p className="text-sm text-red-500 font-medium">Clear analysis history</p>
                <p className="text-xs text-gray-400">Permanently delete all saved analyses</p>
              </div>
              <ChevronRight className="w-4 h-4 text-red-300" />
            </button>
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <button
            onClick={handleSave}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 shadow-sm ${saved ? 'bg-emerald-500 text-white' : 'bg-gray-900 text-white hover:bg-gray-800'}`}
          >
            <Save className="w-4 h-4" />
            {saved ? 'Saved!' : 'Save changes'}
          </button>
        </div>
      </div>
    </div>
  );
};
