"""Body extraction: separate authored text from quoted/forwarded text.

Primary splitter is quotequail (Outlook-idiom aware). A supplementary regex
pass catches the Lotus Notes quote idiom that quotequail does not model
(see troubleshooting.log, 2026-08-22) — Enron mailboxes are heavily Lotus
Notes / cc:Mail in origin. Whichever cut point comes first wins.

This is a heuristic, not a validated parser. docs/prior-work-survey.md §3.1/§7
call for hand-annotating 300-500 bodies and reporting extraction precision/
recall before results are trusted — that validation has not been done yet.
"""
import argparse
import email
import email.message
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import quotequail

EXTRACT_VERSION = "v1"
PARSE_VERSION = "v1"  # must match ingest.STAGE_VERSION for the 'parsed' stage

# Lotus Notes / cc:Mail quote idiom: "Name <addr> on MM/DD/YYYY HH:MM:SS AM/PM"
# followed eventually by To:/cc:/Subject: lines, no ">" quote markers.
_LOTUS_WROTE_RE = re.compile(
    r"^.{0,120}\bon\s+\d{1,2}/\d{1,2}/\d{2,4}\s+\d{1,2}:\d{2}(:\d{2})?\s*(AM|PM)?\s*$",
    re.MULTILINE,
)
_LOTUS_FORWARD_RE = re.compile(
    r"^-{5,}\s*Forwarded by .+ on \d{1,2}/\d{1,2}/\d{2,4}", re.MULTILINE
)

# Simplified trailing-signature heuristic (not a full port of talon's
# bruteforce scorer — see troubleshooting.log). Strips a short trailing
# block introduced by a standalone closing word.
_SIGNOFF_RE = re.compile(
    r"^\s*(thanks|thank you|regards|best regards|best|sincerely|cheers)[,.]?\s*$",
    re.IGNORECASE,
)


def _first_lotus_cut(text: str) -> int | None:
    positions = [m.start() for m in _LOTUS_WROTE_RE.finditer(text)]
    positions += [m.start() for m in _LOTUS_FORWARD_RE.finditer(text)]
    return min(positions) if positions else None


def _strip_signature(text: str) -> str:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if _SIGNOFF_RE.match(line) and (len(lines) - i) <= 8:
            return "\n".join(lines[:i]).rstrip()
    return text


def split_body(text: str) -> tuple[str, str]:
    """Return (authored_text, quoted_text)."""
    if not text:
        return "", ""

    qq_cut = None
    for expand, chunk in quotequail.quote(text):
        if not expand:
            qq_cut = text.find(chunk)
            break

    lotus_cut = _first_lotus_cut(text)

    candidates = [c for c in (qq_cut, lotus_cut) if c is not None]
    cut = min(candidates) if candidates else len(text)

    authored = _strip_signature(text[:cut].rstrip())
    quoted = text[cut:]
    return authored, quoted


def get_plain_text_body(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload is not None:
                    return payload.decode("utf-8", errors="replace")
        return ""
    payload = msg.get_payload(decode=True)
    if payload is not None:
        return payload.decode("utf-8", errors="replace")
    return msg.get_payload() or ""


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(db_path: Path, maildir_root: Path, batch_size: int = 500) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    rows = conn.execute(
        """SELECT e.email_id, e.source_path FROM email e
           JOIN stage_status s ON s.email_id = e.email_id
               AND s.stage = 'parsed' AND s.version = ? AND s.status = 'done'
           WHERE NOT EXISTS (
               SELECT 1 FROM stage_status b WHERE b.email_id = e.email_id
                   AND b.stage = 'bodied' AND b.version = ? AND b.status = 'done'
           )""",
        (PARSE_VERSION, EXTRACT_VERSION),
    ).fetchall()

    print(f"Extracting bodies for {len(rows)} email(s)")
    errors = 0
    for i, (email_id, source_path) in enumerate(rows, 1):
        path = maildir_root / source_path
        try:
            msg = email.message_from_bytes(path.read_bytes())
            text = get_plain_text_body(msg)
            authored, quoted = split_body(text)
            conn.execute(
                """INSERT OR REPLACE INTO body
                       (email_id, authored_text, quoted_text, char_count, extractor_version)
                   VALUES (?, ?, ?, ?, ?)""",
                (email_id, authored, quoted, len(authored), EXTRACT_VERSION),
            )
            conn.execute(
                """INSERT OR REPLACE INTO stage_status
                       (email_id, stage, version, status, error, updated_utc)
                   VALUES (?, 'bodied', ?, 'done', NULL, ?)""",
                (email_id, EXTRACT_VERSION, now_utc()),
            )
        except Exception as exc:  # noqa: BLE001 — record and continue over the batch
            errors += 1
            conn.execute(
                """INSERT OR REPLACE INTO stage_status
                       (email_id, stage, version, status, error, updated_utc)
                   VALUES (?, 'bodied', ?, 'error', ?, ?)""",
                (email_id, EXTRACT_VERSION, str(exc), now_utc()),
            )
        if i % batch_size == 0:
            conn.commit()
            print(f"  {i}/{len(rows)}")
    conn.commit()
    print(f"Done. errors={errors}")
    conn.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--maildir", type=Path, required=True)
    args = ap.parse_args()
    run(args.db, args.maildir)


if __name__ == "__main__":
    main()
