"""
build_index.py: chunk the extracted articles, embed every chunk and every
question with Titan Text Embeddings V2, and save the vectors locally.

    python src/build_index.py            # prints a cost estimate and stops
    python src/build_index.py --yes      # actually calls Bedrock

Outputs (git-ignored, contain article text):
    data/index/chunks.jsonl     one chunk per line: chunk_id, article_id, lang, title, text
    data/index/chunks.npy       chunk vectors, same order as chunks.jsonl
    data/index/questions.npy    question vectors, same order as data/questions.csv
"""
import argparse, csv, json, sys
from pathlib import Path

import numpy as np

import bedrock, config

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / ("index_mock" if bedrock.MOCK else "index")


def chunk_article(title: str, body: str, max_chars: int):
    """Pack paragraphs into chunks of at most max_chars. Each chunk starts with
    the article title so a chunk on its own still says what it is about."""
    paras = [p.strip() for p in body.split("\n") if p.strip()]
    chunks, cur = [], ""
    for p in paras:
        if cur and len(cur) + len(p) + 1 > max_chars:
            chunks.append(cur)
            cur = ""
        cur = f"{cur}\n{p}" if cur else p
    if cur:
        chunks.append(cur)
    return [f"{title}\n{c}" for c in chunks]


def load_chunks():
    rows = list(csv.DictReader(open(DATA / "articles_index.csv", encoding="utf-8")))
    chunks = []
    for r in rows:
        text = (DATA / "articles" / f"{r['id']}.txt").read_text(encoding="utf-8")
        title, _, body = text.partition("\n\n")
        for i, c in enumerate(chunk_article(title, body, config.CHUNK_MAX_CHARS)):
            chunks.append(dict(chunk_id=f"{r['id']}#{i}", article_id=r["nodeId"],
                               lang=r["lang"], title=title, text=c))
    return chunks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--yes", action="store_true", help="make the paid Bedrock calls")
    args = ap.parse_args()

    chunks = load_chunks()
    questions = list(csv.DictReader(open(DATA / "questions.csv", encoding="utf-8-sig")))
    # Rough token estimate: ~4 chars/token for English, ~1.2 for Hindi pages
    # (calibrated on the first real run: 62,191 actual tokens).
    est_tokens = sum(len(c["text"]) / (1.2 if c["lang"] == "hi" else 4) for c in chunks) \
        + sum(len(q["question"]) / 2 for q in questions)
    est_cost = est_tokens / 1e6 * config.EMBED_PRICE_PER_M
    print(f"{len(chunks)} chunks ({sum(c['lang']=='en' for c in chunks)} en, "
          f"{sum(c['lang']=='hi' for c in chunks)} hi) + {len(questions)} questions")
    print(f"Estimated embedding tokens: ~{est_tokens:,.0f}  ->  estimated cost ~${est_cost:.4f}")
    if not (args.yes or bedrock.MOCK):
        print("Dry run only. Re-run with --yes to call Bedrock.")
        sys.exit(0)

    OUT.mkdir(parents=True, exist_ok=True)
    vecs, used = [], 0
    for i, c in enumerate(chunks, 1):
        v, n = bedrock.embed(c["text"]); vecs.append(v); used += n
        print(f"\rchunks {i}/{len(chunks)}", end="", flush=True)
    qvecs = []
    for i, q in enumerate(questions, 1):
        v, n = bedrock.embed(q["question"]); qvecs.append(v); used += n
        print(f"\rquestions {i}/{len(questions)}   ", end="", flush=True)
    print()
    np.save(OUT / "chunks.npy", np.vstack(vecs).astype(np.float32))
    np.save(OUT / "questions.npy", np.vstack(qvecs).astype(np.float32))
    with open(OUT / "chunks.jsonl", "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    (OUT / "question_ids.txt").write_text("\n".join(q["qid"] for q in questions))
    print(f"Done. Actual embedding tokens: {used:,}  ->  cost ${used/1e6*config.EMBED_PRICE_PER_M:.4f}")


if __name__ == "__main__":
    main()
