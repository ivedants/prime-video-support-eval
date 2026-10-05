"""
extract_articles.py — turn saved Prime Video help pages (Safari "Page Source" HTML)
into clean text records.

Input layout (kept local, git-ignored):
    <raw_dir>/<Category>/<Article folder>/<one .html per language>
Output:
    data/articles/<nodeId>_<lang>.txt   clean article text (git-ignored)
    data/articles_index.csv             one row per file: id, nodeId, lang, title, url, category, chars

Only pages whose canonical URL is on primevideo.com/help are kept; anything else
(e.g. a linked Apple Support page) is reported and skipped.
"""
import csv, re, sys
from pathlib import Path
from bs4 import BeautifulSoup

SKIP_DIRS = {"outputs"}
GENERIC_H1 = {"Help", "मदद"}

def extract(path: Path):
    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    canon = soup.find("link", rel="canonical")
    url = canon["href"] if canon else ""
    # Localized pages sometimes use /-/hi/help?nodeId=... as the canonical URL.
    m = re.search(r"primevideo\.com/(?:-/[a-z]{2}/)?help\?nodeId=([A-Za-z0-9]+)", url)
    if not m:
        return None, f"not a Prime Video help page (canonical={url or 'none'})"
    lang = (soup.html.get("lang") or "").split("-")[0].lower()
    for t in soup(["script", "style", "noscript"]):
        t.decompose()
    # The article title is the h1 that isn't the generic "Help" heading.
    h1 = next((h for h in soup.find_all("h1") if h.get_text(strip=True) not in GENERIC_H1), None)
    if h1 is None:
        return None, "no article heading found"
    title = h1.get_text(" ", strip=True)
    # Walk up from the title until the container holds the article body
    # but not the help-topics sidebar.
    # Mark block-level elements with newlines so paragraphs survive, while inline
    # tags (bold, links) stay inside their sentence.
    for b in soup.find_all(["p", "li", "div", "h1", "h2", "h3", "h4", "br", "tr"]):
        b.insert_after("\n")
    node, body = h1, ""
    while node.parent is not None:
        node = node.parent
        text = node.get_text(" ")
        if "See All Help topics" in text or "मदद के सभी विषय देखें" in text:
            break
        body = text
    body = re.sub(r"[ \t\r\f\v]+", " ", body)
    body = re.sub(r" *\n[ \n]*", "\n", body).strip()
    body = re.sub(r" ([.,:;!?])", r"\1", body)
    if body.startswith(title):          # drop the duplicated heading
        body = body[len(title):].strip()
    return dict(nodeId=m.group(1), lang=lang, title=title, url=url, body=body), None

def main(raw_dir, out_dir):
    raw, out = Path(raw_dir), Path(out_dir)
    (out / "articles").mkdir(parents=True, exist_ok=True)
    rows, problems = [], []
    for f in sorted(raw.rglob("*.html")):
        rel = f.relative_to(raw).parts
        if rel[0] in SKIP_DIRS:
            continue
        rec, err = extract(f)
        if err:
            problems.append((str(f.relative_to(raw)), err)); continue
        rec["category"] = rel[0] if len(rel) > 1 else ""
        rec["source_file"] = str(f.relative_to(raw))
        aid = f"{rec['nodeId']}_{rec['lang']}"
        if any(r["id"] == aid for r in rows):
            problems.append((str(f.relative_to(raw)), f"duplicate of {aid}, skipped")); continue
        (out / "articles" / f"{aid}.txt").write_text(rec["title"] + "\n\n" + rec["body"], encoding="utf-8")
        rows.append(dict(id=aid, nodeId=rec["nodeId"], lang=rec["lang"], title=rec["title"], url=rec["url"],
                         category=rec["category"], chars=len(rec["body"]), source_file=rec["source_file"]))
    with open(out / "articles_index.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"kept {len(rows)} pages")
    for p in problems: print("SKIPPED:", *p)
    langs = {}
    for r in rows: langs.setdefault(r["nodeId"], set()).add(r["lang"])
    for n, l in langs.items():
        if l != {"en", "hi"}: print("UNPAIRED:", n, sorted(l))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
