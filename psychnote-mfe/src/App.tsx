import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { LandingView } from '@/views/LandingView';
import { PatientListView } from '@/views/PatientListView';
import { NewPatientEvolutionView } from '@/views/NewPatientEvolutionView';
import { PatientRecordView } from '@/views/PatientRecordView';
import { TriageLayout } from '@/views/TriageLayout';

export const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<LandingView />} />
      <Route path="/patients" element={<PatientListView />} />
      <Route path="/patients/new-evolution" element={<NewPatientEvolutionView />} />
      <Route path="/patients/:patientId/record" element={<PatientRecordView />} />
      <Route path="/patients/:patientId/triage" element={<TriageLayout />} />
      <Route path="*" element={<LandingView />} />
    </Routes>
  );
};
