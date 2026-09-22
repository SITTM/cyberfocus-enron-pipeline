"""Roll feature rows up to per-person, per-role summary statistics.

Per docs/methodology-briefing.md §4: aggregation uses per-email MEANS, not
raw sums, so a high-volume sender does not dominate a group statistic simply
by writing more email.
"""
import argparse
import csv
import sqlite3
from pathlib import Path

# Universal POS tag -> plain-English label, for column headers.
POS_LABELS = {
    "ADJ": "Adjective",
    "ADP": "Adposition",
    "ADV": "Adverb",
    "AUX": "Auxiliary Verb",
    "CCONJ": "Coordinating Conjunction",
    "DET": "Determiner",
    "INTJ": "Interjection",
    "NOUN": "Noun",
    "NUM": "Numeral",
    "PART": "Particle",
    "PRON": "Pronoun",
    "PROPN": "Proper Noun",
    "PUNCT": "Punctuation",
    "SCONJ": "Subordinating Conjunction",
    "SYM": "Symbol",
    "VERB": "Verb",
    "X": "Other/Unclassified",
}

BASE_COLUMN_TITLES = {
    "person_id": "Person ID",
    "canonical_email": "Email Address",
    "role": "Role",
    "n_emails": "Number of Emails",
}


def feature_column_title(feature_name: str) -> str:
    """Turn a raw feature name (e.g. 'pos_ADJ', 'word_count') into a mean-column title."""
    if feature_name == "word_count":
        return "Mean Word Count"
    if feature_name.startswith("pos_"):
        tag = feature_name[len("pos_"):]
        label = POS_LABELS.get(tag, tag)
        return f"Mean {label} Count"
    return f"Mean {feature_name}"


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
        # Exiting 0 here would make a mismatched --feature-set-version look like
        # a successful run that happened to have nothing to say. It doesn't:
        # it means analyze.py has not populated this version.
        available = [
            r[0] for r in conn.execute(
                "SELECT DISTINCT feature_set_version FROM feature ORDER BY 1"
            )
        ]
        conn.close()
        raise SystemExit(
            f"aggregate.py: no features found for version {feature_set_version!r}.\n"
            + (
                f"  Versions present in {db_path}: {', '.join(available)}\n"
                f"  Re-run with --feature-set-version matching one of those."
                if available else
                f"  The feature table is empty -- run analyze.py against {db_path} first."
            )
        )

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

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [BASE_COLUMN_TITLES["person_id"], BASE_COLUMN_TITLES["canonical_email"],
             BASE_COLUMN_TITLES["role"], BASE_COLUMN_TITLES["n_emails"]]
            + [feature_column_title(n) for n in feature_names]
        )
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
    # must match analyze.FEATURE_VERSION -- a stale default here silently
    # produces an empty report on a DB that only holds the current version.
    ap.add_argument("--feature-set-version", default="v2-placeholder")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--min-emails", type=int, default=0)
    args = ap.parse_args()
    run(args.db, args.feature_set_version, args.out, args.min_emails)


if __name__ == "__main__":
    main()
