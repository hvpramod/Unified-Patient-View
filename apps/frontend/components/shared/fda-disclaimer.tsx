import { AlertTriangle } from "lucide-react";

export function FDADisclaimer() {
  return (
    <div className="flex items-center gap-1.5 rounded border border-amber-200 bg-amber-50 px-3 py-1.5 text-xs text-amber-700">
      <AlertTriangle className="h-3 w-3 shrink-0" />
      <span>Clinical Decision Support — For Clinician Review Only</span>
    </div>
  );
}
