"""Generate the top-N-sender review CSV for manual role annotation.

Per docs/methodology-briefing.md §3: the domain rule labels everyone
automatically (enron.com -> Employee, external -> Other). This script
surfaces the top N senders by authored-email volume for human review, with
placeholder evidence columns the reviewer fills in. It does NOT invent
evidence URLs — that would be worse than an empty cell in a reviewed paper.
"""
import argparse
import csv
import sqlite3
from pathlib import Path


def run(db_path: Path, out_csv: Path, top_n: int) -> None:
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        """SELECT p.person_id, p.canonical_email, p.domain, p.is_enron,
                  p.role, p.role_source, p.is_automated, COUNT(*) AS sent_count
           FROM email e JOIN person p ON p.person_id = e.from_person_id
           GROUP BY p.person_id
           ORDER BY sent_count DESC
           LIMIT ?""",
        (top_n,),
    ).fetchall()

    with out_csv.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "person_id", "canonical_email", "domain", "is_enron", "sent_count",
            "is_automated", "domain_rule_role",
            "recommended_role", "evidence_tier", "evidence_url", "evidence_quote",
            "confidence", "reviewer_notes",
        ])
        for person_id, addr, domain, is_enron, role, role_source, is_auto, sent_count in rows:
            w.writerow([
                person_id, addr, domain, is_enron, sent_count, is_auto, role,
                "",  # recommended_role — reviewer fills in
                "none",  # evidence_tier default; reviewer upgrades if evidence exists
                "", "", "", "",
            ])
    print(f"Wrote {len(rows)} rows to {out_csv}")
    conn.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--top-n", type=int, default=500)
    args = ap.parse_args()
    run(args.db, args.out, args.top_n)


if __name__ == "__main__":
    main()
