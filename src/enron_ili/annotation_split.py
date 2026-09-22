"""Divide the top-N annotation sheet between reviewers.

Two requirements shape this, both from docs/methodology-briefing.md §3:

1. Every row is reviewed, and no row is reviewed twice by accident -- duplicate
   effort is waste, and conflicting duplicate labels are worse than waste.
2. A deliberate subset IS reviewed by everyone, so inter-rater agreement can be
   reported. Agreement cannot be reconstructed after the fact, so the overlap
   has to be built in from the start.

The shared subset is spread evenly across the whole sheet rather than taken
from the top. The highest-volume senders are the executives -- the easiest
people in the corpus to identify -- so agreement measured only on them would
be flattering and meaningless.
"""

Rows = list[dict[str, str]]


def split_rows(
    rows: Rows, reviewers: list[str], overlap: int
) -> tuple[dict[str, Rows], list[str]]:
    """Assign rows to reviewers.

    Returns (assignment, shared_person_ids). Every reviewer receives all the
    shared rows plus a disjoint share of the rest. Deterministic: the same
    inputs always give the same split, so it can be re-run without reshuffling
    work someone has already started.

    With a single reviewer the overlap is dropped -- agreement needs at least
    two people, and they would otherwise just get duplicate rows.
    """
    if not reviewers:
        raise ValueError("need at least one reviewer")
    if overlap < 0:
        raise ValueError("overlap cannot be negative")
    if overlap > len(rows):
        raise ValueError(
            f"overlap of {overlap} exceeds the {len(rows)} rows in the sheet"
        )

    if len(reviewers) == 1:
        return {reviewers[0]: list(rows)}, []

    # Evenly spaced indices across the sheet, so the agreement set covers
    # high- and low-volume senders alike.
    if overlap:
        step = len(rows) / overlap
        shared_idx = {min(int(i * step), len(rows) - 1) for i in range(overlap)}
    else:
        shared_idx = set()

    shared_rows = [rows[i] for i in sorted(shared_idx)]
    shared_ids = [r["person_id"] for r in shared_rows]

    assignment: dict[str, Rows] = {name: list(shared_rows) for name in reviewers}

    # Round-robin the rest. Contiguous blocks would hand one reviewer every
    # high-volume sender, which is both unbalanced in effort and confounded:
    # that reviewer alone would face the well-documented executives.
    rest = [r for i, r in enumerate(rows) if i not in shared_idx]
    for i, row in enumerate(rest):
        assignment[reviewers[i % len(reviewers)]].append(row)

    return assignment, shared_ids
