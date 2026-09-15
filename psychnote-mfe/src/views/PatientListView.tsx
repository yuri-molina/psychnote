import { useNavigate, NavLink } from 'react-router-dom';
import { Users, RefreshCw, AlertCircle, Search, ArrowLeft } from 'lucide-react';
import { usePatients } from '@/hooks/usePatients';
import { PatientCard } from '@/components/patient-card/PatientCard';

export const PatientListView: React.FC = () => {
  const navigate = useNavigate();
  const { patients, isLoading, isError, refetch } = usePatients();

  const handleViewRecord = (patientId: string) => {
    navigate(`/patients/${patientId}/record`);
  };

  const handleStartTriage = (patientId: string) => {
    navigate(`/patients/${patientId}/triage`);
  };

  return (
    <div className="psy-max-w-5xl psy-mx-auto psy-space-y-8 psy-px-4 psy-py-8">
      {/* Botão de Retorno */}
      <div>
        <NavLink
          to="/"
          className="psy-inline-flex psy-items-center psy-gap-2 psy-text-sm psy-font-medium psy-text-slate-600 hover:psy-text-primary psy-transition-colors focus:psy-outline-none focus:psy-ring-2 focus:psy-ring-primary psy-px-3 psy-py-1.5 psy-rounded-lg psy-bg-slate-100/80"
        >
          <ArrowLeft className="psy-w-4 psy-h-4" />
          <span>Voltar para o Menu Inicial</span>
        </NavLink>
      </div>

      {/* Header */}
      <header role="banner" className="psy-space-y-2">
        <div className="psy-flex psy-items-center psy-gap-2.5 psy-text-primary">
          <Users className="psy-w-6 psy-h-6" />
          <span className="psy-text-xs psy-font-bold psy-uppercase psy-tracking-wider">Prontuário Eletrônico / Evoluções</span>
        </div>
        <h1 className="psy-text-3xl psy-font-extrabold psy-text-slate-900">Listagem de Pacientes</h1>
        <p className="psy-text-slate-600 psy-text-sm">
          Selecione uma opção para visualizar o prontuário completo do paciente ou realizar uma nova evolução com triagem automatizada de risco.
        </p>
      </header>

      {/* Main Content */}
      <main role="main">
        {/* Loading State: Skeleton Cards */}
        {isLoading && (
          <div aria-live="polite" className="psy-space-y-4">
            <span className="psy-sr-only">Carregando lista de pacientes...</span>
            <div className="psy-grid psy-grid-cols-1 sm:psy-grid-cols-2 lg:psy-grid-cols-3 psy-gap-4">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div
                  key={i}
                  className="psy-p-5 psy-rounded-xl psy-border psy-border-slate-200 psy-bg-white psy-animate-pulse psy-space-y-3"
                >
                  <div className="psy-flex psy-items-center psy-gap-3">
                    <div className="psy-w-10 psy-h-10 psy-rounded-full psy-bg-slate-200" />
                    <div className="psy-space-y-1.5 psy-flex-1">
                      <div className="psy-h-4 psy-bg-slate-200 psy-rounded psy-w-3/4" />
                      <div className="psy-h-3 psy-bg-slate-100 psy-rounded psy-w-1/2" />
                    </div>
                  </div>
                  <div className="psy-h-3 psy-bg-slate-100 psy-rounded psy-w-full" />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Error State */}
        {isError && (
          <div
            role="alert"
            className="psy-p-6 psy-rounded-2xl psy-bg-red-50 psy-border psy-border-red-200 psy-text-red-950 psy-space-y-4 psy-text-center"
          >
            <AlertCircle className="psy-w-8 psy-h-8 psy-text-red-600 psy-mx-auto" />
            <div>
              <h2 className="psy-font-bold psy-text-base">Não foi possível carregar a lista de pacientes</h2>
              <p className="psy-text-sm psy-text-red-800 psy-mt-1">
                Verifique a conexão com o servidor BFF e tente novamente.
              </p>
            </div>
            <button
              onClick={() => refetch()}
              className="psy-inline-flex psy-items-center psy-gap-2 psy-px-4 psy-py-2 psy-rounded-xl psy-bg-red-600 psy-text-white psy-text-sm psy-font-semibold hover:psy-bg-red-700 focus:psy-outline-none focus:psy-ring-2 focus:psy-ring-red-500"
            >
              <RefreshCw className="psy-w-4 psy-h-4" />
              <span>Tentar novamente</span>
            </button>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !isError && patients.length === 0 && (
          <div className="psy-p-12 psy-rounded-2xl psy-bg-slate-50 psy-border psy-border-slate-200 psy-text-center psy-space-y-3">
            <Search className="psy-w-10 psy-h-10 psy-text-slate-400 psy-mx-auto" />
            <h2 className="psy-font-semibold psy-text-slate-700">Nenhum paciente encontrado no sistema.</h2>
            <p className="psy-text-xs psy-text-slate-500">Cadastre um novo paciente para iniciar.</p>
          </div>
        )}

        {/* Success State: Patient Grid */}
        {!isLoading && !isError && patients.length > 0 && (
          <ul role="list" className="psy-grid psy-grid-cols-1 sm:psy-grid-cols-2 lg:psy-grid-cols-3 psy-gap-4">
            {patients.map((patient) => (
              <li key={patient.patient_id} role="listitem">
                <PatientCard
                  patientId={patient.patient_id}
                  patient={patient}
                  onViewRecord={handleViewRecord}
                  onStartTriage={handleStartTriage}
                />
              </li>
            ))}
          </ul>
        )}
      </main>

      {/* Footer */}
      {!isLoading && !isError && patients.length > 0 && (
        <footer className="psy-pt-4 psy-text-xs psy-text-slate-500 psy-text-right">
          <span>{patients.length} paciente(s) localizado(s)</span>
        </footer>
      )}
    </div>
  );
};
