"""スライド用の特製図版：一般視聴者向けタイトル・伝播図。"""
import json, pathlib
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
BG, PANEL, FG, DIM = "#12151c", "#191d26", "#ECECEC", "#9aa0aa"
ACC = "#C5A059"
AG = ["#5B9BD5", "#ED7D31", "#70AD47", "#B39DDB", "#E85D75", "#4DB6AC"]
AGENTS = ["ハル", "ミナ", "ケイ", "サト", "ユキ", "リン"]
plt.rcParams.update({"font.family": ["Hiragino Sans"], "figure.facecolor": BG,
    "axes.facecolor": PANEL, "axes.edgecolor": "#333a46", "text.color": FG,
    "axes.labelcolor": FG, "xtick.color": DIM, "ytick.color": DIM, "font.size": 13})

def village(exp, title, out):
    d = pathlib.Path(exp) / "logs"
    ev = [json.loads(l) for l in open(d/"events.jsonl", encoding="utf-8", errors="replace")]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6.4), sharex=True,
                                   gridspec_kw={"height_ratios": [1, 1.3]})
    for i, name in enumerate(AGENTS):
        xs = [e["turn"] for e in ev if e["agent"] == name and e["action"] == "A"]
        ax1.scatter(xs, [i]*len(xs), marker="s", s=52, color=AG[i])
        pts = [(e["turn"], e["energy"]) for e in ev if e["agent"] == name]
        ax2.plot(*zip(*pts), color=AG[i], linewidth=1.8, label=name)
    ax1.set_yticks(range(6), AGENTS); ax1.set_xlim(0.5, 30.5); ax1.set_ylim(-0.7, 5.7)
    ax1.set_title(title, fontsize=16, pad=10)
    ax2.set_xlim(0.5, 30.5); ax2.set_ylim(0, 21)
    ax2.set_xlabel("日（ターン）"); ax2.set_ylabel("体力")
    ax2.legend(ncol=6, fontsize=11, facecolor=BG, labelcolor=FG, edgecolor="#333a46",
               loc="upper center", bbox_to_anchor=(0.5, -0.22))
    for ax in (ax1, ax2):
        for sp in ax.spines.values(): sp.set_color("#333a46")
        ax.grid(alpha=0.2)
    fig.tight_layout(); fig.subplots_adjust(bottom=0.17); fig.savefig(out, dpi=140); plt.close(fig)
    print(out)

village("experiments/EXP-001_会話あり_seed1", "チャットのある村（村1）の30日間", "deliverables/figs/village_chat.png")
village("experiments/EXP-004_会話なし_seed1", "チャットのない村（村1）の30日間", "deliverables/figs/village_quiet.png")

# --- 伝播図：「20説」が村の共通語になるまで（EXP-002 実データ） ---
first = {"ハル":16, "ユキ":16, "サト":17, "ミナ":18, "リン":18}
fig, ax = plt.subplots(figsize=(9.5, 4.6))
ax.set_xlim(14.4, 20.6); ax.set_ylim(-0.7, 5.7)
ax.set_yticks(range(6), AGENTS)
ax.set_xticks(range(15, 21), [f"{t}日目" for t in range(15, 21)])
for i, name in enumerate(AGENTS):
    if name in first:
        t = first[name]
        star = (t == 16 and name in ("ハル","ユキ"))
        ax.scatter([t], [i], s=700 if star else 420, marker="*" if star else "o",
                   color=AG[i], zorder=3, edgecolors=FG, linewidths=1.2)
        if name not in ("ハル","ユキ"):
            ax.annotate("", xy=(t-0.12, i), xytext=(16.12, AGENTS.index("ハル")),
                        arrowprops=dict(arrowstyle="->", color=DIM, lw=1.6, alpha=0.85))
    else:
        ax.text(20.4, i, "（使わず）", ha="right", va="center", color=DIM, fontsize=12)
ax.text(17.5, -0.55, "★＝16日目、ほぼ同時に言い出した2人（ハル・ユキ）　●＝その名前を使い始めた日", color=ACC, fontsize=11.5, ha="center")
ax.text(18.5, 5.35, "→ 2日後には6人中5人の共通語に", color=FG, fontsize=13, weight="bold")
ax.set_title("ある発見の名前が、村の共通語になるまで（村2「20説」・実データ）", fontsize=15, pad=10)
for sp in ax.spines.values(): sp.set_color("#333a46")
ax.grid(axis="x", alpha=0.2)
fig.tight_layout(); fig.savefig("deliverables/figs/propagation.png", dpi=140); plt.close(fig)
print("deliverables/figs/propagation.png")
