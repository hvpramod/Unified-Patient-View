"use client";

import { useState } from "react";
import {
  User, Calendar, Hash, AlertCircle, RefreshCw, Pill, TrendingUp,
  TrendingDown, AlertTriangle, MessageCircle, ArrowRight, CheckCircle2,
  XCircle, MessageSquare, ChevronDown, Loader2, Activity, ClipboardList,
  FlaskConical, Stethoscope
} from "lucide-react";

// ── Synthetic patient data ────────────────────────────────────────────────
const PATIENT = {
  id: "demo-patient-001",
  first_name: "Margaret",
  last_name: "Thompson",
  date_of_birth: "1958-04-12",
  gender: "Female",
  mrn: "MRN-294817",
};

const CLINICAL_SUMMARY = {
  patient_overview:
    "Margaret Thompson is a 66-year-old female with a complex medical history including Type 2 Diabetes Mellitus (HbA1c 8.2%), Hypertension, and Chronic Kidney Disease Stage 3. She was recently discharged from Regional Medical Center following a 3-day inpatient stay for hypertensive urgency. Her current medication regimen shows a critical conflict between Athena and the hospital discharge summary regarding Lisinopril.",
  active_conditions: [
    { condition: "Type 2 Diabetes Mellitus", icd10: "E11.9", status: "active", source: "Athena" },
    { condition: "Hypertension", icd10: "I10", status: "active", source: "Athena" },
    { condition: "Chronic Kidney Disease Stage 3", icd10: "N18.3", status: "active", source: "Health Gorilla" },
    { condition: "Hyperlipidemia", icd10: "E78.5", status: "active", source: "Athena" },
  ],
  care_gaps: [
    { gap: "HbA1c above target (8.2% — goal <7.5%)", priority: "HIGH", recommendation: "Consider adjusting Metformin dose or adding GLP-1 agonist. Referral to Endocrinology pending." },
    { gap: "Annual diabetic eye exam overdue (last: 18 months ago)", priority: "MEDIUM", recommendation: "Schedule ophthalmology referral" },
    { gap: "Nephrology follow-up not completed", priority: "HIGH", recommendation: "CKD Stage 3 requires nephrology consultation within 3 months" },
  ],
  risk_flags: [
    { flag: "Medication conflict: Lisinopril active in Athena, discontinued in hospital discharge", severity: "CRITICAL", rationale: "Active in Athena as of 2024-01-10. Hospital discharge 2024-01-23 lists Lisinopril as Discontinued due to renal function decline." },
    { flag: "HbA1c trending upward (+0.8% over 6 months)", severity: "HIGH", rationale: "Feb 2024: 7.4%, Aug 2024: 8.2% — pattern suggests inadequate glycemic control" },
  ],
  confidence_score: 0.91,
  generated_at: "2024-09-05T08:14:22Z",
  model_used: "openai/gpt-4o",
  reasoning_summary:
    "Summary generated from 3 source systems (Athena, Health Gorilla, Pathway). Two active conflicts detected by rule engine. RAG retrieved 4 relevant clinical guideline chunks including ADA Standards of Diabetes Care 2024 and KDIGO CKD guidelines. Confidence reflects high data completeness from Athena (primary) with corroborating observations from Health Gorilla.",
};

const CONFLICTS = [
  {
    id: "conf-001",
    conflict_type: "STATUS_MISMATCH",
    resource_type: "MedicationRequest",
    severity: "CRITICAL",
    description: "Lisinopril 10mg: Listed as ACTIVE in Athena (last updated 2024-01-10) but DISCONTINUED in Pathway hospital discharge summary (2024-01-23). Patient may not be taking a critical antihypertensive.",
    sources: ["athena", "pathway"],
    confidence_score: 0.97,
    detected_at: "2024-09-05T08:12:01Z",
    resolved_at: null,
    auto_resolved: false,
  },
  {
    id: "conf-002",
    conflict_type: "LAB_DISCREPANCY",
    resource_type: "Observation",
    severity: "MEDIUM",
    description: "HbA1c result discrepancy within 3-day window: Athena reports 7.4% (Feb 14), Health Gorilla reports 8.2% (Feb 15). 10.8% difference exceeds 15% threshold. Lab source calibration may differ.",
    sources: ["athena", "healthgorilla"],
    confidence_score: 0.84,
    detected_at: "2024-09-05T08:12:03Z",
    resolved_at: null,
    auto_resolved: false,
  },
  {
    id: "conf-003",
    conflict_type: "MEDICATION_DUPLICATE",
    resource_type: "MedicationRequest",
    severity: "MEDIUM",
    description: "Metformin 500mg active in both Athena and Health Gorilla as separate active prescriptions. Possible duplicate entry.",
    sources: ["athena", "healthgorilla"],
    confidence_score: 0.89,
    detected_at: "2024-09-05T08:12:04Z",
    resolved_at: null,
    auto_resolved: false,
  },
];

