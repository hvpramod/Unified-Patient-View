"use client";

import { useState } from "react";
import { CheckCircle2, XCircle, MessageSquare, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ActionButtonsProps {
  onAccept: (annotation?: string) => Promise<void>;
  onReject: (annotation?: string) => Promise<void>;
  disabled?: boolean;
  accepted?: boolean;
  rejected?: boolean;
}

export function ActionButtons({ onAccept, onReject, disabled, accepted, rejected }: ActionButtonsProps) {
  const [loading, setLoading] = useState<"accept" | "reject" | null>(null);
  const [showAnnotation, setShowAnnotation] = useState(false);
  const [annotation, setAnnotation] = useState("");
  const [pendingAction, setPendingAction] = useState<"accept" | "reject" | null>(null);

  const handleAction = async (action: "accept" | "reject") => {
    setLoading(action);
    try {
      if (action === "accept") await onAccept(annotation || undefined);
      else await onReject(annotation || undefined);
      setShowAnnotation(false);
      setAnnotation("");
    } finally {
      setLoading(null);
      setPendingAction(null);
    }
  };

  if (accepted) return <span className="text-xs font-medium text-green-600 flex items-center gap-1"><CheckCircle2 className="h-3.5 w-3.5" /> Accepted</span>;
  if (rejected) return <span className="text-xs font-medium text-red-500 flex items-center gap-1"><XCircle className="h-3.5 w-3.5" /> Rejected</span>;

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <button
          onClick={() => { setPendingAction("accept"); setShowAnnotation(true); }}
          disabled={disabled || !!loading}
          className="flex items-center gap-1 rounded px-2.5 py-1 text-xs font-medium bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 transition-colors"
        >
          {loading === "accept" ? <Loader2 className="h-3 w-3 animate-spin" /> : <CheckCircle2 className="h-3 w-3" />}
          Accept
        </button>
        <button
          onClick={() => { setPendingAction("reject"); setShowAnnotation(true); }}
          disabled={disabled || !!loading}
          className="flex items-center gap-1 rounded px-2.5 py-1 text-xs font-medium border border-red-300 text-red-600 hover:bg-red-50 disabled:opacity-50 transition-colors"
        >
          {loading === "reject" ? <Loader2 className="h-3 w-3 animate-spin" /> : <XCircle className="h-3 w-3" />}
          Reject
        </button>
        <button
          onClick={() => setShowAnnotation(!showAnnotation)}
          className="flex items-center gap-1 rounded px-2.5 py-1 text-xs text-gray-500 hover:bg-gray-100 transition-colors"
        >
          <MessageSquare className="h-3 w-3" />
          Note
        </button>
      </div>
      {showAnnotation && (
        <div className="flex gap-2">
          <input
            type="text"
            value={annotation}
            onChange={(e) => setAnnotation(e.target.value)}
            placeholder="Add clinical note (optional)..."
            className="flex-1 rounded border border-gray-300 px-2 py-1 text-xs focus:border-brand-500 focus:outline-none"
          />
          <button
            onClick={() => pendingAction && handleAction(pendingAction)}
            className="rounded px-2 py-1 text-xs bg-brand-600 text-white hover:bg-brand-700"
          >
            Confirm
          </button>
        </div>
      )}
    </div>
  );
}
