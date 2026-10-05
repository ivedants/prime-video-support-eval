"""
bedrock.py: thin wrappers around the two Bedrock calls this project makes:
  embed(text)            -> Titan Text Embeddings V2 (InvokeModel)
  converse(model, ...)   -> Converse API, returning text, tokens and latency

Set MOCK=1 in the environment to run the whole pipeline without AWS (fake
embeddings and canned answers). That is how the code was tested before any
paid call; mock results are written to separate files and never mixed with
real ones.
"""
import hashlib, json, os, random, time

import numpy as np

import config

MOCK = os.environ.get("MOCK") == "1"
_runtime = None


def _client():
    global _runtime
    if _runtime is None:
        import boto3
        from botocore.config import Config
        session = boto3.Session(profile_name=os.environ.get("AWS_PROFILE", config.AWS_PROFILE),
                                region_name=config.AWS_REGION)
        _runtime = session.client("bedrock-runtime",
                                  config=Config(retries={"max_attempts": 8, "mode": "adaptive"},
                                                read_timeout=120))
    return _runtime


def embed(text: str):
    """Return (unit-length vector, input token count)."""
    if MOCK:
        seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        v = np.random.default_rng(seed).normal(size=config.EMBED_DIMENSIONS)
        return v / np.linalg.norm(v), max(1, len(text) // 4)
    body = json.dumps({"inputText": text, "dimensions": config.EMBED_DIMENSIONS, "normalize": True})
    resp = _client().invoke_model(modelId=config.EMBED_MODEL_ID, body=body)
    out = json.loads(resp["body"].read())
    return np.array(out["embedding"], dtype=np.float32), out["inputTextTokenCount"]


def converse(model_label: str, system: str, user: str) -> dict:
    """One Converse call. Returns answer text, token counts, latency and cost."""
    m = config.MODELS[model_label]
    if MOCK:
        time.sleep(0.01)
        tin, tout = len(system + user) // 4, random.randint(80, 300)
        text = f"[mock answer from {model_label}]"
        latency = random.randint(400, 3000)
        stop = "end_turn"
    else:
        kwargs = dict(modelId=m["model_id"],
                      system=[{"text": system}],
                      messages=[{"role": "user", "content": [{"text": user}]}],
                      inferenceConfig=config.INFERENCE_CONFIG)
        if m["extra"]:
            kwargs["additionalModelRequestFields"] = m["extra"]
        t0 = time.perf_counter()
        resp = _client().converse(**kwargs)
        wall = int((time.perf_counter() - t0) * 1000)
        # Keep only text blocks (a reasoning block would mean thinking was on).
        blocks = resp["output"]["message"]["content"]
        text = "".join(b.get("text", "") for b in blocks)
        if any("reasoningContent" in b for b in blocks):
            text = "[WARNING: reasoning block returned]\n" + text
        tin, tout = resp["usage"]["inputTokens"], resp["usage"]["outputTokens"]
        latency = resp.get("metrics", {}).get("latencyMs", wall)
        stop = resp.get("stopReason", "")
    cost = tin / 1e6 * m["price_in"] + tout / 1e6 * m["price_out"]
    return dict(answer=text, input_tokens=tin, output_tokens=tout,
                latency_ms=latency, stop_reason=stop, est_cost_usd=round(cost, 6))