const MED_RECON = {
  reconciled_medications: [
    {
      drug_name: "Lisinopril 10mg",
      recommended_status: "discontinued",
      recommended_dose: "Discontinue — per hospital discharge 2024-01-23",
      rationale: "Hospital discharge documentation explicitly discontinues Lisinopril due to eGFR decline (eGFR 38). CKD Stage 3 with declining function warrants ACE inhibitor reassessment. Recommend clinical review before reinstatement.",
      sources_used: ["athena", "pathway"],
      confidence_score: 0.94,
      requires_clinician_review: true,
    },
    {
      drug_name: "Metformin 500mg",
      recommended_status: "active",
      recommended_dose: "500mg twice daily (reduce if eGFR <30)",
      rationale: "Consistent across Athena and Health Gorilla. Safe at current eGFR 38. Monitor quarterly. Dose reduction required if eGFR drops below 30.",
      sources_used: ["athena", "healthgorilla"],
      confidence_score: 0.96,
      requires_clinician_review: false,
    },
    {
      drug_name: "Amlodipine 5mg",
      recommended_status: "active",
      recommended_dose: "5mg daily",
      rationale: "Consistent status across sources. Calcium channel blocker appropriate for hypertension in CKD. No conflicts detected.",
      sources_used: ["athena"],
      confidence_score: 0.98,
      requires_clinician_review: false,
    },
    {
      drug_name: "Atorvastatin 40mg",
      recommended_status: "active",
      recommended_dose: "40mg at bedtime",
      rationale: "Consistent. Statin therapy appropriate for cardiovascular risk reduction in T2DM. No conflicts.",
      sources_used: ["athena", "healthgorilla"],
      confidence_score: 0.97,
      requires_clinician_review: false,
    },
  ],
  confidence_score: 0.93,
  generated_at: "2024-09-05T08:14:25Z",
  model_used: "claude/claude-sonnet-4-6",
};

const LAB_INTEL = {
  has_critical_values: true,
  critical_values: [
    {
      test_name: "eGFR (CKD-EPI)",
      value: "38",
      unit: "mL/min/1.73m²",
      reference_range: ">60",
      interpretation: "L",
      clinical_significance: "CKD Stage 3b. Significant renal impairment. Requires nephrology referral and medication dose adjustments. Monitor potassium closely.",
      recommended_action: "Urgent nephrology referral. Review all renally-dosed medications.",
      source: "athena",
      collected_at: "2024-09-01",
    },
  ],
  trends: [
    {
      test_name: "HbA1c",
      trend_direction: "INCREASING",
      values: [
        { value: 7.1, date: "2024-03-01", source: "athena" },
        { value: 7.4, date: "2024-06-01", source: "athena" },
        { value: 8.2, date: "2024-09-01", source: "healthgorilla" },
      ],
      clinical_implication: "Upward trend (+1.1% over 6 months) suggests worsening glycemic control. ADA 2024 guidelines recommend medication intensification at HbA1c >8.0%.",
    },
    {
      test_name: "eGFR",
      trend_direction: "DECREASING",
      values: [
        { value: 52, date: "2024-01-01", source: "athena" },
        { value: 44, date: "2024-05-01", source: "athena" },
        { value: 38, date: "2024-09-01", source: "athena" },
      ],
      clinical_implication: "Declining renal function (-14 mL/min over 8 months). At current rate, Stage 4 CKD within 12–18 months. Nephrology urgent.",
    },
    {
      test_name: "Potassium",
      trend_direction: "STABLE",
      values: [
        { value: 4.2, date: "2024-06-01", source: "athena" },
        { value: 4.4, date: "2024-09-01", source: "athena" },
      ],
      clinical_implication: "Within normal limits. Monitor quarterly given CKD and ACE inhibitor use.",
    },
  ],
  summary_narrative:
    "Critical: eGFR 38 (Stage 3b CKD) with declining trend. HbA1c 8.2% trending upward — glycemic target not met. Potassium stable. No acute electrolyte abnormalities. Primary concern is accelerating renal function decline concurrent with suboptimal diabetes control.",
  confidence_score: 0.92,
  generated_at: "2024-09-05T08:14:28Z",
  model_used: "openai/gpt-4o",
};

