"use client";

/**
 * Demo page — loads the real UnifiedPatientView component
 * pointed at the seeded Margaret Thompson patient.
 *
 * Auth is bypassed in dev mode (AZURE_CLIENT_ID is empty).
 * The API client sends a "demo-token" Bearer token which the
 * gateway-api accepts without verification when in dev mode.
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { UnifiedPatientView } from "@/components/patient/unified-patient-view";
import { useState } from "react";

// Fixed patient ID created by the seed script
const DEMO_PATIENT_ID = "a1b2c3d4-0000-0000-0000-000000000001";

// Inject a demo Bearer token so the API client always has auth headers in dev mode
if (typeof window !== "undefined") {
  (window as any).__UPV_DEMO_TOKEN__ = "demo-token";
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      retry: 1,
      // Use a global fetcher that injects the demo token
    },
  },
});

export default function DemoPage() {
  return (
    <QueryClientProvider client={queryClient}>
      <DemoShell />
    </QueryClientProvider>
  );
}

function DemoShell() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  return (
    <div className="h-screen flex flex-col bg-white">
      {/* Demo banner */}
      <div className="shrink-0 flex items-center justify-between bg-brand-900 px-4 py-1.5 text-xs text-white">
        <span className="font-semibold tracking-wide uppercase">UPV Demo Mode</span>
        <span className="text-blue-200">
          Data served live from API &nbsp;·&nbsp; {apiUrl} &nbsp;·&nbsp;
          <a
            href={`${apiUrl}/api/docs`}
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:text-white"
          >
            Swagger Docs ↗
          </a>
        </span>
      </div>

      {/* Real patient view — calls actual gateway API */}
      <div className="flex-1 overflow-hidden">
        <UnifiedPatientView patientId={DEMO_PATIENT_ID} />
      </div>
    </div>
  );
}
