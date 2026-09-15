import { useQuery } from '@tanstack/react-query';
import { fetchPatients } from '@/lib/api';
import { Patient } from '@/lib/schemas';

export function usePatients() {
  const query = useQuery<Patient[], Error>({
    queryKey: ['patients'],
    queryFn: fetchPatients,
    staleTime: 1000 * 60 * 5, // 5 minutos de cache em memória (LGPD safe - não persiste no disk)
  });

  return {
    patients: query.data || [],
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
