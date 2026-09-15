import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Stethoscope, Users, ShieldCheck, Sparkles, Activity, FileText, ChevronRight } from 'lucide-react';

export const LandingView: React.FC = () => {
  const navigate = useNavigate();

  const handleEvoluirNovoPaciente = () => {
    navigate('/patients/new-evolution');
  };

  const handleListarPacientes = () => {
    navigate('/patients');
  };

  return (
    <div className="psy-max-w-6xl psy-mx-auto psy-px-4 psy-py-12 psy-space-y-12">
      {/* Hero Section */}
      <header className="psy-text-center psy-space-y-4 psy-max-w-3xl psy-mx-auto">
        <div className="psy-inline-flex psy-items-center psy-gap-2 psy-px-3.5 psy-py-1.5 psy-rounded-full psy-bg-primary/10 psy-text-primary psy-text-xs psy-font-semibold">
          <Sparkles className="psy-w-4 psy-h-4" />
          <span>Inteligência Artificial Psiquiátrica & Triagem Clínica</span>
        </div>
        <h1 className="psy-text-4xl md:psy-text-5xl psy-font-extrabold psy-text-slate-900 psy-tracking-tight">
          Psych Note
        </h1>
        <p className="psy-text-slate-600 psy-text-base md:psy-text-lg psy-leading-relaxed">
          Plataforma para suporte à decisão clínica, triagem automatizada de risco de autoextermínio e auditoria de conduta sob diretrizes médicas.
        </p>
      </header>

      {/* Main Actions Grid (2 Hero CTAs) */}
      <main role="main" className="psy-grid psy-grid-cols-1 md:psy-grid-cols-2 psy-gap-8 psy-max-w-4xl psy-mx-auto">
        {/* Card 1: Evoluir Novo Paciente */}
        <div
          onClick={handleEvoluirNovoPaciente}
          className="psy-group psy-relative psy-p-8 psy-rounded-2xl psy-bg-white psy-border-2 psy-border-primary/20 hover:psy-border-primary psy-shadow-sm hover:psy-shadow-xl psy-transition-all psy-cursor-pointer psy-flex psy-flex-col psy-justify-between psy-gap-6"
        >
          <div className="psy-space-y-4">
            <div className="psy-w-14 psy-h-14 psy-rounded-2xl psy-bg-primary psy-text-white psy-flex psy-items-center psy-justify-center psy-shadow-md group-hover:psy-scale-105 psy-transition-transform">
              <Stethoscope className="psy-w-7 psy-h-7" />
            </div>

            <div>
              <div className="psy-flex psy-items-center psy-justify-between">
                <h2 className="psy-text-2xl psy-font-bold psy-text-slate-900 group-hover:psy-text-primary psy-transition-colors">
                  Evoluir Novo Paciente
                </h2>
                <ChevronRight className="psy-w-5 psy-h-5 psy-text-slate-400 group-hover:psy-text-primary group-hover:psy-translate-x-1 psy-transition-all" />
              </div>
              <p className="psy-text-sm psy-text-slate-600 psy-mt-2 psy-leading-relaxed">
                Cadastre ou identifique um novo paciente e redija a evolução médica atual para triagem automatizada de risco por IA.
              </p>
            </div>
          </div>

          <div className="psy-pt-4 psy-border-t psy-border-slate-100">
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                handleEvoluirNovoPaciente();
              }}
              className="psy-w-full psy-inline-flex psy-items-center psy-justify-center psy-gap-2 psy-py-3.5 psy-px-6 psy-rounded-xl psy-font-semibold psy-text-sm psy-text-white psy-bg-primary hover:psy-bg-primary/90 psy-shadow-sm focus:psy-outline-none focus:psy-ring-2 focus:psy-ring-primary psy-transition-all"
            >
              <span>+ Iniciar Nova Evolução</span>
            </button>
          </div>
        </div>

        {/* Card 2: Listar Pacientes */}
        <div
          onClick={handleListarPacientes}
          className="psy-group psy-relative psy-p-8 psy-rounded-2xl psy-bg-white psy-border psy-border-slate-200 hover:psy-border-slate-400 psy-shadow-sm hover:psy-shadow-xl psy-transition-all psy-cursor-pointer psy-flex psy-flex-col psy-justify-between psy-gap-6"
        >
          <div className="psy-space-y-4">
            <div className="psy-w-14 psy-h-14 psy-rounded-2xl psy-bg-slate-100 psy-text-slate-700 psy-flex psy-items-center psy-justify-center group-hover:psy-bg-slate-200 psy-transition-colors">
              <Users className="psy-w-7 psy-h-7" />
            </div>

            <div>
              <div className="psy-flex psy-items-center psy-justify-between">
                <h2 className="psy-text-2xl psy-font-bold psy-text-slate-900 group-hover:psy-text-slate-700 psy-transition-colors">
                  Listar Pacientes
                </h2>
                <ChevronRight className="psy-w-5 psy-h-5 psy-text-slate-400 group-hover:psy-text-slate-700 group-hover:psy-translate-x-1 psy-transition-all" />
              </div>
              <p className="psy-text-sm psy-text-slate-600 psy-mt-2 psy-leading-relaxed">
                Consulte a lista de pacientes cadastrados, prontuários psiquiátricos e histórico de evoluções e triagens passadas.
              </p>
            </div>
          </div>

          <div className="psy-pt-4 psy-border-t psy-border-slate-100">
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                handleListarPacientes();
              }}
              className="psy-w-full psy-inline-flex psy-items-center psy-justify-center psy-gap-2 psy-py-3.5 psy-px-6 psy-rounded-xl psy-font-semibold psy-text-sm psy-text-slate-700 psy-bg-slate-100 hover:psy-bg-slate-200 focus:psy-outline-none focus:psy-ring-2 focus:psy-ring-primary psy-transition-all"
            >
              <span>Ver Lista de Pacientes</span>
            </button>
          </div>
        </div>
      </main>

      {/* Feature Badges & Compliance */}
      <footer className="psy-pt-8 psy-border-t psy-border-slate-200 psy-max-w-4xl psy-mx-auto psy-grid psy-grid-cols-1 sm:psy-grid-cols-3 psy-gap-4 psy-text-center">
        <div className="psy-flex psy-items-center psy-justify-center psy-gap-2 psy-text-xs psy-text-slate-500">
          <ShieldCheck className="psy-w-4 psy-h-4 psy-text-green-600" />
          <span>Conformidade LGPD (Processamento local em memória)</span>
        </div>

        <div className="psy-flex psy-items-center psy-justify-center psy-gap-2 psy-text-xs psy-text-slate-500">
          <Activity className="psy-w-4 psy-h-4 psy-text-blue-600" />
          <span>Streaming SSE em Tempo Real (EventSource)</span>
        </div>

        <div className="psy-flex psy-items-center psy-justify-center psy-gap-2 psy-text-xs psy-text-slate-500">
          <FileText className="psy-w-4 psy-h-4 psy-text-purple-600" />
          <span>Auditoria Médica CFM & Botega</span>
        </div>
      </footer>
    </div>
  );
};
