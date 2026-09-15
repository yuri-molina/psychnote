import { useQuery } from '@tanstack/react-query';
import { fetchPatientRecord } from '@/lib/api';
import { PatientRecord } from '@/lib/schemas';

export function usePatientRecord(patientId: string) {
  const query = useQuery<PatientRecord, Error>({
    queryKey: ['patientRecord', patientId],
    queryFn: () => fetchPatientRecord(patientId),
    enabled: !!patientId,
    staleTime: 0,
    refetchInterval: (query) => {
      const data = query.state.data;
      const hasPendingTriage =
        data?.active_job_id ||
        data?.history?.some((item) => item.has_triage === false || !item.risk_level);
      return hasPendingTriage ? 3000 : false;
    },
  });

  return {
    record: query.data || null,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
