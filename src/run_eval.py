"""
run_eval.py: send each question, with its retrieved excerpts, to each model
through the Bedrock Converse API and record the result.

    python src/run_eval.py --qids EN-B01,EN-U02,HI-B05,HI-D02,HG-DL01        # estimate the 5-question test
    python src/run_eval.py --qids EN-B01,EN-U02,HI-B05,HI-D02,HG-DL01 --yes  # run it
    python src/run_eval.py --yes                     # full run

Every model gets the identical system prompt and the identical excerpts for a
given (question, corpus) pair, so differences come from the models alone.

Results are appended to results/raw_answers.jsonl, one line per answer. Rerunning
skips anything already recorded, so an interrupted run can simply be restarted.
--qids picks exact questions; --limit N takes the first N English pair_ids and includes their Hindi and
Hinglish versions, so a small test still covers every language.
"""
import argparse, csv, json, sys, time
from pathlib import Path

import bedrock, config
from retrieve import Index, format_context

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results" / ("raw_answers_mock.jsonl" if bedrock.MOCK else "raw_answers.jsonl")


def plan_jobs(questions, limit, models):
    if limit:
        keep = []
        for q in questions:
            if q["language"] == "en" and q["pair_id"] not in keep:
                keep.append(q["pair_id"])
        keep = set(keep[:limit])
        questions = [q for q in questions if q["pair_id"] in keep]
    return [(q, corpus, m) for q in questions for corpus in config.CONDITIONS[q["language"]] for m in models]


def estimate(jobs, idx):
    """Estimate cost from the actual prompts.
    Tokens: ~4 chars/token for Latin text, ~1 char/token for Devanagari. The
    Devanagari figure comes from the real embedding run (Titan counted about
    1.1 tokens per Devanagari character); each model tokenizes differently, so
    this is a guide, not a quote.
    Output: 350 tokens typical for English/Hinglish answers, 600 for Hindi;
    the high case assumes every answer hits the maxTokens limit."""
    def toks(s):
        dev = sum('\u0900' <= ch <= '\u097f' for ch in s)
        return dev / 1.0 + (len(s) - dev) / 4
    cap = config.INFERENCE_CONFIG["maxTokens"]
    typ = high = 0.0
    for q, corpus, m in jobs:
        prompt = config.SYSTEM_PROMPT + format_context(idx.search(q["qid"], corpus)) + q["question"]
        p = config.MODELS[m]; tin = toks(prompt)
        out_typ = 600 if q["language"] == "hi" else 350
        typ += tin / 1e6 * p["price_in"] + out_typ / 1e6 * p["price_out"]
        high += tin * 1.3 / 1e6 * p["price_in"] + cap / 1e6 * p["price_out"]
    return typ, high


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="only the first N question pairs")
    ap.add_argument("--qids", default="", help="comma-separated question IDs (overrides --limit)")
    ap.add_argument("--models", default=",".join(config.MODELS), help="comma-separated model labels")
    ap.add_argument("--yes", action="store_true", help="make the paid Bedrock calls")
    args = ap.parse_args()
    models = args.models.split(",")

    idx = Index()
    questions = list(csv.DictReader(open(ROOT / "data" / "questions.csv", encoding="utf-8-sig")))
    if args.qids:
        wanted = set(args.qids.split(","))
        questions = [q for q in questions if q["qid"] in wanted]
        missing = wanted - {q["qid"] for q in questions}
        if missing: sys.exit(f"Unknown question IDs: {sorted(missing)}")
    jobs = plan_jobs(questions, args.limit, models)
    done = set()
    if RESULTS.exists():
        # Keep successful answers; drop failed calls so they are retried.
        kept = [json.loads(line) for line in open(RESULTS, encoding="utf-8")]
        good = [r for r in kept if not r.get("error")]
        if len(good) != len(kept):
            print(f"Removing {len(kept)-len(good)} failed calls from earlier runs; they will be retried.")
            with open(RESULTS, "w", encoding="utf-8") as f:
                for r in good:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
        done = {(r["qid"], r["corpus"], r["model"]) for r in good}
    todo = [j for j in jobs if (j[0]["qid"], j[1], j[2]) not in done]
    typ, high = estimate(todo, idx)
    print(f"{len(jobs)} answers planned, {len(jobs)-len(todo)} already done, {len(todo)} to run")
    print(f"Estimated cost: ~${typ:.2f} typical, ~${high:.2f} high case")
    if not (args.yes or bedrock.MOCK):
        print("Dry run only. Re-run with --yes to call Bedrock.")
        sys.exit(0)

    RESULTS.parent.mkdir(exist_ok=True)
    spent = 0.0
    with open(RESULTS, "a", encoding="utf-8") as out:
        for i, (q, corpus, m) in enumerate(todo, 1):
            hits = idx.search(q["qid"], corpus)
            user = config.USER_TEMPLATE.format(context=format_context(hits), question=q["question"])
            try:
                r = bedrock.converse(m, config.SYSTEM_PROMPT, user)
            except Exception as e:                      # record the failure and keep going
                r = dict(answer="", input_tokens=0, output_tokens=0, latency_ms=None,
                         stop_reason="", est_cost_usd=0.0, error=f"{type(e).__name__}: {e}")
            expected = {a for a in q["expected_article_id"].split(";") if a}
            got = [h["article_id"] for h in hits]
            rec = dict(model=m, model_id=config.MODELS[m]["model_id"], prompt_version=config.PROMPT_VERSION, qid=q["qid"], pair_id=q["pair_id"],
                       language=q["language"], corpus=corpus, category=q["category"],
                       answerable=q["answerable"], expected_article_ids=sorted(expected),
                       retrieved_article_ids=got, retrieved_chunk_ids=[h["chunk_id"] for h in hits],
                       retrieval_hit=(bool(expected & set(got)) if expected else None),
                       question=q["question"], **r,
                       timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"))
            out.write(json.dumps(rec, ensure_ascii=False) + "\n"); out.flush()
            spent += r["est_cost_usd"]
            flag = f" ERROR: {r['error'][:140]}" if r.get("error") else ""
            print(f"[{i}/{len(todo)}] {m:16} {q['qid']:9} {corpus:4} "
                  f"{r['input_tokens']:>5}in {r['output_tokens']:>4}out {r['latency_ms']}ms  total ${spent:.3f}{flag}")
    print(f"Done. Estimated spend this run: ${spent:.3f}. Results: {RESULTS}")


if __name__ == "__main__":
    main()
