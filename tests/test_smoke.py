"""End-to-end smoke test: the whole pipeline over four custodians.

This is the single check that the pipeline still works on this machine. It
runs all five stages for real against the corpus and asserts the row counts
from a known-good run -- it is not a unit test and does not mock anything.

Needs the corpus. Point ENRON_MAILDIR at it (scripts/bootstrap.py does this
for you):

    ENRON_MAILDIR=~/data/enron/maildir python3 -m unittest discover -s tests -v

Takes about 4 minutes; almost all of it is stage 3 (spaCy, on CPU).
"""
import os
import subprocess
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "enron_ili"

CUSTODIANS = ["skilling-j", "lay-k", "allen-p", "sanders-r"]

# Known-good counts, measured 2026-09-22 against the CMU enron_mail_20150507
# release. These are exact, not approximate: the corpus is a fixed archive and
# every stage is deterministic. A mismatch means either an incomplete corpus
# extraction or a genuine behaviour change -- investigate, don't just update.
EXPECTED = {
    "email": 20439,
    "person": 14007,
    "body": 20439,
    "feature": 367902,
    "recipient": 148350,
}
EXPECTED_TOP_N_ROWS = 500
EXPECTED_PERSON_ROWS = 3592


def maildir() -> Path:
    raw = os.environ.get("ENRON_MAILDIR")
    if not raw:
        raise unittest.SkipTest(
            "ENRON_MAILDIR is not set -- point it at the corpus maildir. "
            "See docs/SETUP.md."
        )
    path = Path(raw).expanduser()
    if not path.is_dir():
        raise unittest.SkipTest(f"ENRON_MAILDIR does not exist: {path}")
    return path


class TestPipelineSmoke(unittest.TestCase):
    """Runs the five stages in order, then checks the outputs."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.maildir = maildir()
        cls._tmp = tempfile.TemporaryDirectory(prefix="enron-smoke-")
        tmp = Path(cls._tmp.name)
        cls.db = tmp / "enron.sqlite"
        cls.top_csv = tmp / "top500.csv"
        cls.stats_csv = tmp / "person_stats.csv"

        cls.stage(
            "ingest", "--db", cls.db, "--maildir", cls.maildir,
            "--custodians", *CUSTODIANS,
        )
        cls.stage("extract", "--db", cls.db, "--maildir", cls.maildir)
        cls.stage("analyze", "--db", cls.db)
        cls.stage("annotate", "--db", cls.db, "--out", cls.top_csv, "--top-n", "500")
        cls.stage("aggregate", "--db", cls.db, "--out", cls.stats_csv)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    @classmethod
    def stage(cls, name: str, *args) -> None:
        """Run one pipeline stage, failing the whole test class if it errors."""
        cmd = [sys.executable, str(SRC / f"{name}.py"), *map(str, args)]
        print(f"  [smoke] {name}.py ...", flush=True)
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise AssertionError(
                f"stage {name!r} exited {r.returncode}\n"
                f"--- stdout ---\n{r.stdout}\n--- stderr ---\n{r.stderr}"
            )

    def count(self, table: str) -> int:
        with sqlite3.connect(self.db) as conn:
            return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    def test_row_counts_match_known_good_run(self) -> None:
        for table, expected in EXPECTED.items():
            with self.subTest(table=table):
                self.assertEqual(
                    self.count(table), expected,
                    f"{table} row count differs from the known-good run. "
                    f"If the corpus extracted incompletely this will be low "
                    f"-- check you have 150 custodian directories.",
                )

    def test_annotate_writes_requested_number_of_rows(self) -> None:
        lines = self.top_csv.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), EXPECTED_TOP_N_ROWS + 1, "header + 500 rows")

    def test_aggregate_writes_person_statistics(self) -> None:
        lines = self.stats_csv.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), EXPECTED_PERSON_ROWS + 1, "header + person rows")
        self.assertIn("Mean Word Count", lines[0])

    def test_aggregate_fails_loudly_on_unknown_feature_version(self) -> None:
        """A version mismatch must be an error, not an empty file (see buglog bug-003)."""
        r = subprocess.run(
            [sys.executable, str(SRC / "aggregate.py"), "--db", str(self.db),
             "--out", str(self.stats_csv.with_name("never-written.csv")),
             "--feature-set-version", "v0-does-not-exist"],
            capture_output=True, text=True,
        )
        self.assertNotEqual(r.returncode, 0, "should exit non-zero")
        self.assertIn("no features found", r.stderr.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
