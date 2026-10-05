"""
config.py: every setting that affects results lives here, so a run can be
reproduced exactly and the README can quote it.

Prices are USD per 1M tokens, read from https://aws.amazon.com/bedrock/pricing/
on 2026-10-01 (US geographic cross-region inference). Nova 2 Lite's geo price
was not shown on the page; it is assumed to be 10% above its global price,
matching the Anthropic pattern on the same page. Recheck before a paid run.
"""

AWS_REGION = "us-east-1"          # where we call from; geo profiles route within the US
AWS_PROFILE = "pv-eval"           # local AWS CLI profile (see SETUP_AWS.md); never committed

# ---- Embeddings / retrieval -------------------------------------------------
EMBED_MODEL_ID = "amazon.titan-embed-text-v2:0"
EMBED_DIMENSIONS = 1024
EMBED_PRICE_PER_M = 0.02
CHUNK_MAX_CHARS = 1200            # paragraphs are packed into chunks up to this size
TOP_K = 3

# ---- Generation models ------------------------------------------------------
# label: short name used in files and charts
# extra: model-specific request fields. Sonnet 5.5 thinks by default, so we
# turn thinking off to match the other two (Nova 2 Lite's reasoning is off by
# default; we set it explicitly anyway so the setting is on record).
MODELS = {
    "sonnet-5.5": {
        "model_id": "us.anthropic.claude-sonnet-5-5",
        "price_in": 2.20, "price_out": 11.00,
        "extra": {"thinking": {"type": "disabled"}},
    },
    # Added 2026-10-02: Sonnet 5.5 returned "not available for this account" on a
    # new AWS account. Haiku 4.5 is Anthropic's low-cost tier, closer in price to
    # the other two models. Extended thinking is off unless requested.
    "haiku-4.5": {
        "model_id": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
        "price_in": 1.10, "price_out": 5.50,
        "extra": None,
    },
    "llama4-maverick": {
        "model_id": "us.meta.llama4-maverick-17b-instruct-v1:0",
        "price_in": 0.24, "price_out": 0.97,
        "extra": None,
    },
    "nova2-lite": {
        "model_id": "us.amazon.nova-2-lite-v1:0",
        "price_in": 0.33, "price_out": 2.75,   # assumed geo price, see note above
        "extra": {"reasoningConfig": {"type": "disabled"}},
    },
}

# maxTokens 1200: Devanagari costs roughly one token per character, so 800 could
# cut off a Hindi answer mid-sentence. stop_reason is logged to catch truncation.
INFERENCE_CONFIG = {"temperature": 0.0, "maxTokens": 1200}

# ---- Retrieval conditions ---------------------------------------------------
# Which article corpus each question language is searched against.
#   en  = English articles only, hi = Hindi articles only, both = all articles
CONDITIONS = {
    "en": ["en"],
    "hi": ["en", "hi", "both"],
    "hinglish": ["en", "hi", "both"],
}

# ---- System prompt (identical for every model) -----------------------------
# v1: original prompt, used only for the first 5-question test (2026-10-02).
# v2: after that test, rule 4 was tightened (answer in the question's language,
#     not the excerpts') and rule 6 was added (don't mention excerpts). All
#     reported results use v2.
PROMPT_VERSION = "v2"
SYSTEM_PROMPT = """You are a customer support assistant for Prime Video.

Rules:
1. Answer ONLY using the help-center excerpts provided in the user message. Do not use outside knowledge about Prime Video, Amazon, devices, prices, or policies.
2. If the excerpts do not contain the answer, say clearly that you don't have that information and suggest the customer contact Prime Video customer support. Do not guess.
3. If the excerpts answer only part of the question, answer that part and say plainly which part you can't answer.
4. Reply in the language and script of the customer's question, not the language of the excerpts. If they wrote in English, reply in English. If they wrote in Hindi (Devanagari), reply in Hindi. If they wrote Hindi in Latin letters (Hinglish), reply in Hinglish. Product names such as Prime Video can stay in English.
5. Be brief and practical: short steps the customer can follow.
6. Don't mention "excerpts" or their numbers. The customer can't see them."""

USER_TEMPLATE = """Help-center excerpts:
{context}

Customer question:
{question}"""
