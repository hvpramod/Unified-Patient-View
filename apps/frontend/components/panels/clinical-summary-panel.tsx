"use client";

import { Loader2, RefreshCw, ChevronDown } from "lucide-react";
import { useClinicalSummary } from "@/lib/api/hooks";
import { ConfidenceScore } from "@/components/shared/confidence-score";
import { FDADisclaimer } from "@/components/shared/fda-disclaimer";
import { Badge } from "@/components/ui/badge";
import { severityVariant, formatDate } from "@/lib/utils";
import { useState } from "react";

export function ClinicalSummaryPanel({ patientId }: { patientId: string }) {
  const { data, isLoading, error, refetch } = useClinicalSummary(patientId);
  const [showReasoning, setShowReasoning] = useState(false);

  if (isLoading) return <PanelSkeleton label="Clinical Summary" />;
  if (error) return <PanelError label="Clinical Summary" onRetry={refetch} />;
  if (!data) return null;

  const content = data.content || {};

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-sm font-semibold text-gray-800">Clinical Summary</h2>
          <p className="mt-0.5 text-xs text-gray-500">
            Generated {formatDate(data.generated_at)} · {data.model_used}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <ConfidenceScore score={data.confidence_score} />
          <button onClick={() => refetch()} className="rounded p-1 text-gray-400 hover:bg-gray-100">
            <RefreshCw className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      <FDADisclaimer />

      {content.patient_overview && (
        <div className="rounded-lg border border-gray-100 bg-gray-50 px-3 py-2.5">
          <p className="text-xs text-gray-700 leading-relaxed">{content.patient_overview}</p>
        </div>
      )}

      {content.active_conditions?.length > 0 && (
        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">Active Conditions</h3>
          <div className="flex flex-wrap gap-1.5">
            {content.active_conditions.map((c: any, i: number) => (
              <span key={i} className="rounded border border-gray-200 bg-white px-2 py-0.5 text-xs text-gray-700">
                {c.condition}
                {c.icd10 && <span className="ml-1 text-gray-400">({c.icd10})</span>}
              </span>
            ))}
          </div>
        </section>
      )}

      {content.care_gaps?.length > 0 && (
        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">Care Gaps</h3>
          <div className="flex flex-col gap-1.5">
            {content.care_gaps.map((gap: any, i: number) => (
              <div key={i} className="flex items-start gap-2 rounded border px-2.5 py-2 text-xs"
                style={{ borderColor: gap.priority === "HIGH" ? "#fed7aa" : "#e5e7eb" }}>
                <Badge variant={severityVariant(gap.priority)} className="shrink-0 mt-0.5">{gap.priority}</Badge>
                <div>
                  <p className="font-medium text-gray-800">{gap.gap}</p>
                  {gap.recommendation && <p className="mt-0.5 text-gray-500">{gap.recommendation}</p>}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {content.risk_flags?.length > 0 && (
        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">Risk Flags</h3>
          <div className="flex flex-col gap-1.5">
            {content.risk_flags.map((flag: any, i: number) => (
              <div key={i} className="flex items-start gap-2 rounded border border-red-100 bg-red-50 px-2.5 py-2 text-xs">
                <Badge variant={severityVariant(flag.severity)} className="shrink-0">{flag.severity}</Badge>
                <div>
                  <p className="font-medium text-gray-800">{flag.flag}</p>
                  {flag.rationale && <p className="mt-0.5 text-gray-500">{flag.rationale}</p>}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {data.reasoning_summary && (
        <button
          onClick={() => setShowReasoning(!showReasoning)}
          className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600"
        >
          <ChevronDown className={`h-3 w-3 transition-transform ${showReasoning ? "rotate-180" : ""}`} />
          {showReasoning ? "Hide" : "Show"} AI reasoning
        </button>
      )}
      {showReasoning && (
        <p className="rounded border border-gray-100 bg-gray-50 px-3 py-2 text-xs text-gray-500 leading-relaxed">
          {data.reasoning_summary}
        </p>
      )}
    </div>
  );
}

function PanelSkeleton({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-2 text-sm text-gray-400">
      <Loader2 className="h-4 w-4 animate-spin" />
      Loading {label}...
    </div>
  );
}

function PanelError({ label, onRetry }: { label: string; onRetry: () => void }) {
  return (
    <div className="flex items-center justify-between text-xs text-red-500">
      <span>Failed to load {label}</span>
      <button onClick={onRetry} className="text-brand-600 underline">Retry</button>
    </div>
  );
}
