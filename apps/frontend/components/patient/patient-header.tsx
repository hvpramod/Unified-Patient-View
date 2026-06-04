"use client";

import { User, Calendar, Hash, AlertCircle } from "lucide-react";
import { formatDate } from "@/lib/utils";
import { useConflicts } from "@/lib/api/hooks";
import { Badge } from "@/components/ui/badge";

interface PatientHeaderProps {
  patient: {
    id: string;
    first_name: string;
    last_name: string;
    date_of_birth?: string;
    gender?: string;
    mrn?: string;
  };
}

export function PatientHeader({ patient }: PatientHeaderProps) {
  const { data: conflictsData } = useConflicts(patient.id);
  const openConflicts = conflictsData?.open_count ?? 0;

  return (
    <div className="flex items-start justify-between border-b border-gray-200 bg-white px-4 py-3">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-brand-100 text-brand-700">
          <User className="h-5 w-5" />
        </div>
        <div>
          <h1 className="text-base font-semibold text-gray-900">
            {patient.first_name} {patient.last_name}
          </h1>
          <div className="flex items-center gap-3 text-xs text-gray-500">
            {patient.date_of_birth && (
              <span className="flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                {formatDate(patient.date_of_birth)}
              </span>
            )}
            {patient.gender && <span>{patient.gender}</span>}
            {patient.mrn && (
              <span className="flex items-center gap-1">
                <Hash className="h-3 w-3" />
                MRN: {patient.mrn}
              </span>
            )}
          </div>
        </div>
      </div>
      {openConflicts > 0 && (
        <div className="flex items-center gap-1.5 rounded-full bg-orange-100 px-3 py-1 text-xs font-medium text-orange-700">
          <AlertCircle className="h-3.5 w-3.5" />
          {openConflicts} open conflict{openConflicts !== 1 ? "s" : ""}
        </div>
      )}
    </div>
  );
}
