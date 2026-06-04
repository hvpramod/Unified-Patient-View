"use client";

import { useState } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { ClinicalSummaryPanel } from "@/components/panels/clinical-summary-panel";
import { MedicationReconciliationPanel } from "@/components/panels/medication-reconciliation-panel";
import { LabIntelligencePanel } from "@/components/panels/lab-intelligence-panel";
import { VisitPrepPanel } from "@/components/panels/visit-prep-panel";
import { PatientHeader } from "./patient-header";
import { usePatient } from "@/lib/api/hooks";
import { Loader2 } from "lucide-react";

interface UnifiedPatientViewProps {
  patientId: string;
  appointmentId?: string;
  compact?: boolean;
}

export function UnifiedPatientView({ patientId, appointmentId, compact }: UnifiedPatientViewProps) {
  const { data: patient, isLoading } = usePatient(patientId);

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-brand-600" />
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col bg-white">
      {patient && <PatientHeader patient={patient as any} />}

      <Tabs defaultValue="clinical" className="flex flex-1 flex-col overflow-hidden">
        <TabsList className="shrink-0 border-b border-gray-200 bg-white px-4 py-0 h-auto rounded-none justify-start gap-0">
          {[
            { value: "clinical", label: "Summary" },
            { value: "medications", label: "Medications" },
            { value: "labs", label: "Labs" },
            { value: "visit", label: "Visit Prep" },
          ].map((tab) => (
            <TabsTrigger
              key={tab.value}
              value={tab.value}
              className="rounded-none border-b-2 border-transparent px-4 py-2.5 text-xs font-medium text-gray-500 data-[state=active]:border-brand-600 data-[state=active]:text-brand-700 data-[state=active]:bg-transparent"
            >
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>

        <div className="flex-1 overflow-y-auto p-4">
          <TabsContent value="clinical" className="mt-0">
            <ClinicalSummaryPanel patientId={patientId} />
          </TabsContent>
          <TabsContent value="medications" className="mt-0">
            <MedicationReconciliationPanel patientId={patientId} />
          </TabsContent>
          <TabsContent value="labs" className="mt-0">
            <LabIntelligencePanel patientId={patientId} />
          </TabsContent>
          <TabsContent value="visit" className="mt-0">
            <VisitPrepPanel patientId={patientId} apptId={appointmentId} />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}
