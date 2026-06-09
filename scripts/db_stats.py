"""
Show a quick summary of what's in the UPV database.

Usage:
    python scripts/db_stats.py
    python scripts/db_stats.py --patients     # list all patients
    python scripts/db_stats.py --patient <id> # inspect one patient
"""
import argparse, os, sys
import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://upv:upv@localhost:5432/upv")


def connect():
    return psycopg2.connect(DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"))


def show_stats(cur):
    tables = ["patients", "fhir_resources", "conflicts", "ai_summaries", "apc_actions", "audit_log"]
    print("\n=== UPV Database Stats ===\n")
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        n = cur.fetchone()[0]
        print(f"  {t:<30} {n:>6} rows")

    print("\n=== Conflicts by Severity ===\n")
    cur.execute("SELECT severity, COUNT(*) FROM conflicts GROUP BY severity ORDER BY severity")
    for row in cur.fetchall():
        print(f"  {row[0]:<12} {row[1]:>6}")

    print("\n=== Conflicts by Type ===\n")
    cur.execute("SELECT conflict_type, COUNT(*) FROM conflicts GROUP BY conflict_type ORDER BY conflict_type")
    for row in cur.fetchall():
        print(f"  {row[0]:<30} {row[1]:>6}")

    print("\n=== FHIR Resources by Type ===\n")
    cur.execute("SELECT resource_type, source_system, COUNT(*) FROM fhir_resources GROUP BY resource_type, source_system ORDER BY resource_type, source_system")
    for row in cur.fetchall():
        print(f"  {row[0]:<30} {row[1]:<20} {row[2]:>6}")

    print("\n=== AI Summaries by Type ===\n")
    cur.execute("SELECT summary_type, COUNT(*), AVG(confidence_score)::numeric(4,2) FROM ai_summaries WHERE is_current GROUP BY summary_type")
    for row in cur.fetchall():
        print(f"  {row[0]:<35} {row[1]:>4} summaries  avg confidence: {row[2]}")
    print()


def list_patients(cur):
    cur.execute("""
        SELECT p.id, p.first_name, p.last_name, p.date_of_birth, p.gender, p.mrn,
               COUNT(DISTINCT f.id) AS resources,
               COUNT(DISTINCT c.id) FILTER (WHERE c.resolved_at IS NULL AND NOT c.auto_resolved) AS open_conflicts
        FROM patients p
        LEFT JOIN fhir_resources f ON f.patient_id = p.id
        LEFT JOIN conflicts c ON c.patient_id = p.id
        GROUP BY p.id
        ORDER BY p.last_name, p.first_name
    """)
    rows = cur.fetchall()
    print(f"\n=== Patients ({len(rows)}) ===\n")
    print(f"  {'Name':<25} {'DOB':<12} {'Gender':<8} {'MRN':<14} {'Resources':>9} {'Conflicts':>9}")
    print("  " + "-" * 80)
    for r in rows:
        name = f"{r[1]} {r[2]}"
        print(f"  {name:<25} {str(r[3]):<12} {r[4]:<8} {r[5]:<14} {r[6]:>9} {r[7]:>9}")
    print()


def inspect_patient(cur, patient_id: str):
    # Support partial ID match
    if len(patient_id) < 36:
        cur.execute("SELECT id FROM patients WHERE id::text LIKE %s", (f"{patient_id}%",))
        row = cur.fetchone()
        if not row:
            print(f"Patient not found: {patient_id}")
            return
        patient_id = str(row[0])

    cur.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
    p = cur.fetchone()
    if not p:
        print("Patient not found")
        return

    print(f"\n=== Patient: {p[2]} {p[3]} ===")
    print(f"  ID     : {p[0]}")
    print(f"  DOB    : {p[4]}  Gender: {p[5]}  MRN: {p[6]}")

    cur.execute("SELECT resource_type, source_system, COUNT(*) FROM fhir_resources WHERE patient_id = %s GROUP BY resource_type, source_system ORDER BY resource_type", (patient_id,))
    print("\n  FHIR Resources:")
    for r in cur.fetchall():
        print(f"    {r[0]:<30} {r[1]:<20} {r[2]}")

    cur.execute("SELECT conflict_type, severity, description FROM conflicts WHERE patient_id = %s ORDER BY severity", (patient_id,))
    conflicts = cur.fetchall()
    print(f"\n  Conflicts ({len(conflicts)}):")
    for c in conflicts:
        print(f"    [{c[1]:<8}] {c[0]:<25} {c[2][:70]}...")

    cur.execute("SELECT summary_type, model_used, confidence_score, generated_at FROM ai_summaries WHERE patient_id = %s AND is_current ORDER BY summary_type", (patient_id,))
    print("\n  AI Summaries:")
    for s in cur.fetchall():
        print(f"    {s[0]:<35} {s[1]:<25} conf: {s[2]}  {str(s[3])[:19]}")
    print()


def main():
    parser = argparse.ArgumentParser(description="UPV database inspector")
    parser.add_argument("--patients",  action="store_true", help="List all patients")
    parser.add_argument("--patient",   type=str, help="Inspect a specific patient (full or partial UUID)")
    args = parser.parse_args()

    conn = connect()
    cur = conn.cursor()

    if args.patient:
        inspect_patient(cur, args.patient)
    elif args.patients:
        list_patients(cur)
    else:
        show_stats(cur)
        list_patients(cur)

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
