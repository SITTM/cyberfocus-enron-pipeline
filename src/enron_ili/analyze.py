"""Placeholder linguistic analysis: word count + Universal POS tag counts.

This is explicitly a placeholder feature set (per project scope) pending the
real feature list. Because `feature` is long-format (email_id, version, name,
value), adding the real feature list later is new rows, not a schema change,
and does not require reprocessing emails already at this stage version.
"""
import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import spacy

FEATURE_VERSION = "v1-placeholder"
EXTRACT_VERSION = "v1"  # must match extract.EXTRACT_VERSION

UNIVERSAL_POS_TAGS = (
    "ADJ", "ADP", "ADV", "AUX", "CCONJ", "DET", "INTJ", "NOUN", "NUM",
    "PART", "PRON", "PROPN", "PUNCT", "SCONJ", "SYM", "VERB", "X",
)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def features_for_doc(doc) -> dict[str, float]:
    counts = dict.fromkeys(UNIVERSAL_POS_TAGS, 0)
    word_count = 0
    for tok in doc:
        if tok.is_space:
            continue
        if not tok.is_punct:
            word_count += 1
        if tok.pos_ in counts:
            counts[tok.pos_] += 1
    feats = {"word_count": float(word_count)}
    feats.update({f"pos_{tag}": float(v) for tag, v in counts.items()})
    return feats


def run(db_path: Path, batch_size: int = 200, n_process: int = 1, device: str = "cpu") -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    rows = conn.execute(
        """SELECT b.email_id, b.authored_text FROM body b
           JOIN stage_status s ON s.email_id = b.email_id
               AND s.stage = 'bodied' AND s.version = ? AND s.status = 'done'
           WHERE NOT EXISTS (
               SELECT 1 FROM stage_status a WHERE a.email_id = b.email_id
                   AND a.stage = 'analysed' AND a.version = ? AND a.status = 'done'
           )""",
        (EXTRACT_VERSION, FEATURE_VERSION),
    ).fetchall()

    print(f"Analysing {len(rows)} email(s) with feature_set_version={FEATURE_VERSION} device={device}")

    if device == "gpu":
        # Cap the cupy pool: this machine's GPU is shared with other processes
        # (e.g. a local llama-server) and typically has only 2-3GB free.
        # n_process must stay 1 -- multiprocessing would spawn multiple CUDA
        # contexts and is not supported for GPU pipes.
        import cupy

        cupy.get_default_memory_pool().set_limit(size=2 * 1024**3)
        spacy.require_gpu()
        n_process = 1

    nlp = spacy.load("en_core_web_sm", exclude=["ner", "lemmatizer", "parser"])

    ids = [r[0] for r in rows]
    texts = [r[1] or "" for r in rows]

    for i, (email_id, doc) in enumerate(
        zip(ids, nlp.pipe(texts, batch_size=batch_size, n_process=n_process)), 1
    ):
        feats = features_for_doc(doc)
        conn.executemany(
            """INSERT OR REPLACE INTO feature (email_id, feature_set_version, feature_name, value)
               VALUES (?, ?, ?, ?)""",
            [(email_id, FEATURE_VERSION, name, val) for name, val in feats.items()],
        )
        conn.execute(
            """INSERT OR REPLACE INTO stage_status
                   (email_id, stage, version, status, error, updated_utc)
               VALUES (?, 'analysed', ?, 'done', NULL, ?)""",
            (email_id, FEATURE_VERSION, now_utc()),
        )
        if i % 1000 == 0:
            conn.commit()
            print(f"  {i}/{len(rows)}")
    conn.commit()
    print("Done.")
    conn.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--n-process", type=int, default=1)
    ap.add_argument("--batch-size", type=int, default=None)
    ap.add_argument("--device", choices=["cpu", "gpu"], default="cpu")
    args = ap.parse_args()
    # Measured best on this machine (see troubleshooting.log): batch=512 for GPU,
    # 200 for CPU. Throughput is dominated by CPU-side tokenization contention
    # from other processes on this shared machine either way -- these are best
    # available defaults, not a tuned optimum.
    batch_size = args.batch_size or (512 if args.device == "gpu" else 200)
    run(args.db, batch_size=batch_size, n_process=args.n_process, device=args.device)


if __name__ == "__main__":
    main()
