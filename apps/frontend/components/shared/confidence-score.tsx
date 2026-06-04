import { cn, confidenceColor } from "@/lib/utils";

interface ConfidenceScoreProps {
  score: number;
  showLabel?: boolean;
  className?: string;
}

export function ConfidenceScore({ score, showLabel = true, className }: ConfidenceScoreProps) {
  const pct = Math.round(score * 100);
  return (
    <div className={cn("flex items-center gap-2", className)}>
      {showLabel && <span className="text-xs text-gray-500">Confidence</span>}
      <div className="confidence-bar w-20">
        <div
          className={cn("confidence-fill", confidenceColor(score))}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-medium text-gray-700">{pct}%</span>
    </div>
  );
}
