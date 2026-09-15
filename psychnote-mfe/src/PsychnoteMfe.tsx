import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider, useQueryClient } from '@tanstack/react-query';
import { App } from './App';
import './index.css';

const localQueryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const InternalAppWrapper: React.FC = () => {
  return (
    <div className="psychnote-mfe-root psy-min-h-screen psy-bg-slate-50/50">
      <App />
    </div>
  );
};

export const PsychnoteMfe: React.FC = () => {
  let hasHostQueryClient = true;
  try {
    useQueryClient();
  } catch {
    hasHostQueryClient = false;
  }

  if (hasHostQueryClient) {
    return (
      <BrowserRouter>
        <InternalAppWrapper />
      </BrowserRouter>
    );
  }

  return (
    <QueryClientProvider client={localQueryClient}>
      <BrowserRouter>
        <InternalAppWrapper />
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default PsychnoteMfe;
