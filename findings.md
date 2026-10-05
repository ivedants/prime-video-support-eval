# A Hindi and English support assistant for Prime Video: what a small evaluation shows

Vedant Shrivastava · October 2026 · Version 1

## Problem

A support assistant that answers from help-center articles has to do three things for a customer in India: give the right answer, avoid inventing one, and reply in the customer's own language. I wanted to know how well current models on Amazon Bedrock do this in English, Hindi and Hinglish (Hindi typed in Latin letters), and what a team would need to fix before piloting one.

## Method

- **Content.** 35 public Prime Video help articles, each in English and Hindi, saved by hand on 1 October 2026. The source is the public Prime Video Help Center (https://www.primevideo.com/help). I saved the pages by hand in a browser, with no automated collection. Article text is not in this repository; `data/sources.csv` links to each page.
- **Questions.** 70 customer-style questions: 30 English, the same 30 in Hindi, and 10 in Hinglish. Of each 30, 16 can be answered from the articles, 5 only in part, and 9 not at all.
- **Assistant.** For each question, a local search picks the 3 closest article passages (Titan Text Embeddings V2). Each model gets the same passages and the same instructions: answer only from the passages, in the customer's language, and say so when the answer isn't there.
- **Models.** Claude Haiku 4.5, Llama 4 Maverick and Nova 2 Lite, 150 answers each.
- **Search conditions.** Hindi and Hinglish questions were run three times: against English articles, Hindi articles, and both.
- **Scoring.** I set a rubric with four measures: correctness (0–2), made-up content, declining when it should, and replying in the right language. An LLM judge (Claude) applied it to all 450 answers without seeing which model wrote each one, and gave a one-line reason for every score. I checked the judge on a sample of 30 English answers, and scored Hindi and Hinglish language quality myself on 89 answers, since that needs a native reader.

## Findings

Charts for findings 1, 2 and 5 are in `results/charts/`; the full table is `results/summary_by_model_language.csv`.

**1. Correctness does not separate the models.** On questions the articles can answer, the models got full marks on 70, 68 and 70 of 82. Across all 450 answers the figures are 110, 109 and 104 of 150. Differences this small are within noise for a test of this size.

**2. Hindi questions did better when the search ran over English articles.** For Hindi questions the articles can answer, 47 of 48 answers got full marks with English articles, against 35 of 48 with Hindi articles and 40 of 48 with both. The cause is search, not writing: search found the right article for all 21 Hindi questions against English articles, but for 18 of 21 against Hindi articles. The answers were still written in Hindi.

**3. A missed search is rarely recovered.** In the 18 cases where search missed the right article, no answer got full marks and 9 contained made-up content.

**4. Partly answerable questions are the weak spot for every model.** When the articles covered only part of a question, the models usually answered that part and did not say what was missing. Full marks: 8, 8 and 1 of 26.

**5. The models differ on made-up content and on language.**

| | Claude Haiku 4.5 | Llama 4 Maverick | Nova 2 Lite |
|---|---|---|---|
| Answers with made-up content (of 150) | 14 | 7 | 22 |
| Answers in the wrong language or script (of 150) | 16 | 5 | 33 |
| Hindi answers I rated natural (of 22) | 17 | 7 | 11 |
| Median response time | 2.2 s | 0.6 s | 1.3 s |
| Estimated cost per 1,000 questions | $2.99 | $0.34 | $0.86 |

Nova 2 Lite answered 11 of 30 English questions in Hindi or Hinglish. All three models tended to reply in Devanagari to Hinglish questions when the passages were in Hindi (20 of 30 answers).

**6. Hindi quality is where a native reader disagrees with the numbers.** Llama 4 Maverick had the fewest errors but its Hindi often read as stiff or over-formal; I rated 7 of 22 answers natural, against 17 of 22 for Haiku. Hinglish pointed the other way (Llama 5 of 8, Haiku 1 of 8), but 8 answers per model is too few to rely on.

**7. An automated judge was not a usable substitute for a Hindi reader.** I tested whether the LLM judge could also score Hindi language quality, calibrating it on 16 of my scores. On the next 73 it matched me 41 times (56%). It was stricter than I was, and it widened the lead of the Claude model over the other two.

## Recommendations

1. **Search English articles for Hindi questions until Hindi search is fixed.** In this test it gave more correct Hindi answers than searching Hindi articles. Measure Hindi search on its own before relying on it.
2. **Choose the model on fidelity, language and cost, not on correctness.** Llama 4 Maverick was the cheapest and fastest, with the fewest made-up answers and language errors. Claude Haiku 4.5 wrote the most natural Hindi at about nine times the cost. Which matters more is a product decision; this test does not settle it.
3. **Check the reply language in code.** A simple script check on the output would have caught the 54 wrong-language answers before a customer saw them.
4. **Treat "partly answerable" as its own test case.** It needs a prompt or product change, and a metric of its own; overall correctness hides it.
5. **Decline when search confidence is low.** Missed searches produced half of their answers with made-up content.
6. **Keep a native speaker in the loop for Hindi quality.** Use automated scoring there only after checking it against human scores.

## Limitations

- **Small test.** 70 questions and 35 articles. A difference of one or two answers between models means nothing; I have reported counts so the reader can judge.
- **Scoring.** Correctness scores come from the LLM judge. A second blind pass on 42 answers gave the same correctness score on 37. My check of 30 English answers was a read-through with the judge's scores visible, not independent re-scoring; I found no score I would change. Hindi and Hinglish correctness rests on the judge alone. The judge and Claude Haiku 4.5 are from the same model family; scoring was blind to model names, which reduces but does not remove that concern.
- **Language quality.** One rater (me), 89 answers, about 30 per model.
- **Model choice.** Claude Sonnet 5.5 was planned but was not available on my account, so Haiku 4.5 stands in. Results for a larger Claude model may differ.
- **One run.** Each question was run once per model at temperature 0.
- **Cost and speed.** Costs are estimates from token counts and list prices on 1 October 2026 (the Nova 2 Lite regional price is assumed). Response times were measured from one laptop in Los Angeles and are indicative only.
- **Content.** Pages were saved from the US. India-specific help pages were used where they exist. Help content changes; results describe the pages as saved.
- **Search check is lenient.** A search counts as a hit if the right article appears, even when the specific passage with the answer does not.

Total AWS spend for the project was about $0.64.
