"use client";

import { useSearchParams } from "next/navigation";
import { useIsAuthenticated, useMsal } from "@azure/msal-react";
import { loginRequest } from "@/lib/auth/msal-config";
import { UnifiedPatientView } from "@/components/patient/unified-patient-view";
import { Suspense } from "react";

function EmbedContent() {
  const searchParams = useSearchParams();
  const patientId = searchParams.get("patient_id") || "";
  const appointmentId = searchParams.get("appt_id") || undefined;
  const isAuthenticated = useIsAuthenticated();
  const { instance } = useMsal();

  if (!isAuthenticated) {
    return (
      <div className="flex h-full items-center justify-center p-4">
        <button
          onClick={() => instance.loginPopup(loginRequest)}
          className="rounded bg-brand-600 px-4 py-2 text-sm text-white hover:bg-brand-700"
        >
          Sign in
        </button>
      </div>
    );
  }

  if (!patientId) {
    return <div className="p-4 text-xs text-gray-400">patient_id required</div>;
  }

  return <UnifiedPatientView patientId={patientId} appointmentId={appointmentId} compact />;
}

export default function EmbedPage() {
  return (
    <div className="h-screen">
      <Suspense fallback={<div className="flex h-full items-center justify-center text-xs text-gray-400">Loading...</div>}>
        <EmbedContent />
      </Suspense>
    </div>
  );
}