const VISIT_PREP = {
  visit_brief:
    "Ms. Thompson presents for a scheduled follow-up 6 weeks post-discharge from Regional Medical Center (Jan 20–23 admission for hypertensive urgency). Critical agenda items include: (1) Resolving the Lisinopril medication conflict — the drug appears active in Athena but was discontinued at discharge; (2) Addressing accelerating eGFR decline now at 38; (3) Reviewing worsening glycemic control (HbA1c 8.2%). Patient has a pending Endocrinology referral.",
  risk_alerts: [
    { alert: "Unresolved Lisinopril conflict — patient may be incorrectly taking or omitting a critical antihypertensive", severity: "CRITICAL", recommended_action: "Confirm current medication use. Reconcile Athena record with discharge summary." },
    { alert: "eGFR decline trajectory — approaching CKD Stage 4", severity: "HIGH", recommended_action: "Initiate nephrology referral if not yet completed. Review Metformin continuation." },
  ],
  suggested_questions: [
    { question: "Are you currently taking Lisinopril? When did you last take it?", rationale: "Resolves the medication conflict — determines actual patient behaviour", related_condition: "Hypertension / CKD" },
    { question: "How are your blood sugars running at home? Any readings above 250?", rationale: "Contextualises HbA1c 8.2% — identifies post-prandial vs fasting pattern", related_condition: "Type 2 Diabetes" },
    { question: "Have you noticed any changes in your urine output or ankle swelling since discharge?", rationale: "Screens for fluid retention / acute decompensation related to eGFR decline", related_condition: "CKD Stage 3b" },
    { question: "Have you followed up with the Endocrinology referral from your last visit?", rationale: "Tracks care coordination for uncontrolled diabetes", related_condition: "Type 2 Diabetes" },
  ],
  follow_up_recommendations: [
    { recommendation: "Order repeat BMP in 4 weeks to monitor eGFR and potassium trend", timeframe: "4 weeks" },
    { recommendation: "Expedite Nephrology referral — eGFR 38 with declining trend", timeframe: "Within 2 weeks" },
    { recommendation: "Intensify diabetes management: consider adding GLP-1 agonist (also renoprotective)", timeframe: "This visit" },
    { recommendation: "Update Athena medication record to reflect hospital discharge changes", timeframe: "Today" },
  ],
  confidence_score: 0.89,
  generated_at: "2024-09-05T08:14:30Z",
  model_used: "openai/gpt-4o",
};

// ── Small reusable components ──────────────────────────────────────────────

