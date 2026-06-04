import { Badge } from "@/components/ui/badge";
import { sourceVariant } from "@/lib/utils";

const SOURCE_LABELS: Record<string, string> = {
  athena: "Athena",
  healthgorilla: "Health Gorilla",
  pathway: "Pathway",
  hospital: "Hospital",
  manual: "Manual",
};

export function SourceBadge({ source }: { source: string }) {
  return (
    <Badge variant={sourceVariant(source)}>
      {SOURCE_LABELS[source?.toLowerCase()] ?? source}
    </Badge>
  );
}
