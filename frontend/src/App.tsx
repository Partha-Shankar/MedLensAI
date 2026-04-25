import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { LandingPage } from './components/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { SignupPage } from './pages/SignupPage';
import { HistoryPage } from './pages/HistoryPage';
import { ProfilePage } from './pages/ProfilePage';
import { PublicMedicalCardPage } from './pages/PublicMedicalCardPage';
import { SettingsPage } from './pages/SettingsPage';
import { NotificationsPage } from './pages/NotificationsPage';
import { HelpPage } from './pages/HelpPage';
import { Layout } from './components/Layout';
import { UploadScreen } from './components/UploadScreen';
import { ProcessingScreen } from './components/ProcessingScreen';
import { ConfirmationScreen } from './components/ConfirmationScreen';
import { ResultsScreen } from './components/ResultsScreen';
import { TimelineScreen } from './components/TimelineScreen';
import type { ExtractionResponse } from './lib/types';
import { api } from './lib/api';

type AppState = 'upload' | 'processing' | 'confirmation' | 'results' | 'timeline';

export interface PatientProfile {
  name: string; age: string; sex: string; conditions: string[]; allergies: string;
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('medlens_token');
  if (!token) return <Navigate to="/login" replace />;
  return <Layout>{children}</Layout>;
}

function PrescriptionAnalyzer() {
  const [appState, setAppState] = useState<AppState>('upload');
  const [patientProfile, setPatientProfile] = useState<PatientProfile>({ name: '', age: '', sex: '', conditions: [], allergies: '' });
  const [extractionData, setExtractionData] = useState<ExtractionResponse | null>(null);
  const [clinicalData, setClinicalData] = useState<any>(null);
  const location = useLocation();
  const navigate = useNavigate();

  // Handle data passed from history page
  useEffect(() => {
    if (location.state?.prescription) {
      const p = location.state.prescription;
      setExtractionData({ success: true, prescription: p, raw_ocr_lines: [], processing_time_ms: 0, errors: [] });
      setPatientProfile({ name: p.patient_name || '', age: p.patient_age || '', sex: p.sex || '', conditions: [], allergies: '' });
      setClinicalData({ interactions: { conflicts: p.interactions || [], has_critical: (p.interactions || []).length > 0 }, validity: { score: p.validity_score, criteria: [], legally_complete: true } });
      setAppState('results');
      navigate(location.pathname, { replace: true, state: {} });
    }
  }, [location.state, navigate]);

  const handleAnalyze = async (file: File, profile: PatientProfile) => {
    setPatientProfile(profile);
    setAppState('processing');
    try {
      const data = await api.extract(file);
      setExtractionData(data);
      setAppState('confirmation');
    } catch (err) {
      console.error(err);
      alert('Extraction failed. Check that the backend is running on port 8000.');
      setAppState('upload');
    }
  };

  const handleConfirmAndProceed = async (updatedPrescription: any) => {
    setAppState('processing');
    try {
      const p = updatedPrescription;
      const drugNames = p.Medications.map((m: any) => m.DrugName).filter(Boolean);
      const frequencies = p.Medications.map((m: any) => m.Frequency);
      const doses = p.Medications.map((m: any) => `${m.DoseValue} ${m.DoseUnit}`);
      const [dosageSanity, interactions, validity, foodWarnings, insurance, timeline] = await Promise.all([
        api.checkDosageSanity(p.Medications, patientProfile.age, patientProfile.conditions).catch(() => null),
        api.checkInteractions(drugNames).catch(() => null),
        api.checkValidity(p, false).catch(() => null),
        api.getFoodWarnings(drugNames).catch(() => null),
        api.getInsuranceSummary(drugNames).catch(() => null),
        api.getTimeline(drugNames, frequencies, doses).catch(() => null),
      ]);
      setClinicalData({ dosageSanity, interactions, validity, foodWarnings, insurance, timeline });
      setExtractionData(prev => prev ? { ...prev, prescription: p } : null);
      setAppState('results');
    } catch (err) {
      console.error(err);
      setAppState('results');
    }
  };

  return (
    <>
      {appState === 'upload' && <UploadScreen onAnalyze={handleAnalyze} />}
      {appState === 'processing' && <ProcessingScreen />}
      {appState === 'confirmation' && extractionData && <ConfirmationScreen data={extractionData} onConfirm={handleConfirmAndProceed} />}
      {appState === 'results' && extractionData && clinicalData && (
        <ResultsScreen prescription={extractionData.prescription} clinicalData={clinicalData} patientProfile={patientProfile} onViewTimeline={() => setAppState('timeline')} />
      )}
      {appState === 'timeline' && clinicalData?.timeline && extractionData && (
        <TimelineScreen timelineResult={clinicalData.timeline} medications={extractionData.prescription.Medications} onBack={() => setAppState('results')} />
      )}
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/card/:userId" element={<PublicMedicalCardPage />} />
        <Route path="/app" element={<ProtectedRoute><PrescriptionAnalyzer /></ProtectedRoute>} />
        <Route path="/history" element={<ProtectedRoute><HistoryPage /></ProtectedRoute>} />
        <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
        <Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
        <Route path="/notifications" element={<ProtectedRoute><NotificationsPage /></ProtectedRoute>} />
        <Route path="/help" element={<ProtectedRoute><HelpPage /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
