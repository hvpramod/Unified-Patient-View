"use client";

import { Loader2, RefreshCw, TrendingUp, TrendingDown, Minus, AlertTriangle } from "lucide-react";
import { useLabIntelligenceSummary } from "@/lib/api/hooks";
import { ConfidenceScore } from "@/components/shared/confidence-score";
import { FDADisclaimer } from "@/components/shared/fda-disclaimer";
import { SourceBadge } from "@/components/shared/source-badge";
import { formatDate } from "@/lib/utils";

export function LabIntelligencePanel({ patientId }: { patientId: string }) {
  const { data, isLoading, error, refetch } = useLabIntelligenceSummary(patientId);

  if (isLoading) return <div className="flex items-center gap-2 text-sm text-gray-400"><Loader2 className="h-4 w-4 animate-spin" />Loading lab intelligence...</div>;
  if (error) return <div className="text-xs text-red-500">Failed to load labs. <button onClick={() => refetch()} className="underline">Retry</button></div>;
  if (!data) return null;

  const content = data.content || {};

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-sm font-semibold text-gray-800">Lab Intelligence</h2>
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

      {data.has_critical_values && (
        <div className="flex items-center gap-2 rounded border border-red-200 bg-red-50 px-3 py-2 text-xs font-medium text-red-700">
          <AlertTriangle className="h-4 w-4" />
          Critical lab values detected — immediate review required
        </div>
      )}

      {content.critical_values?.length > 0 && (
        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">Critical Values</h3>
          <div className="flex flex-col gap-2">
            {content.critical_values.map((lab: any, i: number) => (
              <div key={i} className="rounded border border-red-200 bg-red-50 px-3 py-2.5">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs font-semibold text-gray-800">{lab.test_name}</p>
                    <p className="text-sm font-bold text-red-700 mt-0.5">
                      {lab.value} {lab.unit}
                      {lab.reference_range && <span className="text-xs font-normal text-gray-500 ml-2">(ref: {lab.reference_range})</span>}
                    </p>
                    {lab.clinical_significance && (
                      <p className="text-xs text-gray-600 mt-1">{lab.clinical_significance}</p>
                    )}
                    {lab.recommended_action && (
                      <p className="text-xs font-medium text-red-700 mt-1">→ {lab.recommended_action}</p>
                    )}
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    {lab.source && <SourceBadge source={lab.source} />}
                    {lab.collected_at && <span className="text-xs text-gray-400">{formatDate(lab.collected_at)}</span>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {content.trends?.length > 0 && (
        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">Trends</h3>
          <div className="flex flex-col gap-2">
            {content.trends.map((trend: any, i: number) => {
              const TrendIcon = trend.trend_direction === "INCREASING" ? TrendingUp
                : trend.trend_direction === "DECREASING" ? TrendingDown : Minus;
              const trendColor = trend.trend_direction === "INCREASING" ? "text-red-500" : trend.trend_direction === "DECREASING" ? "text-green-600" : "text-gray-500";
              return (
                <div key={i} className="flex items-start gap-3 rounded border border-gray-100 bg-white px-3 py-2.5">
                  <TrendIcon className={`h-4 w-4 shrink-0 mt-0.5 ${trendColor}`} />
                  <div className="flex-1">
                    <p className="text-xs font-medium text-gray-800">{trend.test_name}</p>
                    <div className="flex gap-2 mt-1">
                      {trend.values?.slice(-3).map((v: any, j: number) => (
                        <span key={j} className="text-xs text-gray-500">{v.value} <span className="text-gray-300">({formatDate(v.date)})</span></span>
                      ))}
                    </div>
                    {trend.clinical_implication && (
                      <p className="text-xs text-gray-500 mt-0.5">{trend.clinical_implication}</p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {content.summary_narrative && (
        <div className="rounded border border-gray-100 bg-gray-50 px-3 py-2.5 text-xs text-gray-700 leading-relaxed">
          {content.summary_narrative}
        </div>
      )}
    </div>
  );
}
