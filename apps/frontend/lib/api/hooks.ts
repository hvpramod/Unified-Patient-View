"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useMsal } from "@azure/msal-react";
import { loginRequest } from "@/lib/auth/msal-config";
import { apiGet, apiPatch, apiPost } from "./client";

function useToken() {
  const { instance, accounts } = useMsal();
  return async () => {
    if (!accounts[0]) return "";
    try {
      const result = await instance.acquireTokenSilent({ ...loginRequest, account: accounts[0] });
      return result.accessToken;
    } catch {
      return "";
    }
  };
}

export function usePatient(patientId: string) {
  const getToken = useToken();
  return useQuery({
    queryKey: ["patient", patientId],
    queryFn: async () => {
      const token = await getToken();
      return apiGet(`/patients/${patientId}`, token);
    },
    enabled: !!patientId,
  });
}

export function usePatientTimeline(patientId: string) {
  const getToken = useToken();
  return useQuery({
    queryKey: ["timeline", patientId],
    queryFn: async () => {
      const token = await getToken();
      return apiGet(`/patients/${patientId}/timeline`, token);
    },
    enabled: !!patientId,
  });
}

export function useMedications(patientId: string) {
  const getToken = useToken();
  return useQuery({
    queryKey: ["medications", patientId],
    queryFn: async () => {
      const token = await getToken();
      return apiGet(`/patients/${patientId}/medications`, token);
    },
    enabled: !!patientId,
  });
}

export function useLabs(patientId: string) {
  const getToken = useToken();
  return useQuery({
    queryKey: ["labs", patientId],
    queryFn: async () => {
      const token = await getToken();
      return apiGet(`/patients/${patientId}/labs`, token);
    },
    enabled: !!patientId,
  });
}

export function useConflicts(patientId: string) {
  const getToken = useToken();
  return useQuery({
    queryKey: ["conflicts", patientId],
    queryFn: async () => {
      const token = await getToken();
      return apiGet(`/patients/${patientId}/conflicts`, token);
    },
    enabled: !!patientId,
    refetchInterval: 30_000,
  });
}

export function useClinicalSummary(patientId: string) {
  const getToken = useToken();
  return useQuery({
    queryKey: ["summary", "CLINICAL", patientId],
    queryFn: async () => {
      const token = await getToken();
      return apiGet(`/patients/${patientId}/summary/clinical`, token);
    },
    enabled: !!patientId,
  });
}

export function useMedReconciliationSummary(patientId: string) {
  const getToken = useToken();
  return useQuery({
    queryKey: ["summary", "MEDICATION_RECONCILIATION", patientId],
    queryFn: async () => {
      const token = await getToken();
      return apiGet(`/patients/${patientId}/summary/medication-reconciliation`, token);
    },
    enabled: !!patientId,
  });
}

export function useLabIntelligenceSummary(patientId: string) {
  const getToken = useToken();
  return useQuery({
    queryKey: ["summary", "LAB_INTELLIGENCE", patientId],
    queryFn: async () => {
      const token = await getToken();
      return apiGet(`/patients/${patientId}/summary/lab-intelligence`, token);
    },
    enabled: !!patientId,
  });
}

export function useVisitPrepSummary(patientId: string, apptId?: string) {
  const getToken = useToken();
  return useQuery({
    queryKey: ["summary", "VISIT_PREP", patientId, apptId],
    queryFn: async () => {
      const token = await getToken();
      const qs = apptId ? `?appt_id=${apptId}` : "";
      return apiGet(`/patients/${patientId}/summary/visit-prep${qs}`, token);
    },
    enabled: !!patientId,
  });
}

export function useResolveConflict() {
  const getToken = useToken();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ conflictId, patientId, action, annotation }: { conflictId: string; patientId: string; action: string; annotation?: string }) => {
      const token = await getToken();
      return apiPatch(`/conflicts/${conflictId}`, token, { action, annotation });
    },
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ["conflicts", variables.patientId] });
    },
  });
}

export function useActOnRecommendation() {
  const getToken = useToken();
  return useMutation({
    mutationFn: async ({ recommendationId, action, annotation }: { recommendationId: string; action: string; annotation?: string }) => {
      const token = await getToken();
      return apiPost(`/recommendations/${recommendationId}/action`, token, { action, annotation });
    },
  });
}
