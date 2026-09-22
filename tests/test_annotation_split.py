"""Unit tests for dividing the annotation sheet between reviewers.

Fast and corpus-free, unlike test_smoke.py.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from enron_ili.annotation_split import split_rows


def rows(n: int) -> list[dict]:
    """n rows in descending sent_count order, as annotate.py emits them."""
    return [{"person_id": str(i), "sent_count": str(n - i)} for i in range(n)]


class TestSplitRows(unittest.TestCase):
    REVIEWERS = ["ana", "ben", "cleo"]

    def test_every_row_is_assigned_to_someone(self) -> None:
        assignment, _ = split_rows(rows(500), self.REVIEWERS, overlap=50)
        seen = {r["person_id"] for rs in assignment.values() for r in rs}
        self.assertEqual(len(seen), 500)

    def test_overlap_rows_go_to_every_reviewer(self) -> None:
        assignment, shared = split_rows(rows(500), self.REVIEWERS, overlap=50)
        self.assertEqual(len(shared), 50)
        for name in self.REVIEWERS:
            got = {r["person_id"] for r in assignment[name]}
            self.assertTrue(set(shared).issubset(got), f"{name} is missing shared rows")

    def test_non_overlap_rows_are_assigned_exactly_once(self) -> None:
        assignment, shared = split_rows(rows(500), self.REVIEWERS, overlap=50)
        counts: dict[str, int] = {}
        for rs in assignment.values():
            for r in rs:
                if r["person_id"] not in shared:
                    counts[r["person_id"]] = counts.get(r["person_id"], 0) + 1
        self.assertEqual(set(counts.values()), {1}, "a row was double-assigned")

    def test_workload_is_balanced(self) -> None:
        assignment, _ = split_rows(rows(500), self.REVIEWERS, overlap=50)
        sizes = sorted(len(v) for v in assignment.values())
        self.assertLessEqual(sizes[-1] - sizes[0], 1, f"unbalanced: {sizes}")

    def test_shared_set_spans_the_volume_range(self) -> None:
        """Agreement must not be measured only on high-volume senders, who are
        the easiest to identify and would flatter the score."""
        _, shared = split_rows(rows(500), self.REVIEWERS, overlap=50)
        idx = sorted(int(p) for p in shared)
        self.assertLess(idx[0], 50, "no shared rows near the top")
        self.assertGreater(idx[-1], 450, "no shared rows near the bottom")

    def test_is_deterministic(self) -> None:
        a1, s1 = split_rows(rows(500), self.REVIEWERS, overlap=50)
        a2, s2 = split_rows(rows(500), self.REVIEWERS, overlap=50)
        self.assertEqual(s1, s2)
        self.assertEqual({k: [r["person_id"] for r in v] for k, v in a1.items()},
                         {k: [r["person_id"] for r in v] for k, v in a2.items()})

    def test_single_reviewer_gets_everything(self) -> None:
        assignment, shared = split_rows(rows(100), ["ana"], overlap=10)
        self.assertEqual(len(assignment["ana"]), 100)
        self.assertEqual(shared, [])  # overlap is meaningless with one reviewer

    def test_overlap_larger_than_sheet_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            split_rows(rows(10), self.REVIEWERS, overlap=20)

    def test_no_reviewers_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            split_rows(rows(10), [], overlap=0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
