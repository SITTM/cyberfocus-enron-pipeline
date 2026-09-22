"""Build the full-corpus database and produce the annotation sheets.

Run this after the setup (scripts/bootstrap.ps1 on Windows,
scripts/bootstrap-v2.py otherwise) has reported success.

    python3 scripts/prepare_annotation.py --reviewers ana ben cleo

It:
    1. finds your corpus (never re-downloads)
    2. ingests ALL 150 custodians -- not the four from the smoke test
    3. writes annotations/top500.csv
    4. splits it into one sheet per reviewer, with a deliberate overlap
       so inter-rater agreement can be measured

Resumable and safe to re-run: ingest skips emails already in the database,
and the split is deterministic, so nobody's rows get reshuffled.

Only stage 1 (ingest) is needed here -- annotate.py reads the `email` and
`person` tables and nothing else. The slow spaCy stage is NOT required to
start annotating; run it separately while the annotation is under way.
"""
import argparse
import csv
import functools
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from enron_ili.annotation_split import split_rows  # noqa: E402

print = functools.partial(print, flush=True)

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "enron_ili"
DB = ROOT / "db" / "enron.sqlite"
OUT = ROOT / "annotations"
EXPECTED_CUSTODIANS = 150


def venv_python() -> Path:
    p = (ROOT / ".venv" / ("Scripts" if sys.platform == "win32" else "bin")
         / ("python.exe" if sys.platform == "win32" else "python"))
    if not p.exists():
        sys.exit("No .venv found -- run the setup first: bootstrap.ps1 on "
                 "Windows, scripts/bootstrap-v2.py otherwise.")
    return p


def find_corpus(explicit: Path | None) -> Path:
    """Reuse bootstrap's detection so the two scripts never disagree."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "bootstrap", ROOT / "scripts" / "bootstrap.py")
    bs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bs)

    if explicit and explicit.name != "maildir":
        explicit = explicit / "maildir"
    found = bs.find_corpus(explicit.expanduser() if explicit else None)
    if not found:
        sys.exit(
            "Could not find the corpus. Run the setup first, or "
            "pass --corpus with the path to it."
        )
    return found


def ingest_all(maildir: Path) -> None:
    custodians = sorted(p.name for p in maildir.iterdir() if p.is_dir())
    if len(custodians) < EXPECTED_CUSTODIANS:
        sys.exit(
            f"Only {len(custodians)} custodian directories in {maildir}, "
            f"expected {EXPECTED_CUSTODIANS}. The corpus is incomplete -- "
            f"re-run the setup. Not continuing, because the top 500 "
            f"senders of a partial corpus are not the top 500 of the corpus."
        )
    DB.parent.mkdir(parents=True, exist_ok=True)
    print(f"[..] ingesting all {len(custodians)} custodians (~6 minutes)")
    subprocess.run(
        [str(venv_python()), str(SRC / "ingest.py"), "--db", str(DB),
         "--maildir", str(maildir), "--custodians", *custodians],
        check=True,
    )
    print("[ok] ingest complete")


def write_sheet(top_n: int) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    sheet = OUT / f"top{top_n}.csv"
    print(f"[..] writing {sheet.name}")
    subprocess.run(
        [str(venv_python()), str(SRC / "annotate.py"), "--db", str(DB),
         "--out", str(sheet), "--top-n", str(top_n)],
        check=True,
    )
    return sheet


def split(sheet: Path, reviewers: list[str], overlap: int) -> None:
    with sheet.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        rows = list(reader)

    assignment, shared = split_rows(rows, reviewers, overlap)

    for name, their_rows in assignment.items():
        # Keep each reviewer's sheet in the sheet's own order, so the most
        # prolific senders come first rather than the shared rows.
        order = {r["person_id"]: i for i, r in enumerate(rows)}
        their_rows.sort(key=lambda r: order[r["person_id"]])
        path = OUT / f"{sheet.stem}_{name}.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=header)
            w.writeheader()
            w.writerows(their_rows)
        print(f"[ok] {path.name}: {len(their_rows)} rows")

    # The shared set is recorded here and NOT marked in the reviewers' sheets --
    # telling someone which rows are being checked would bias those rows.
    manifest = OUT / f"{sheet.stem}_manifest.json"
    manifest.write_text(json.dumps({
        "generated": date.today().isoformat(),
        "source_sheet": sheet.name,
        "total_rows": len(rows),
        "reviewers": reviewers,
        "overlap": len(shared),
        "shared_person_ids": shared,
        "note": "shared_person_ids are the rows every reviewer sees, for "
                "inter-rater agreement. Do not share this file with reviewers.",
    }, indent=2), encoding="utf-8")
    print(f"[ok] {manifest.name} (keep this one back from the reviewers)")


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--reviewers", nargs="+", required=True,
                    help="one short name per reviewer, e.g. --reviewers ana ben cleo")
    ap.add_argument("--overlap", type=int, default=50,
                    help="rows every reviewer gets, for agreement (default: 50)")
    ap.add_argument("--top-n", type=int, default=500,
                    help="how many senders to review (default: 500)")
    ap.add_argument("--corpus", type=Path, default=None,
                    help="corpus location, if it isn't where bootstrap put it")
    args = ap.parse_args()

    maildir = find_corpus(args.corpus)
    ingest_all(maildir)
    sheet = write_sheet(args.top_n)
    split(sheet, args.reviewers, args.overlap)

    print(
        f"\n{'=' * 68}\n"
        f"Annotation sheets are in {OUT}/\n\n"
        f"These stay on your machine -- nothing needs sending anywhere.\n\n"
        f"Do NOT commit any of it. This repository is public and these files\n"
        f"contain real people's email addresses; `git add -f` would publish\n"
        f"them permanently.\n\n"
        f"If you are dividing the work between people, send each person only\n"
        f"their own file and keep the manifest back -- it lists the rows\n"
        f"everyone reviews as a consistency check, and knowing which they are\n"
        f"biases them.\n\n"
        f"See 'The annotation task' in the ClickUp onboarding page. Leave\n"
        f"evidence_url blank where no public record exists -- an empty cell\n"
        f"is correct and expected for most rows.\n"
        f"{'=' * 68}\n"
    )


if __name__ == "__main__":
    main()
