"""実験ログから図と要約を生成する。
使い方: .venv/bin/python tools/analyze.py experiments/EXP-001_会話あり_seed1 [...]
出力: 各実験dirに timeline.png、複数指定時は experiments/comparison.png と summary
日本語フォント: macOSのHiragino系を使用。"""
import json
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

plt.rcParams["font.family"] = ["Hiragino Sans", "Hiragino Kaku Gothic ProN", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False
BG, PANEL, FG, DIM = "#12151c", "#191d26", "#ECECEC", "#8a8f98"
plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": PANEL,
    "axes.edgecolor": "#333a46", "axes.labelcolor": FG, "text.color": FG,
    "xtick.color": DIM, "ytick.color": DIM, "font.size": 13})


def load(exp_dir):
    d = pathlib.Path(exp_dir)
    events = [json.loads(l) for l in open(d / "logs" / "events.jsonl")]
    metrics = json.loads((d / "logs" / "metrics.json").read_text())
    return d, events, metrics


def timeline(exp_dir):
    d, events, metrics = load(exp_dir)
    agents = sorted({e["agent"] for e in events})
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6.4), sharex=True,
                                   gridspec_kw={"height_ratios": [1, 1.4]})
    # 上段: 行動ラスタ（■=A）
    for i, name in enumerate(agents):
        xs = [e["turn"] for e in events if e["agent"] == name and e["action"] == "A"]
        ax1.scatter(xs, [i] * len(xs), marker="s", s=48)
    ax1.set_yticks(range(len(agents)), agents)
    ax1.set_title(f"{d.name}", fontsize=15)
    ax1.grid(axis="x", alpha=0.3)
    # 下段: エネルギー
    for name in agents:
        pts = [(e["turn"], e["energy"]) for e in events if e["agent"] == name]
        ax2.plot(*zip(*pts), label=name, linewidth=1.6)
    ax2.set_xlabel("ターン"); ax2.set_ylabel("エネルギー")
    ax2.legend(ncol=6, fontsize=10, facecolor="#191d26", labelcolor="#ECECEC", edgecolor="#333a46"); ax2.grid(alpha=0.3)
    fig.tight_layout()
    out = d / "timeline.png"
    fig.savefig(out, dpi=140); plt.close(fig)
    print(f"{out}  定着率={metrics['adoption_rate']}  A率={metrics['per_agent_A_rate']}")


def comparison(exp_dirs):
    rows = []
    for e in exp_dirs:
        d, _, m = load(e)
        comm = "会話あり" if "会話あり" in d.name else ("会話なし" if "会話なし" in d.name else d.name)
        rows.append((d.name, comm, m["adoption_rate"]))
    fig, ax = plt.subplots(figsize=(8, 4.2))
    colors = {"会話あり": "#2B6CB0", "会話なし": "#B03A2E"}
    ax.bar([r[0].split("_")[0] + "\n" + r[1] for r in rows], [r[2] for r in rows],
           color=[colors.get(r[1], "#777") for r in rows])
    ax.set_ylabel("定着率（最終1/3でA実行率≥70%の住人の割合）")
    ax.set_ylim(0, 1.05); ax.grid(axis="y", alpha=0.25)
    ax.set_title("会話チャネルの有無と定着率")
    fig.tight_layout()
    out = pathlib.Path("experiments/comparison.png")
    fig.savefig(out, dpi=140); plt.close(fig)
    print(out)


if __name__ == "__main__":
    dirs = sys.argv[1:]
    for e in dirs:
        timeline(e)
    if len(dirs) > 1:
        comparison(dirs)
