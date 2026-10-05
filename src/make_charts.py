"""Draw the three result charts into results/charts/ from results/scores.csv."""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "charts"
MODELS = [("haiku-4.5", "Claude Haiku 4.5"), ("llama4-maverick", "Llama 4 Maverick"), ("nova2-lite", "Nova 2 Lite")]
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
SEQ = {2: "#1f5fae", 1: "#7fb0ea", 0: "#d5e4f7"}  # one hue, dark = full marks

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": INK, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
                     "savefig.facecolor": SURFACE})


def rows():
    return list(csv.DictReader(open(ROOT / "results" / "scores.csv", encoding="utf-8")))


def clean(ax):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(length=0)


def title(fig, head, sub):
    fig.text(0.02, 0.965, head, fontsize=13, fontweight="bold", va="top")
    fig.text(0.02, 0.905, sub, fontsize=9.5, color=INK2, va="top")


def chart_correctness(R):
    types = [("yes", "Answerable"), ("partial", "Partly answerable"), ("no", "Not answerable")]
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.6), sharey=True)
    for ax, (t, label) in zip(axes, types):
        for i, (m, name) in enumerate(MODELS):
            rs = [r for r in R if r["model"] == m and r["answerable"] == t]
            n, left = len(rs), 0
            for score in (2, 1, 0):
                c = sum(int(r["correctness"]) == score for r in rs)
                w = 100 * c / n
                ax.barh(i, w, left=left, color=SEQ[score], edgecolor=SURFACE, linewidth=2, height=0.62)
                if w >= 7:
                    ax.text(left + w / 2, i, str(c), ha="center", va="center", fontsize=9,
                            color="white" if score == 2 else INK)
                left += w
        ax.set_title(f"{label} (n = {n} per model)", fontsize=10, loc="left", color=INK)
        ax.set_xlim(0, 100)
        ax.set_xticks([0, 50, 100])
        ax.set_xticklabels(["0%", "50%", "100%"])
        ax.set_yticks(range(3))
        ax.set_yticklabels([n for _, n in MODELS])
        clean(ax)
    axes[0].invert_yaxis()
    handles = [plt.Rectangle((0, 0), 1, 1, color=SEQ[s]) for s in (2, 1, 0)]
    fig.legend(handles, ["2 = full marks", "1 = partly right", "0 = wrong or no usable answer"], loc="lower left",
               bbox_to_anchor=(0.02, 0.0), ncol=3, frameon=False, fontsize=9)
    title(fig, "Correctness is a tie on answerable questions; partly answerable questions are the weak spot",
          "Share of answers by correctness score. Numbers in bars are answer counts. All languages combined.")
    fig.subplots_adjust(top=0.74, bottom=0.2, left=0.13, right=0.97, wspace=0.16)
    fig.savefig(OUT / "1_correctness_by_question_type.png", dpi=160)
    plt.close(fig)


def chart_hindi_corpus(R):
    conds = [("en", "English articles", BLUE), ("hi", "Hindi articles", ORANGE), ("both", "Both", AQUA)]
    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    w = 0.24
    for j, (c, label, color) in enumerate(conds):
        for i, (m, _) in enumerate(MODELS):
            rs = [r for r in R if r["model"] == m and r["language"] == "hi" and r["corpus"] == c]
            v = sum(int(r["correctness"]) == 2 for r in rs)
            x = i + (j - 1) * (w + 0.02)
            ax.bar(x, v, width=w, color=color, label=label if i == 0 else None)
            ax.text(x, v + 0.5, str(v), ha="center", va="bottom", fontsize=9, color=INK)
    ax.set_xticks(range(3))
    ax.set_xticklabels([n for _, n in MODELS])
    ax.set_ylim(0, 30)
    ax.set_yticks([0, 10, 20, 30])
    ax.set_ylabel("Answers with full marks (of 30)")
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    clean(ax)
    ax.legend(title="Help articles searched", loc="lower left", bbox_to_anchor=(0, -0.3), ncol=3, frameon=False,
              fontsize=9, title_fontsize=9, alignment="left")
    title(fig, "Hindi questions scored higher when the search ran over English articles",
          "30 Hindi questions per model, same questions in each condition. Answers were still written in Hindi.")
    fig.subplots_adjust(top=0.8, bottom=0.24, left=0.09, right=0.98)
    fig.savefig(OUT / "2_hindi_questions_by_articles_searched.png", dpi=160)
    plt.close(fig)


def chart_problems(R):
    panels = [("made_up", "y", "Answers with made-up content"), ("lang_match", "n", "Answers in the wrong language or script")]
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.3), sharey=True)
    for ax, (col, bad, label) in zip(axes, panels):
        for i, (m, _) in enumerate(MODELS):
            v = sum(r[col] == bad for r in R if r["model"] == m)
            ax.barh(i, v, color=BLUE, height=0.55)
            ax.text(v + 0.6, i, str(v), va="center", fontsize=9.5, color=INK)
        ax.set_title(label, fontsize=10, loc="left", color=INK)
        ax.set_xlim(0, 40)
        ax.set_xticks([0, 10, 20, 30, 40])
        ax.set_yticks(range(3))
        ax.set_yticklabels([n for _, n in MODELS])
        ax.xaxis.grid(True, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        clean(ax)
    axes[0].invert_yaxis()
    title(fig, "The models differ on made-up content and on replying in the customer's language",
          "Count of answers out of 150 per model (LLM-judge scoring). Lower is better.")
    fig.subplots_adjust(top=0.7, bottom=0.1, left=0.15, right=0.97, wspace=0.1)
    fig.savefig(OUT / "3_made_up_and_wrong_language.png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    R = rows()
    chart_correctness(R)
    chart_hindi_corpus(R)
    chart_problems(R)
    print("wrote", sorted(p.name for p in OUT.glob("*.png")))
