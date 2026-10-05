"""
retrieve.py: cosine-similarity top-k search over the local vector file, plus a
retrieval-only report that costs nothing once the index exists.

    python src/retrieve.py      # writes results/retrieval_report.csv and prints a summary

Retrieval hit = at least one expected article appears among the top-k chunks.
Only answerable and partial questions have expected articles, so unanswerable
questions are left out of the hit rate.
"""
import csv, json
from collections import defaultdict
from pathlib import Path

import numpy as np

import bedrock, config

ROOT = Path(__file__).resolve().parent.parent
IDX = ROOT / "data" / ("index_mock" if bedrock.MOCK else "index")


class Index:
    def __init__(self):
        self.chunks = [json.loads(l) for l in open(IDX / "chunks.jsonl", encoding="utf-8")]
        # float64: numpy's float32 matmul prints spurious warnings on Apple Silicon
        self.vecs = np.load(IDX / "chunks.npy").astype(np.float64)
        self.qvecs = np.load(IDX / "questions.npy").astype(np.float64)
        assert np.isfinite(self.vecs).all() and np.isfinite(self.qvecs).all(), "bad vectors in index"
        self.qids = (IDX / "question_ids.txt").read_text().split("\n")
        self.qpos = {q: i for i, q in enumerate(self.qids)}
        self.lang = np.array([c["lang"] for c in self.chunks])

    def search(self, qid: str, corpus: str, k: int = config.TOP_K):
        """Return the top-k chunks for a question within one corpus (en / hi / both)."""
        q = self.qvecs[self.qpos[qid]]
        # Vectors are unit length, so dot product = cosine similarity. numpy's
        # matmul prints spurious floating-point warnings on Apple Silicon; the
        # inputs are checked finite above and the result is checked here.
        with np.errstate(all="ignore"):
            scores = self.vecs @ q
        assert np.isfinite(scores).all(), "non-finite similarity scores"
        if corpus != "both":
            scores = np.where(self.lang == corpus, scores, -np.inf)
        top = np.argsort(-scores)[:k]
        return [dict(self.chunks[i], score=float(scores[i])) for i in top]


def format_context(hits):
    return "\n\n".join(f"[Excerpt {i} | {h['title']}]\n{h['text']}" for i, h in enumerate(hits, 1))


def main():
    idx = Index()
    questions = list(csv.DictReader(open(ROOT / "data" / "questions.csv", encoding="utf-8-sig")))
    rows, agg = [], defaultdict(lambda: [0, 0])
    for q in questions:
        expected = {a for a in q["expected_article_id"].split(";") if a}
        for corpus in config.CONDITIONS[q["language"]]:
            hits = idx.search(q["qid"], corpus)
            got = [h["article_id"] for h in hits]
            hit = bool(expected & set(got)) if expected else None
            rows.append(dict(qid=q["qid"], language=q["language"], corpus=corpus,
                             answerable=q["answerable"], expected=";".join(sorted(expected)),
                             retrieved=";".join(got), retrieved_langs=";".join(h["lang"] for h in hits),
                             top_score=round(hits[0]["score"], 4), hit=hit))
            if hit is not None:
                agg[(q["language"], corpus)][0] += hit
                agg[(q["language"], corpus)][1] += 1
    out = ROOT / "results" / ("retrieval_report_mock.csv" if bedrock.MOCK else "retrieval_report.csv")
    out.parent.mkdir(exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    print(f"Retrieval hit@{config.TOP_K} (answerable + partial questions only)")
    for (lang, corpus), (h, n) in sorted(agg.items()):
        print(f"  {lang:9} questions vs {corpus:4} articles: {h}/{n} = {h/n:.0%}")
    print(f"Detail: {out}")


if __name__ == "__main__":
    main()
