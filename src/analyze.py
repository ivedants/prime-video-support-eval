"""Summarise results: results/summary_by_model_language.csv and results/summary_by_model.csv.

Inputs: results/run_log.csv (latency, tokens, cost per answer, no answer text), results/scores.csv (LLM-judge
scores), results/language_quality.csv (native-speaker language scores on a sample of Hindi/Hinglish answers).

If results/raw_answers.jsonl exists locally (it is git-ignored), run_log.csv is rebuilt from it first.
"""
import csv
import json
import statistics as st
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS = ["haiku-4.5", "llama4-maverick", "nova2-lite"]
CONDITIONS = [("en", "en"), ("hi", "en"), ("hi", "hi"), ("hi", "both"),
              ("hinglish", "en"), ("hinglish", "hi"), ("hinglish", "both")]


LOG_COLS = ["model", "model_id", "prompt_version", "qid", "pair_id", "language", "corpus", "category", "answerable",
            "expected_article_ids", "retrieved_article_ids", "retrieved_chunk_ids", "retrieval_hit", "input_tokens",
            "output_tokens", "latency_ms", "est_cost_usd", "stop_reason", "timestamp"]


def export_run_log():
    """Write results/run_log.csv from the local raw answers, leaving out the answer text."""
    src = ROOT / "results" / "raw_answers.jsonl"
    if not src.exists():
        return
    with open(ROOT / "results" / "run_log.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(LOG_COLS)
        for r in map(json.loads, open(src, encoding="utf-8")):
            w.writerow([";".join(r[c]) if isinstance(r[c], list) else r[c] for c in LOG_COLS])


def load():
    export_run_log()
    raw = {(r["model"], r["qid"], r["corpus"]): r
           for r in csv.DictReader(open(ROOT / "results" / "run_log.csv", encoding="utf-8"))}
    scores = list(csv.DictReader(open(ROOT / "results" / "scores.csv", encoding="utf-8")))
    lq = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "results" / "language_quality.csv", encoding="utf-8")):
        if r["native_speaker_quality"] != "":
            lq[(r["model"], r["qid"], r["corpus"])].append(int(r["native_speaker_quality"]))
    for s in scores:
        k = (s["model"], s["qid"], s["corpus"])
        s["latency_ms"] = float(raw[k]["latency_ms"])
        s["cost"] = float(raw[k]["est_cost_usd"])
        s["lq"] = lq.get(k, [None])[0]
        s["correctness"] = int(s["correctness"])
    return scores


def summarise(rows):
    n = len(rows)
    unans = [r for r in rows if r["answerable"] == "no"]
    partial = [r for r in rows if r["answerable"] == "partial"]
    lq = [r["lq"] for r in rows if r["lq"] is not None]
    return {
        "answers": n,
        "full_marks": sum(r["correctness"] == 2 for r in rows),
        "partial_marks": sum(r["correctness"] == 1 for r in rows),
        "zero": sum(r["correctness"] == 0 for r in rows),
        "full_marks_pct": round(100 * sum(r["correctness"] == 2 for r in rows) / n),
        "made_up": sum(r["made_up"] == "y" for r in rows),
        "wrong_language_or_script": sum(r["lang_match"] == "n" for r in rows),
        "unanswerable_declined": f"{sum(r['abstained'] == 'y' for r in unans)}/{len(unans)}",
        "partial_gap_flagged": f"{sum(r['abstained'] == 'y' for r in partial)}/{len(partial)}",
        "median_response_ms": round(st.median(r["latency_ms"] for r in rows)),
        "cost_per_1000_questions_usd": round(1000 * sum(r["cost"] for r in rows) / n, 2),
        "language_quality_scored": len(lq),
        "language_quality_mean_0_2": round(sum(lq) / len(lq), 2) if lq else "",
        "language_quality_twos": sum(x == 2 for x in lq) if lq else "",
    }


def write(path, key_names, table):
    cols = key_names + list(next(iter(table.values())).keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for k, v in table.items():
            w.writerow(list(k) + list(v.values()))


def main():
    scores = load()
    by_cond, by_model = {}, {}
    for m in MODELS:
        by_model[(m,)] = summarise([r for r in scores if r["model"] == m])
        for lang, corpus in CONDITIONS:
            rows = [r for r in scores if r["model"] == m and r["language"] == lang and r["corpus"] == corpus]
            by_cond[(m, lang, corpus)] = summarise(rows)
    write(ROOT / "results" / "summary_by_model_language.csv", ["model", "question_language", "articles_searched"], by_cond)
    write(ROOT / "results" / "summary_by_model.csv", ["model"], by_model)
    for k, v in by_model.items():
        print(k[0], v)


if __name__ == "__main__":
    main()