function Badge({ children, variant = "default" }: { children: React.ReactNode; variant?: string }) {
  const styles: Record<string, string> = {
    default: "bg-blue-600 text-white border-transparent",
    critical: "bg-red-50 text-red-700 border-red-200",
    high: "bg-orange-50 text-orange-700 border-orange-200",
    medium: "bg-amber-50 text-amber-700 border-amber-200",
    low: "bg-green-50 text-green-700 border-green-200",
    athena: "bg-blue-50 text-blue-700 border-blue-200",
    healthgorilla: "bg-purple-50 text-purple-700 border-purple-200",
    pathway: "bg-teal-50 text-teal-700 border-teal-200",
    secondary: "bg-gray-100 text-gray-700 border-gray-200",
  };
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-semibold ${styles[variant] ?? styles.secondary}`}>
      {children}
    </span>
  );
}

function SourceBadge({ source }: { source: string }) {
  const labels: Record<string, string> = { athena: "Athena", healthgorilla: "Health Gorilla", pathway: "Pathway" };
  return <Badge variant={source}>{labels[source] ?? source}</Badge>;
}

function ConfidenceBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color = pct >= 85 ? "bg-green-500" : pct >= 65 ? "bg-amber-500" : "bg-red-400";
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-xs text-gray-400">Confidence</span>
      <div className="h-1.5 w-16 rounded-full bg-gray-200">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-medium text-gray-600">{pct}%</span>
    </div>
  );
}

function FDABanner() {
  return (
    <div className="flex items-center gap-1.5 rounded border border-amber-200 bg-amber-50 px-3 py-1.5 text-xs text-amber-700">
      <AlertTriangle className="h-3 w-3 shrink-0" />
      Clinical Decision Support — For Clinician Review Only
    </div>
  );
}

function SeverityBadge({ sev }: { sev: string }) {
  const v: Record<string, string> = { CRITICAL: "critical", HIGH: "high", MEDIUM: "medium", LOW: "low" };
  return <Badge variant={v[sev] ?? "secondary"}>{sev}</Badge>;
}

// ── Action buttons with accept/reject/annotate ─────────────────────────────
function ActionButtons({ id, onAccept, onReject }: { id: string; onAccept: (id: string) => void; onReject: (id: string) => void }) {
  const [done, setDone] = useState<"accept" | "reject" | null>(null);
  const [note, setNote] = useState("");
  const [showNote, setShowNote] = useState(false);

  if (done === "accept") return <span className="flex items-center gap-1 text-xs font-medium text-green-600"><CheckCircle2 className="h-3.5 w-3.5" /> Accepted</span>;
  if (done === "reject") return <span className="flex items-center gap-1 text-xs font-medium text-red-500"><XCircle className="h-3.5 w-3.5" /> Rejected</span>;

  return (
    <div className="flex flex-col gap-1.5 mt-2">
      <div className="flex items-center gap-2">
        <button onClick={() => { setDone("accept"); onAccept(id); }} className="flex items-center gap-1 rounded px-2.5 py-1 text-xs font-medium bg-green-600 text-white hover:bg-green-700 transition-colors">
          <CheckCircle2 className="h-3 w-3" /> Accept
        </button>
        <button onClick={() => { setDone("reject"); onReject(id); }} className="flex items-center gap-1 rounded px-2.5 py-1 text-xs font-medium border border-red-300 text-red-600 hover:bg-red-50 transition-colors">
          <XCircle className="h-3 w-3" /> Reject
        </button>
        <button onClick={() => setShowNote(!showNote)} className="flex items-center gap-1 rounded px-2 py-1 text-xs text-gray-400 hover:bg-gray-100">
          <MessageSquare className="h-3 w-3" /> Note
        </button>
      </div>
      {showNote && (
        <input type="text" value={note} onChange={e => setNote(e.target.value)} placeholder="Add clinical note..." className="w-full rounded border border-gray-200 px-2 py-1 text-xs focus:border-blue-400 focus:outline-none" />
      )}
    </div>
  );
}

// ── Panel: Clinical Summary ────────────────────────────────────────────────
function ClinicalSummaryPanel() {
  const [showReasoning, setShowReasoning] = useState(false);
  const s = CLINICAL_SUMMARY;
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-sm font-semibold text-gray-800">Clinical Summary</h2>
          <p className="mt-0.5 text-xs text-gray-400">Sep 5, 2024 · {s.model_used}</p>
        </div>
        <ConfidenceBar score={s.confidence_score} />
      </div>
      <FDABanner />
      <div className="rounded-lg border border-gray-100 bg-gray-50 px-3 py-2.5 text-xs text-gray-700 leading-relaxed">{s.patient_overview}</div>

      <section>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">Active Conditions</h3>
        <div className="flex flex-wrap gap-1.5">
          {s.active_conditions.map((c, i) => (
            <span key={i} className="rounded border border-gray-200 bg-white px-2 py-0.5 text-xs text-gray-700">
              {c.condition} <span className="text-gray-400">({c.icd10})</span>
            </span>
          ))}
        </div>
      </section>

      <section>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">Care Gaps</h3>
        {s.care_gaps.map((g, i) => (
          <div key={i} className="mb-1.5 flex items-start gap-2 rounded border px-2.5 py-2 text-xs" style={{ borderColor: g.priority === "HIGH" ? "#fed7aa" : "#e5e7eb", background: g.priority === "HIGH" ? "#fff7ed" : "#fff" }}>
            <SeverityBadge sev={g.priority} />
            <div><p className="font-medium text-gray-800">{g.gap}</p><p className="mt-0.5 text-gray-500">{g.recommendation}</p></div>
          </div>
        ))}
      </section>

      <section>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">Risk Flags</h3>
        {s.risk_flags.map((f, i) => (
          <div key={i} className="mb-1.5 flex items-start gap-2 rounded border border-red-100 bg-red-50 px-2.5 py-2 text-xs">
            <SeverityBadge sev={f.severity} />
            <div><p className="font-medium text-gray-800">{f.flag}</p><p className="mt-0.5 text-gray-500">{f.rationale}</p></div>
          </div>
        ))}
      </section>

      <button onClick={() => setShowReasoning(!showReasoning)} className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600">
        <ChevronDown className={`h-3 w-3 transition-transform ${showReasoning ? "rotate-180" : ""}`} />
        {showReasoning ? "Hide" : "Show"} AI reasoning
      </button>
      {showReasoning && <p className="rounded border border-gray-100 bg-gray-50 px-3 py-2 text-xs text-gray-500 leading-relaxed">{s.reasoning_summary}</p>}
    </div>
  );
}

// ── Panel: Medications ─────────────────────────────────────────────────────
function MedicationPanel() {
  const [resolved, setResolved] = useState<Record<string, "accept" | "reject">>({});
  const medConflicts = CONFLICTS.filter(c => ["STATUS_MISMATCH", "MEDICATION_DUPLICATE", "DOSE_DISCREPANCY"].includes(c.conflict_type));

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start justify-between">
        <div><h2 className="text-sm font-semibold text-gray-800">Medication Reconciliation</h2>
          <p className="mt-0.5 text-xs text-gray-400">Sep 5, 2024 · {MED_RECON.model_used}</p></div>
        <ConfidenceBar score={MED_RECON.confidence_score} />
      </div>
      <FDABanner />

      <section>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">Detected Conflicts ({medConflicts.length})</h3>
        {medConflicts.map(c => (
          <div key={c.id} className="mb-2 rounded border border-orange-100 bg-orange-50 px-3 py-2.5">
            <div className="flex items-center gap-2 mb-1"><SeverityBadge sev={c.severity} /><span className="text-xs font-medium text-gray-700">{c.conflict_type.replace(/_/g, " ")}</span></div>
            <p className="text-xs text-gray-600">{c.description}</p>
            <div className="mt-1.5 flex gap-1">{c.sources.map(s => <SourceBadge key={s} source={s} />)}</div>
            {resolved[c.id] ? (
              resolved[c.id] === "accept"
                ? <span className="mt-2 flex items-center gap-1 text-xs font-medium text-green-600"><CheckCircle2 className="h-3.5 w-3.5" /> Accepted</span>
                : <span className="mt-2 flex items-center gap-1 text-xs font-medium text-red-500"><XCircle className="h-3.5 w-3.5" /> Rejected</span>
            ) : (
              <ActionButtons id={c.id} onAccept={id => setResolved(p => ({ ...p, [id]: "accept" }))} onReject={id => setResolved(p => ({ ...p, [id]: "reject" }))} />
            )}
          </div>
        ))}
      </section>

      <section>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">Reconciliation Recommendations</h3>
        {MED_RECON.reconciled_medications.map((m, i) => (
          <div key={i} className="mb-2 rounded border border-gray-200 bg-white px-3 py-2.5">
            <div className="flex items-center gap-2 mb-1">
              <Pill className="h-3.5 w-3.5 text-blue-600" />
              <span className="text-xs font-semibold text-gray-800">{m.drug_name}</span>
              <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${m.recommended_status === "active" ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}>
                → {m.recommended_status}
              </span>
            </div>
            {m.recommended_dose && <p className="text-xs text-gray-500">Dose: {m.recommended_dose}</p>}
            <p className="text-xs text-gray-500 mt-0.5">{m.rationale}</p>
            <div className="mt-1.5 flex items-center gap-2">
              {m.sources_used.map(s => <SourceBadge key={s} source={s} />)}
              <ConfidenceBar score={m.confidence_score} />
            </div>
          </div>
        ))}
      </section>
    </div>
  );
}

// ── Panel: Labs ────────────────────────────────────────────────────────────
function LabPanel() {
  const s = LAB_INTEL;
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start justify-between">
        <div><h2 className="text-sm font-semibold text-gray-800">Lab Intelligence</h2>
          <p className="mt-0.5 text-xs text-gray-400">Sep 5, 2024 · {s.model_used}</p></div>
        <ConfidenceBar score={s.confidence_score} />
      </div>
      <FDABanner />
      {s.has_critical_values && (
        <div className="flex items-center gap-2 rounded border border-red-200 bg-red-50 px-3 py-2 text-xs font-medium text-red-700">
          <AlertTriangle className="h-4 w-4" /> Critical lab values detected — immediate review required
        </div>
      )}

      <section>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">Critical Values</h3>
        {s.critical_values.map((lab, i) => (
          <div key={i} className="mb-2 rounded border border-red-200 bg-red-50 px-3 py-2.5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-800">{lab.test_name}</p>
                <p className="mt-0.5 text-sm font-bold text-red-700">{lab.value} {lab.unit} <span className="text-xs font-normal text-gray-400">(ref: {lab.reference_range})</span></p>
                <p className="text-xs text-gray-600 mt-1">{lab.clinical_significance}</p>
                <p className="text-xs font-medium text-red-700 mt-1">→ {lab.recommended_action}</p>
              </div>
              <div className="text-right"><SourceBadge source={lab.source} /><p className="text-xs text-gray-400 mt-1">{lab.collected_at}</p></div>
            </div>
          </div>
        ))}
      </section>

      <section>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">Trends</h3>
        {s.trends.map((t, i) => {
          const Icon = t.trend_direction === "INCREASING" ? TrendingUp : t.trend_direction === "DECREASING" ? TrendingDown : Activity;
          const col = t.trend_direction === "INCREASING" ? "text-red-500" : t.trend_direction === "DECREASING" ? "text-orange-500" : "text-green-600";
          return (
            <div key={i} className="mb-2 flex items-start gap-3 rounded border border-gray-100 bg-white px-3 py-2.5">
              <Icon className={`h-4 w-4 shrink-0 mt-0.5 ${col}`} />
              <div className="flex-1">
                <p className="text-xs font-medium text-gray-800">{t.test_name}</p>
                <div className="flex gap-3 mt-1">
                  {t.values.map((v, j) => (
                    <span key={j} className="text-xs text-gray-500">{v.value} <span className="text-gray-300">({v.date.slice(0, 7)})</span></span>
                  ))}
                </div>
                <p className="text-xs text-gray-400 mt-0.5">{t.clinical_implication}</p>
              </div>
            </div>
          );
        })}
      </section>

      <div className="rounded border border-gray-100 bg-gray-50 px-3 py-2.5 text-xs text-gray-600 leading-relaxed">{s.summary_narrative}</div>
    </div>
  );
}

// ── Panel: Visit Prep ──────────────────────────────────────────────────────
function VisitPrepPanel() {
  const v = VISIT_PREP;
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start justify-between">
        <div><h2 className="text-sm font-semibold text-gray-800">Visit Preparation</h2>
          <p className="mt-0.5 text-xs text-gray-400">Sep 5, 2024 · {v.model_used}</p></div>
        <ConfidenceBar score={v.confidence_score} />
      </div>
      <FDABanner />
      <div className="rounded-lg border border-blue-100 bg-blue-50 px-3 py-2.5 text-xs text-gray-700 leading-relaxed">{v.visit_brief}</div>

      <section>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">Risk Alerts</h3>
        {v.risk_alerts.map((a, i) => (
          <div key={i} className="mb-1.5 flex items-start gap-2 rounded border border-orange-200 bg-orange-50 px-2.5 py-2 text-xs">
            <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5 text-orange-600" />
            <div><SeverityBadge sev={a.severity} /><p className="font-medium text-gray-800 mt-1">{a.alert}</p><p className="text-gray-500 mt-0.5">→ {a.recommended_action}</p></div>
          </div>
        ))}
      </section>

      <section>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400 flex items-center gap-1"><MessageCircle className="h-3.5 w-3.5" /> Suggested Questions</h3>
        <ol className="flex flex-col gap-2">
          {v.suggested_questions.map((q, i) => (
            <li key={i} className="flex items-start gap-2 text-xs">
              <span className="shrink-0 font-bold text-blue-600">{i + 1}.</span>
              <div><p className="text-gray-800">{q.question}</p><p className="text-gray-400 mt-0.5">{q.rationale}</p></div>
            </li>
          ))}
        </ol>
      </section>

      <section>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">Follow-up</h3>
        {v.follow_up_recommendations.map((r, i) => (
          <div key={i} className="mb-1 flex items-start gap-2 text-xs">
            <ArrowRight className="h-3.5 w-3.5 shrink-0 mt-0.5 text-blue-500" />
            <div><p className="text-gray-800">{r.recommendation}</p>{r.timeframe && <p className="text-gray-400">{r.timeframe}</p>}</div>
          </div>
        ))}
      </section>
    </div>
  );
}

// ── Main demo layout ───────────────────────────────────────────────────────
const TABS = [
  { id: "clinical", label: "Summary", icon: ClipboardList },
  { id: "medications", label: "Medications", icon: Pill },
  { id: "labs", label: "Labs", icon: FlaskConical },
  { id: "visit", label: "Visit Prep", icon: Stethoscope },
];

export default function DemoPage() {
  const [tab, setTab] = useState("clinical");

  return (
    <div className="flex h-screen flex-col bg-white text-sm" style={{ fontFamily: "Inter, system-ui, sans-serif" }}>
      {/* Header */}
      <div className="flex items-start justify-between border-b border-gray-200 bg-white px-4 py-3 shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 text-blue-700">
            <User className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-base font-semibold text-gray-900">{PATIENT.first_name} {PATIENT.last_name}</h1>
            <div className="flex items-center gap-3 text-xs text-gray-400">
              <span className="flex items-center gap-1"><Calendar className="h-3 w-3" /> Apr 12, 1958 (66 yrs)</span>
              <span>{PATIENT.gender}</span>
              <span className="flex items-center gap-1"><Hash className="h-3 w-3" /> {PATIENT.mrn}</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 rounded-full bg-orange-100 px-3 py-1 text-xs font-medium text-orange-700">
            <AlertCircle className="h-3.5 w-3.5" /> 3 open conflicts
          </div>
          <div className="flex items-center gap-1.5 rounded-full bg-blue-50 px-3 py-1 text-xs text-blue-600">
            <span className="h-1.5 w-1.5 rounded-full bg-green-500 inline-block" /> Live · 3 sources
          </div>
        </div>
      </div>

      {/* Tab bar */}
      <div className="flex shrink-0 border-b border-gray-200 bg-white px-4">
        {TABS.map(t => {
          const Icon = t.icon;
          return (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-1.5 border-b-2 px-4 py-2.5 text-xs font-medium transition-colors ${
                tab === t.id
                  ? "border-blue-600 text-blue-700"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {t.label}
            </button>
          );
        })}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {tab === "clinical" && <ClinicalSummaryPanel />}
        {tab === "medications" && <MedicationPanel />}
        {tab === "labs" && <LabPanel />}
        {tab === "visit" && <VisitPrepPanel />}
      </div>

      {/* Footer */}
      <div className="shrink-0 border-t border-gray-100 bg-gray-50 px-4 py-2 text-xs text-gray-400 flex items-center justify-between">
        <span>Unified Patient View · MVP 1.0</span>
        <span>Sources: Athena · Health Gorilla · Pathway &nbsp;|&nbsp; Last sync: Sep 5 2024 08:14 UTC</span>
      </div>
    </div>
  );
}
