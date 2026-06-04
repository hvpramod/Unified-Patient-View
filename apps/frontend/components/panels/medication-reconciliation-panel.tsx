"use client";

import { useState } from "react";
import { Loader2, RefreshCw, Pill, ChevronDown } from "lucide-react";
import { useMedReconciliationSummary, useConflicts, useResolveConflict, useActOnRecommendation } from "@/lib/api/hooks";
import { ConfidenceScore } from "@/components/shared/confidence-score";
import { FDADisclaimer } from "@/components/shared/fda-disclaimer";
import { SourceBadge } from "@/components/shared/source-badge";
import { ActionButtons } from "@/components/shared/action-buttons";
import { Badge } from "@/components/ui/badge";
import { severityVariant, formatDate } from "@/lib/utils";

export function MedicationReconciliationPanel({ patientId }: { patientId: string }) {
  const { data, isLoading, error, refetch } = useMedReconciliationSummary(patientId);
  const { data: conflictsData } = useConflicts(patientId);
  const resolveConflict = useResolveConflict();
  const actOnRec = useActOnRecommendation();
  const [acceptedRecs, setAcceptedRecs] = useState<Set<string>>(new Set());
  const [rejectedRecs, setRejectedRecs] = useState<Set<string>>(new Set());

  if (isLoading) return <div className="flex items-center gap-2 text-sm text-gray-400"><Loader2 className="h-4 w-4 animate-spin" />Loading reconciliation...</div>;
  if (error) return <div className="text-xs text-red-500">Failed to load reconciliation. <button onClick={() => refetch()} className="underline">Retry</button></div>;
  if (!data) return null;

  const content = data.content || {};
  const medConflicts = conflictsData?.conflicts?.filter((c: any) =>
    ["MEDICATION_DUPLICATE", "STATUS_MISMATCH", "DOSE_DISCREPANCY"].includes(c.conflict_type)
  ) ?? [];

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-sm font-semibold text-gray-800">Medication Reconciliation</h2>
          <p className="mt-0.5 text-xs text-gray-500">Generated {formatDate(data.generated_at)}</p>
        </div>
        <div className="flex items-center gap-2">
          <ConfidenceScore score={data.confidence_score} />
          <button onClick={() => refetch()} className="rounded p-1 text-gray-400 hover:bg-gray-100">
            <RefreshCw className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      <FDADisclaimer />

      {/* Active Conflicts */}
      {medConflicts.length > 0 && (
        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
            Detected Conflicts ({medConflicts.length})
          </h3>
          <div className="flex flex-col gap-2">
            {medConflicts.map((conflict: any) => (
              <div key={conflict.id} className="rounded border border-orange-100 bg-orange-50 px-3 py-2.5">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant={severityVariant(conflict.severity)}>{conflict.severity}</Badge>
                      <span className="text-xs font-medium text-gray-700">
                        {conflict.conflict_type.replace(/_/g, " ")}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600">{conflict.description}</p>
                    <div className="mt-1.5 flex gap-1">
                      {conflict.sources?.map((s: string) => <SourceBadge key={s} source={s} />)}
                    </div>
                  </div>
                </div>
                <div className="mt-2">
                  <ActionButtons
                    onAccept={async (annotation) => {
                      await resolveConflict.mutateAsync({ conflictId: conflict.id, patientId, action: "ACCEPT", annotation });
                    }}
                    onReject={async (annotation) => {
                      await resolveConflict.mutateAsync({ conflictId: conflict.id, patientId, action: "REJECT", annotation });
                    }}
                    disabled={resolveConflict.isPending}
                    accepted={!!conflict.resolved_at}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* AI Reconciliation Recommendations */}
      {content.reconciled_medications?.length > 0 && (
        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
            Reconciliation Recommendations
          </h3>
          <div className="flex flex-col gap-2">
            {content.reconciled_medications.map((med: any, i: number) => {
              const recId = `${data.summary_id}-rec-${i}`;
              return (
                <div key={i} className="rounded border border-gray-200 bg-white px-3 py-2.5">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Pill className="h-3.5 w-3.5 text-brand-600" />
                        <span className="text-xs font-medium text-gray-800">{med.drug_name}</span>
                        <span className={`text-xs px-1.5 rounded ${med.recommended_status === "active" ? "text-green-700 bg-green-50" : "text-gray-500 bg-gray-50"}`}>
                          → {med.recommended_status}
                        </span>
                      </div>
                      {med.recommended_dose && (
                        <p className="text-xs text-gray-500">Dose: {med.recommended_dose}</p>
                      )}
                      <p className="text-xs text-gray-500 mt-0.5">{med.rationale}</p>
                      <div className="mt-1.5 flex items-center gap-2">
                        {med.sources_used?.map((s: string) => <SourceBadge key={s} source={s} />)}
                        <ConfidenceScore score={med.confidence_score} showLabel={false} />
                      </div>
                    </div>
                  </div>
                  {med.requires_clinician_review && (
                    <div className="mt-2">
                      <ActionButtons
                        onAccept={async (annotation) => {
                          await actOnRec.mutateAsync({ recommendationId: recId, action: "ACCEPT", annotation });
                          setAcceptedRecs(prev => new Set([...prev, recId]));
                        }}
                        onReject={async (annotation) => {
                          await actOnRec.mutateAsync({ recommendationId: recId, action: "REJECT", annotation });
                          setRejectedRecs(prev => new Set([...prev, recId]));
                        }}
                        accepted={acceptedRecs.has(recId)}
                        rejected={rejectedRecs.has(recId)}
                      />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
}
