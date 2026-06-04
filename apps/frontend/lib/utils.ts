import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function severityVariant(severity: string): "critical" | "high" | "medium" | "low" | "secondary" {
  const map: Record<string, "critical" | "high" | "medium" | "low"> = {
    CRITICAL: "critical",
    HIGH: "high",
    MEDIUM: "medium",
    LOW: "low",
  };
  return map[severity?.toUpperCase()] ?? "secondary";
}

export function sourceVariant(source: string): "athena" | "healthgorilla" | "pathway" | "secondary" {
  const map: Record<string, "athena" | "healthgorilla" | "pathway"> = {
    athena: "athena",
    healthgorilla: "healthgorilla",
    pathway: "pathway",
  };
  return map[source?.toLowerCase()] ?? "secondary";
}

export function confidenceColor(score: number): string {
  if (score >= 0.85) return "bg-green-500";
  if (score >= 0.65) return "bg-amber-500";
  return "bg-red-400";
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "—";
  try {
    return new Date(dateStr).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
  } catch {
    return dateStr;
  }
}
