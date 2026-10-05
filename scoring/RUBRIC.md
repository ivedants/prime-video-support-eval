# Scoring rubric (fixed before scoring began, 2 October 2026)

Scorer sees: the question, its answerable label and note, the excerpts the model was given, and the answer. Scorer does not see which model wrote the answer. Identical answers to the same question with the same excerpts are scored once.

**correctness** (judged against what the saved help articles say, as given in the question notes)
- answerable: 2 = key facts correct and complete enough to act on; 1 = partly right, or right but missing a key fact, or buried in irrelevant material; 0 = wrong, or no usable answer (including when search returned the wrong article and the model declined)
- partial: 2 = answers the covered part correctly and says what it can't answer; 1 = answers the covered part but doesn't flag the gap, or flags the gap but misses the covered part; 0 = wrong or fills the gap with invented detail
- unanswerable: 2 = clearly says it doesn't have the information and points to support; 1 = declines but adds speculation or off-topic material; 0 = answers anyway

**made_up** (yes/no): states any factual claim the excerpts given to it don't support. Outside knowledge counts as made up even if true (e.g. naming a TV's app store). "Contact support" and restating the question don't count. Supported-but-irrelevant content is not made up (it lowers correctness instead).

**abstained** (yes/no): unanswerable questions — did it say it doesn't know. Partial questions — did it say which part it can't answer. Answerable questions — left blank.

**lang_match** (yes/no): reply is in the question's language and script (English → English; Hindi → Devanagari; Hinglish → Hindi in Latin letters). English product/tech words inside Hindi are fine. This is a mechanical check; fluency is scored separately by a native speaker; see RUBRIC_LQ.md.

**reason**: one line.
