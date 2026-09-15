import React, { useEffect } from 'react';
import { useParams, useNavigate, NavLink } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Stethoscope, User, Calendar, FileText, AlertTriangle, ShieldCheck, AlertCircle, RefreshCw } from 'lucide-react';
import { usePatientRecord } from '@/hooks/usePatientRecord';
import { ClinicalRiskBadge } from '@/components/clinical-risk-badge/ClinicalRiskBadge';
import { AuditAlerts } from '@/components/audit-alerts/AuditAlerts';
import { subscribeTriageStream, registerPatient } from '@/lib/api';

export const PatientRecordView: React.FC = () => {
  const { patientId = 'PAC-UNKNOWN' } = useParams<{ patientId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { record, isLoading, isError, refetch } = usePatientRecord(patientId);

  const pendingItem = record?.history.find((h) => h.has_triage === false || !h.risk_level);
  const activeJobId = record?.active_job_id || pendingItem?.id;

  useEffect(() => {
    if (!activeJobId || !patientId) return;

    // Escuta ativamente o canal SSE enquanto a triagem estiver pendente
    const unsubscribe = subscribeTriageStream(
      activeJobId,
      patientId,
      (completedData) => {
        registerPatient(
          {
            patient_id: patientId,
            name: record?.name || `Paciente ${patientId}`,
            last_triage_date: new Date().toISOString().split('T')[0],
            last_risk_level: completedData.risk_assessment.risk_level,
          },
          undefined,
          completedData,
          activeJobId
        );
        queryClient.invalidateQueries({ queryKey: ['patientRecord', patientId] });
        queryClient.invalidateQueries({ queryKey: ['patients'] });
      },
      (err) => {
        console.warn('SSE finalizado ou alternando para polling no prontuário:', err);
      }
    );

    return () => {
      unsubscribe();
    };
  }, [activeJobId, patientId, record?.name, queryClient]);

  const handleStartTriage = () => {
    navigate(`/patients/${patientId}/triage`);
  };

  const displayName = record?.name || `Paciente ${patientId}`;

  const formatDate = (rawDate?: string) => {
    if (!rawDate) return 'Data recente';
    try {
      const parsed = new Date(rawDate);
      if (isNaN(parsed.getTime())) return rawDate;
      return parsed.toLocaleString('pt-BR');
    } catch {
      return rawDate;
    }
  };

  return (
    <div className="psy-max-w-4xl psy-mx-auto psy-px-4 psy-py-8 psy-space-y-6">
      {/* Navegação de Retorno */}
      <div>
        <NavLink
          to="/patients"
          className="psy-inline-flex psy-items-center psy-gap-2 psy-text-sm psy-font-medium psy-text-slate-600 hover:psy-text-primary psy-transition-colors focus:psy-outline-none focus:psy-ring-2 focus:psy-ring-primary psy-px-3 psy-py-1.5 psy-rounded-lg psy-bg-slate-100/80"
        >
          <ArrowLeft className="psy-w-4 psy-h-4" />
          <span>Voltar para a Listagem de Pacientes</span>
        </NavLink>
      </div>

      {/* Cabeçalho do Prontuário */}
      <header className="psy-bg-white psy-p-6 psy-rounded-2xl psy-border psy-border-slate-200 psy-shadow-sm psy-flex psy-flex-col sm:psy-flex-row sm:psy-items-center psy-justify-between psy-gap-4">
        <div className="psy-flex psy-items-center psy-gap-4">
          <div className="psy-w-12 psy-h-12 psy-rounded-full psy-bg-primary/10 psy-flex psy-items-center psy-justify-center psy-text-primary psy-shrink-0">
            <User className="psy-w-6 psy-h-6" />
          </div>
          <div>
            <span className="psy-text-xs psy-font-mono psy-text-slate-500 psy-uppercase psy-tracking-wider">Prontuário Psiquiátrico</span>
            <h1 className="psy-text-2xl psy-font-bold psy-text-slate-900">{displayName}</h1>
          </div>
        </div>

        <button
          onClick={handleStartTriage}
          className="psy-inline-flex psy-items-center psy-justify-center psy-gap-2 psy-px-5 psy-py-2.5 psy-rounded-xl psy-font-semibold psy-text-sm psy-text-white psy-bg-primary hover:psy-bg-primary/90 focus:psy-outline-none focus:psy-ring-2 focus:psy-ring-primary psy-transition-all psy-shadow-sm"
        >
          <Stethoscope className="psy-w-4 psy-h-4" />
          <span>+ Iniciar Nova Evolução</span>
        </button>
      </header>

      {/* Main Content */}
      <main className="psy-space-y-6">
        {/* Loading State */}
        {isLoading && (
          <div aria-live="polite" className="psy-p-8 psy-rounded-2xl psy-bg-white psy-border psy-border-slate-200 psy-animate-pulse psy-space-y-4">
            <div className="psy-h-6 psy-bg-slate-200 psy-rounded psy-w-1/3" />
            <div className="psy-h-20 psy-bg-slate-100 psy-rounded" />
            <div className="psy-h-20 psy-bg-slate-100 psy-rounded" />
          </div>
        )}

        {/* Error State */}
        {isError && (
          <div role="alert" className="psy-p-6 psy-rounded-2xl psy-bg-red-50 psy-border psy-border-red-200 psy-text-red-950 psy-space-y-4 psy-text-center">
            <AlertCircle className="psy-w-8 psy-h-8 psy-text-red-600 psy-mx-auto" />
            <div>
              <h2 className="psy-font-bold psy-text-base">Não foi possível carregar o prontuário do paciente</h2>
              <p className="psy-text-sm psy-text-red-800 psy-mt-1">Tente novamente ou verifique a conexão com a API.</p>
            </div>
            <button
              onClick={() => refetch()}
              className="psy-inline-flex psy-items-center psy-gap-2 psy-px-4 psy-py-2 psy-rounded-xl psy-bg-red-600 psy-text-white psy-text-sm psy-font-semibold hover:psy-bg-red-700"
            >
              <RefreshCw className="psy-w-4 psy-h-4" />
              <span>Tentar novamente</span>
            </button>
          </div>
        )}

        {/* Success State: Timeline de Histórico de Triagens */}
        {!isLoading && !isError && record && (
          <section aria-labelledby="history-section-title" className="psy-space-y-6">
            <div className="psy-flex psy-items-center psy-justify-between">
              <h2 id="history-section-title" className="psy-text-lg psy-font-bold psy-text-slate-900 psy-flex psy-items-center psy-gap-2">
                <FileText className="psy-w-5 psy-h-5 psy-text-primary" />
                <span>Histórico de Evoluções</span>
              </h2>
              <span className="psy-text-xs psy-text-slate-500">
                {record.history.length} registro(s) encontrado(s)
              </span>
            </div>

            {record.history.length === 0 ? (
              <div className="psy-p-8 psy-rounded-2xl psy-bg-slate-50 psy-border psy-border-slate-200 psy-text-center">
                <p className="psy-text-sm psy-text-slate-600">Nenhuma evolução registrada anteriormente para este paciente.</p>
                <button
                  onClick={handleStartTriage}
                  className="psy-mt-3 psy-inline-flex psy-items-center psy-gap-2 psy-px-4 psy-py-2 psy-rounded-xl psy-bg-primary psy-text-white psy-text-xs psy-font-semibold"
                >
                  <Stethoscope className="psy-w-3.5 psy-h-3.5" />
                  <span>Realizar Primeira Evolução</span>
                </button>
              </div>
            ) : (
              <div className="psy-space-y-6">
                {record.history.map((triage, index) => {
                  const rawDate = triage.date || triage.timestamp;
                  const noteContent = triage.current_note || triage.note_text || 'Nota clínica não registrada.';
                  const isPendingTriage = triage.has_triage === false || !triage.risk_level;

                  return (
                    <article
                      key={index}
                      className="psy-p-6 psy-rounded-2xl psy-bg-white psy-border psy-border-slate-200 psy-shadow-sm psy-space-y-4"
                    >
                      {/* Topo do Item do Histórico */}
                      <div className="psy-flex psy-flex-col sm:psy-flex-row sm:psy-items-center psy-justify-between psy-gap-2 psy-pb-4 psy-border-b psy-border-slate-100">
                        <div className="psy-flex psy-items-center psy-gap-2 psy-text-xs psy-text-slate-500">
                          <Calendar className="psy-w-4 psy-h-4 psy-text-slate-400" />
                          <span>Data da Avaliação: {formatDate(rawDate)}</span>
                        </div>
                        {isPendingTriage ? (
                          <div className="psy-inline-flex psy-items-center psy-gap-1.5 psy-px-3 psy-py-1 psy-rounded-full psy-bg-amber-50 psy-border psy-border-amber-200 psy-text-amber-800 psy-text-xs psy-font-semibold psy-animate-pulse">
                            <RefreshCw className="psy-w-3.5 psy-h-3.5 psy-animate-spin psy-text-amber-600" />
                            <span>Análise de Risco em Andamento...</span>
                          </div>
                        ) : (
                          <ClinicalRiskBadge riskLevel={triage.risk_level || 'Moderado'} size="sm" />
                        )}
                      </div>

                      {/* Nota Clínica Original */}
                      <div className="psy-space-y-1">
                        <span className="psy-text-xs psy-font-bold psy-uppercase psy-tracking-wider psy-text-slate-500">
                          Evolução Registrada:
                        </span>
                        <p className="psy-text-sm psy-text-slate-800 psy-italic psy-bg-slate-50 psy-p-3 psy-rounded-lg psy-border psy-border-slate-200">
                          "{noteContent}"
                        </p>
                      </div>

                      {/* Bloco quando a triagem está em andamento pela IA */}
                      {isPendingTriage ? (
                        <div className="psy-p-4 psy-rounded-xl psy-bg-amber-50/60 psy-border psy-border-amber-200/80 psy-space-y-2">
                          <div className="psy-flex psy-items-center psy-gap-2 psy-text-amber-900 psy-text-xs psy-font-bold">
                            <RefreshCw className="psy-w-3.5 psy-h-3.5 psy-animate-spin psy-text-amber-600" />
                            <span>Aguardando conclusão da triagem automatizada de risco por IA</span>
                          </div>
                          <p className="psy-text-xs psy-text-amber-800 psy-leading-relaxed">
                            A evolução clínica foi salva no prontuário. O nível de risco, os fatores determinantes (Red Flags), fatores de proteção e os pareceres de auditoria estão sendo analisados e serão atualizados automaticamente.
                          </p>
                        </div>
                      ) : (
                        <>
                          {/* Red Flags & Fatores de Proteção */}
                          <div className="psy-grid psy-grid-cols-1 md:psy-grid-cols-2 psy-gap-4">
                            {triage.red_flags.length > 0 && (
                              <div className="psy-space-y-2">
                                <span className="psy-text-xs psy-font-bold psy-uppercase psy-tracking-wider psy-text-red-600 psy-flex psy-items-center psy-gap-1">
                                  <AlertTriangle className="psy-w-3.5 psy-h-3.5" /> Red Flags Detectadas
                                </span>
                                <ul role="list" className="psy-space-y-1">
                                  {triage.red_flags.map((flag, idx) => (
                                    <li key={idx} className="psy-text-xs psy-text-red-900 psy-bg-red-50 psy-p-2 psy-rounded psy-border psy-border-red-100">
                                      • {flag}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {triage.protection_factors.length > 0 && (
                              <div className="psy-space-y-2">
                                <span className="psy-text-xs psy-font-bold psy-uppercase psy-tracking-wider psy-text-green-700 psy-flex psy-items-center psy-gap-1">
                                  <ShieldCheck className="psy-w-3.5 psy-h-3.5" /> Fatores de Proteção
                                </span>
                                <ul role="list" className="psy-space-y-1">
                                  {triage.protection_factors.map((factor, idx) => (
                                    <li key={idx} className="psy-text-xs psy-text-green-900 psy-bg-green-50 psy-p-2 psy-rounded psy-border psy-border-green-100">
                                      ✓ {factor}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>

                          {/* Justificativa Clínica */}
                          {triage.clinical_justification && (
                            <div className="psy-space-y-1">
                              <span className="psy-text-xs psy-font-bold psy-uppercase psy-tracking-wider psy-text-slate-500">
                                Justificativa Clínica:
                              </span>
                              <p className="psy-text-xs psy-text-slate-700 psy-leading-relaxed">
                                {triage.clinical_justification}
                              </p>
                            </div>
                          )}

                          {/* Alertas de Auditoria */}
                          {triage.audit_alerts.length > 0 && (
                            <div className="psy-pt-2">
                              <AuditAlerts alerts={triage.audit_alerts} />
                            </div>
                          )}
                        </>
                      )}
                    </article>
                  );
                })}
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
};
