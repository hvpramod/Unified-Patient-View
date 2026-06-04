"use client";

import { Loader2, RefreshCw, MessageCircle, AlertTriangle, ArrowRight } from "lucide-react";
import { useVisitPrepSummary } from "@/lib/api/hooks";
import { ConfidenceScore } from "@/components/shared/confidence-score";
import { FDADisclaimer } from "@/components/shared/fda-disclaimer";
import { Badge } from "@/components/ui/badge";
import { severityVariant, formatDate } from "@/lib/utils";

export function VisitPrepPanel({ patientId, apptId }: { patientId: string; apptId?: string }) {
  const { data, isLoading, error, refetch } = useVisitPrepSummary(patientId, apptId);

  if (isLoading) return <div className="flex items-center gap-2 text-sm text-gray-400"><Loader2 className="h-4 w-4 animate-spin" />Loading visit prep...</div>;
  if (error) return <div className="text-xs text-red-500">No visit prep available. <button onClick={() => refetch()} className="underline">Retry</button></div>;
  if (!data) return null;

  const content = data.content || {};

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-sm font-semibold text-gray-800">Visit Preparation</h2>
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

      {content.visit_brief && (
        <div className="rounded-lg border border-brand-100 bg-brand-50 px-3 py-2.5">
          <p className="text-xs text-gray-700 leading-relaxed">{content.visit_brief}</p>
        </div>
      )}

      {content.risk_alerts?.length > 0 && (
        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">Risk Alerts</h3>
          {content.risk_alerts.map((alert: any, i: number) => (
            <div key={i} className="mb-1.5 flex items-start gap-2 rounded border px-2.5 py-2 text-xs border-orange-200 bg-orange-50">
              <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5 text-orange-600" />
              <div>
                <Badge variant={severityVariant(alert.severity)} className="mb-1">{alert.severity}</Badge>
                <p className="font-medium text-gray-800">{alert.alert}</p>
                {alert.recommended_action && <p className="text-gray-500 mt-0.5">→ {alert.recommended_action}</p>}
              </div>
            </div>
          ))}
        </section>
      )}

      {content.suggested_questions?.length > 0 && (
        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500 flex items-center gap-1">
            <MessageCircle className="h-3.5 w-3.5" />
            Suggested Questions
          </h3>
          <ol className="flex flex-col gap-1.5">
            {content.suggested_questions.map((q: any, i: number) => (
              <li key={i} className="flex items-start gap-2 text-xs">
                <span className="shrink-0 font-semibold text-brand-600">{i + 1}.</span>
                <div>
                  <p className="text-gray-800">{q.question}</p>
                  {q.rationale && <p className="text-gray-400 mt-0.5">{q.rationale}</p>}
                </div>
              </li>
            ))}
          </ol>
        </section>
      )}

      {content.follow_up_recommendations?.length > 0 && (
        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">Follow-up</h3>
          <div className="flex flex-col gap-1.5">
            {content.follow_up_recommendations.map((rec: any, i: number) => (
              <div key={i} className="flex items-start gap-2 text-xs">
                <ArrowRight className="h-3.5 w-3.5 shrink-0 mt-0.5 text-brand-500" />
                <div>
                  <p className="text-gray-800">{rec.recommendation}</p>
                  {rec.timeframe && <p className="text-gray-400">{rec.timeframe}</p>}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
