"""Content-based duplicate detection over authored text.

Distinct from ingest.py's Message-ID dedup (same file appearing under
multiple custodians/folders). This finds DIFFERENT Message-IDs whose
authored_text -- i.e. text attributed to the sender with quoted/forwarded
history and trailing signatures already stripped by extract.py -- is
exactly identical after normalisation. It does not touch the schema: it
reads body.authored_text and writes a standalone report file, per project
decision to keep this a separate, reviewable artefact rather than a
new stage_status stage.

Exact-match only (v1). Fuzzy/near-duplicate matching is a deliberate
fast-follow, not attempted here.
"""
import argparse
import csv
import hashlib
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

# Below this length, short generic replies ("Thanks!", "OK", "FYI, see below")
# would spuriously cluster into large "duplicate" groups despite not being
# meaningful content duplication. Exclude them from grouping.
MIN_CHARS_FOR_DEDUP = 40

_WS_RE = re.compile(r"\s+")


def normalize(text: str) -> str:
    return _WS_RE.sub(" ", text.strip().lower())


def content_hash(normalized: str) -> str:
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def run(db_path: Path, out_csv: Path, min_chars: int = MIN_CHARS_FOR_DEDUP) -> None:
    conn = sqlite3.connect(db_path)

    rows = conn.execute(
        """SELECT b.email_id, b.authored_text, e.message_id, e.from_address,
                  e.custodian, e.source_path, e.date_utc
           FROM body b JOIN email e ON e.email_id = b.email_id"""
    ).fetchall()

    groups: dict[str, list[tuple]] = defaultdict(list)
    skipped_short = 0
    for email_id, authored_text, message_id, from_address, custodian, source_path, date_utc in rows:
        text = authored_text or ""
        norm = normalize(text)
        if len(norm) < min_chars:
            skipped_short += 1
            continue
        h = content_hash(norm)
        groups[h].append((email_id, message_id, from_address, custodian, source_path, date_utc, len(text)))

    dup_groups = {h: members for h, members in groups.items() if len(members) > 1}

    with out_csv.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "group_id", "content_hash", "group_size", "email_id", "message_id",
            "from_address", "custodian", "source_path", "date_utc",
            "authored_char_count", "is_group_representative",
        ])
        for group_id, (h, members) in enumerate(
            sorted(dup_groups.items(), key=lambda kv: -len(kv[1])), 1
        ):
            members_sorted = sorted(members, key=lambda m: m[0])  # by email_id
            for i, (email_id, message_id, from_address, custodian, source_path, date_utc, char_count) in enumerate(members_sorted):
                w.writerow([
                    group_id, h, len(members_sorted), email_id, message_id,
                    from_address, custodian, source_path, date_utc,
                    char_count, int(i == 0),
                ])

    total_emails_considered = len(rows) - skipped_short
    total_in_dup_groups = sum(len(m) for m in dup_groups.values())
    print(f"Emails scanned: {len(rows)}")
    print(f"Skipped (authored_text < {min_chars} chars after normalisation): {skipped_short}")
    print(f"Emails eligible for dedup comparison: {total_emails_considered}")
    print(f"Duplicate groups found: {len(dup_groups)}")
    print(f"Emails involved in a duplicate group: {total_in_dup_groups}")
    print(f"Wrote {out_csv}")
    conn.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--min-chars", type=int, default=MIN_CHARS_FOR_DEDUP)
    args = ap.parse_args()
    run(args.db, args.out, args.min_chars)


if __name__ == "__main__":
    main()
