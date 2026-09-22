"""Walk a maildir tree, parse RFC-822 headers, dedupe on Message-ID, populate
person/email/recipient tables. No body extraction here (see extract.py) and
no NLP (see analyze.py) — this stage only needs headers.
"""
import argparse
import email
import email.utils
import hashlib
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

STAGE_VERSION = "v1"

# Enron used both enron.com and enron.net for internal addresses (the latter
# mostly Lotus Notes-migrated accounts); both count as Enron for the domain rule.
ENRON_DOMAINS = ("enron.com", "enron.net")

AUTOMATED_TOKENS = (
    "no-reply", "noreply", "postmaster", "mailer-daemon", "listserv",
    "announce", "announcements", "webmaster", "notification", "notifications",
    "bounce", "listmanager", "majordomo",
)


def canonical_email(addr: str) -> str:
    return addr.strip().lower()


def is_automated(addr: str) -> bool:
    local = addr.split("@", 1)[0].lower()
    return any(tok in local for tok in AUTOMATED_TOKENS)


def get_or_create_person(conn: sqlite3.Connection, addr: str) -> int:
    addr = canonical_email(addr)
    if not addr or "@" not in addr:
        addr = addr or "unknown@unknown"
    row = conn.execute(
        "SELECT person_id FROM address_alias WHERE email_address = ?", (addr,)
    ).fetchone()
    if row:
        return row[0]

    domain = addr.rsplit("@", 1)[-1]
    is_enron_domain = domain in ENRON_DOMAINS
    role = "Employee" if is_enron_domain else "Other"
    cur = conn.execute(
        """INSERT INTO person
               (canonical_email, domain, is_enron, is_automated,
                role, role_source, evidence_tier, needs_review)
           VALUES (?, ?, ?, ?, ?, 'domain_rule', 'none', 1)""",
        (addr, domain, int(is_enron_domain), int(is_automated(addr)), role),
    )
    person_id = cur.lastrowid
    conn.execute(
        "INSERT INTO address_alias (email_address, person_id) VALUES (?, ?)",
        (addr, person_id),
    )
    return person_id


def parse_date_utc(raw_date: str | None) -> str | None:
    if not raw_date:
        return None
    try:
        dt = email.utils.parsedate_to_datetime(raw_date)
    except (TypeError, ValueError):
        return None
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def subject_hash(subject: str | None) -> str | None:
    if subject is None:
        return None
    return hashlib.sha256(subject.encode("utf-8", errors="replace")).hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def ingest_file(conn: sqlite3.Connection, path: Path, maildir_root: Path) -> None:
    rel = path.relative_to(maildir_root)
    custodian = rel.parts[0]
    folder = str(Path(*rel.parts[1:-1])) if len(rel.parts) > 2 else ""

    raw = path.read_bytes()
    msg = email.message_from_bytes(raw)

    message_id = msg.get("Message-ID", "").strip()
    if not message_id:
        # Fall back to a content hash so every file still gets a stable key.
        message_id = "sha256:" + hashlib.sha256(raw).hexdigest()

    existing = conn.execute(
        "SELECT email_id, copy_count FROM email WHERE message_id = ?",
        (message_id,),
    ).fetchone()
    if existing:
        email_id, copy_count = existing
        conn.execute(
            "UPDATE email SET copy_count = ? WHERE email_id = ?",
            (copy_count + 1, email_id),
        )
        return

    from_raw = email.utils.parseaddr(msg.get("From", ""))[1] or "unknown@unknown"
    from_person_id = get_or_create_person(conn, from_raw)

    cur = conn.execute(
        """INSERT INTO email
               (message_id, date_utc, from_address, from_person_id,
                subject_hash, custodian, folder, source_path, copy_count)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)""",
        (
            message_id,
            parse_date_utc(msg.get("Date")),
            canonical_email(from_raw),
            from_person_id,
            subject_hash(msg.get("Subject")),
            custodian,
            folder,
            str(rel),
        ),
    )
    email_id = cur.lastrowid

    for kind, header in (("to", "To"), ("cc", "Cc"), ("bcc", "Bcc")):
        for _, addr in email.utils.getaddresses(msg.get_all(header, [])):
            if not addr:
                continue
            addr = canonical_email(addr)
            person_id = get_or_create_person(conn, addr)
            conn.execute(
                """INSERT OR IGNORE INTO recipient (email_id, person_id, address, kind)
                   VALUES (?, ?, ?, ?)""",
                (email_id, person_id, addr, kind),
            )

    conn.execute(
        """INSERT OR REPLACE INTO stage_status
               (email_id, stage, version, status, error, updated_utc)
           VALUES (?, 'parsed', ?, 'done', NULL, ?)""",
        (email_id, STAGE_VERSION, now_utc()),
    )


def run(db_path: Path, maildir_root: Path, custodians: list[str], batch_size: int = 500) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    schema = (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")
    conn.executescript(schema)

    files = []
    for custodian in custodians:
        files.extend(sorted((maildir_root / custodian).rglob("*")))
    files = [f for f in files if f.is_file()]

    total = len(files)
    print(f"Ingesting {total} files from {len(custodians)} custodian(s)", file=sys.stderr)

    errors = 0
    for i, path in enumerate(files, 1):
        try:
            ingest_file(conn, path, maildir_root)
        except Exception as exc:  # noqa: BLE001 — record and continue; this is a 517k-file batch job
            errors += 1
            print(f"ERROR {path}: {exc}", file=sys.stderr)
        if i % batch_size == 0:
            conn.commit()
            print(f"  {i}/{total}", file=sys.stderr)
    conn.commit()

    n_email = conn.execute("SELECT COUNT(*) FROM email").fetchone()[0]
    n_person = conn.execute("SELECT COUNT(*) FROM person").fetchone()[0]
    n_recipient = conn.execute("SELECT COUNT(*) FROM recipient").fetchone()[0]
    dup_total = conn.execute("SELECT SUM(copy_count) - COUNT(*) FROM email").fetchone()[0]
    print(
        f"Done. files={total} errors={errors} unique_emails={n_email} "
        f"persons={n_person} recipient_rows={n_recipient} duplicate_copies={dup_total}",
        file=sys.stderr,
    )
    conn.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--maildir", type=Path, required=True)
    ap.add_argument("--custodians", nargs="+", required=True)
    args = ap.parse_args()
    run(args.db, args.maildir, args.custodians)


if __name__ == "__main__":
    main()
