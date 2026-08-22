"""Roll feature rows up to per-person, per-role summary statistics.

Per docs/methodology-briefing.md §4: aggregation uses per-email MEANS, not
raw sums, so a high-volume sender does not dominate a group statistic simply
by writing more email.
"""
import argparse
import csv
import sqlite3
from pathlib import Path


def run(db_path: Path, feature_set_version: str, out_csv: Path, min_emails: int = 0) -> None:
    conn = sqlite3.connect(db_path)

    feature_names = [
        r[0]
        for r in conn.execute(
            "SELECT DISTINCT feature_name FROM feature WHERE feature_set_version = ? ORDER BY feature_name",
            (feature_set_version,),
        )
    ]
    if not feature_names:
        print(f"No features found for version {feature_set_version}")
        return

    person_rows = conn.execute(
        """SELECT p.person_id, p.canonical_email, p.role, COUNT(DISTINCT e.email_id) AS n_emails
           FROM person p
           JOIN email e ON e.from_person_id = p.person_id
           JOIN feature f ON f.email_id = e.email_id AND f.feature_set_version = ?
           GROUP BY p.person_id
           HAVING n_emails >= ?
           ORDER BY n_emails DESC""",
        (feature_set_version, min_emails),
    ).fetchall()

    with out_csv.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["person_id", "canonical_email", "role", "n_emails"] + [f"mean_{n}" for n in feature_names])
        for person_id, addr, role, n_emails in person_rows:
            means = conn.execute(
                """SELECT f.feature_name, AVG(f.value)
                   FROM feature f JOIN email e ON e.email_id = f.email_id
                   WHERE e.from_person_id = ? AND f.feature_set_version = ?
                   GROUP BY f.feature_name""",
                (person_id, feature_set_version),
            ).fetchall()
            mean_by_name = dict(means)
            w.writerow(
                [person_id, addr, role, n_emails]
                + [mean_by_name.get(n, "") for n in feature_names]
            )

    print(f"Wrote {len(person_rows)} person rows to {out_csv}")
    conn.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--feature-set-version", default="v1-placeholder")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--min-emails", type=int, default=0)
    args = ap.parse_args()
    run(args.db, args.feature_set_version, args.out, args.min_emails)


if __name__ == "__main__":
    main()
