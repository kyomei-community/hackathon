"""デモ動画の自動生成。実験ログ（実データ）をそのまま再生してMP4にする。
使い方: .venv/bin/python tools/make_video.py 出力.mp4
構成: タイトル → 世界のルール → EXP-001(会話あり)リプレイ → EXP-004(会話なし)リプレイ → 結果 → 換算
"""
import json
import pathlib
import sys
import textwrap

import imageio_ffmpeg
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter

plt.rcParams["font.family"] = ["Hiragino Sans", "sans-serif"]
plt.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()

BG, FG, ACC, DIM = "#12151c", "#ECECEC", "#C5A059", "#8a8f98"
AGENTS = ["ハル", "ミナ", "ケイ", "サト", "ユキ", "リン"]
COLORS = ["#5B9BD5", "#ED7D31", "#70AD47", "#B39DDB", "#E85D75", "#4DB6AC"]
FPS = 10


def load(exp):
    d = pathlib.Path(exp) / "logs"
    ev = [json.loads(l) for l in open(d / "events.jsonl", encoding="utf-8", errors="replace")]
    msgs = []
    if (d / "messages.jsonl").exists():
        msgs = [json.loads(l) for l in open(d / "messages.jsonl", encoding="utf-8", errors="replace")]
    return ev, msgs


def card(w, fig, lines, hold_s, title_size=34, body_size=19):
    fig.clf(); fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    y = 0.72
    for i, (txt, kind) in enumerate(lines):
        if kind == "t":
            ax.text(0.5, y, txt, color=FG, size=title_size, ha="center", weight="bold")
            y -= 0.14
        elif kind == "a":
            ax.text(0.5, y, txt, color=ACC, size=22, ha="center")
            y -= 0.1
        else:
            ax.text(0.5, y, txt, color=DIM if kind == "d" else FG, size=body_size, ha="center")
            y -= 0.075
    for _ in range(int(hold_s * FPS)):
        w.grab_frame()


def replay(w, fig, exp, label, sec_per_turn, show_chat):
    ev, msgs = load(exp)
    turns = max(e["turn"] for e in ev)
    for t in range(1, turns + 1):
        fig.clf(); fig.patch.set_facecolor(BG)
        fig.text(0.02, 0.955, label, color=ACC, size=20, weight="bold")
        fig.text(0.98, 0.955, f"ターン {t} / {turns}", color=FG, size=20, ha="right")
        if show_chat:
            axc = fig.add_axes([0.02, 0.04, 0.44, 0.86]); axc.axis("off")
            axc.set_facecolor(BG)
            recent = [m for m in msgs if m["turn"] <= t][-7:]
            y = 0.97
            for m in recent:
                ci = COLORS[AGENTS.index(m["agent"])]
                body = textwrap.fill(m["message"], 30)[:120]
                axc.text(0, y, f"t{m['turn']} {m['agent']}", color=ci, size=12, weight="bold",
                         va="top", transform=axc.transAxes)
                axc.text(0, y - 0.035, body, color=FG, size=11, va="top",
                         transform=axc.transAxes, linespacing=1.4)
                y -= 0.035 + 0.032 * (body.count("\n") + 1) + 0.025
            x0 = 0.52
        else:
            fig.text(0.02, 0.5, "（会話チャネルなし）\n各住人は自分の数値だけを見て判断する",
                     color=DIM, size=16, va="center")
            x0 = 0.35
        ax1 = fig.add_axes([x0, 0.56, 0.96 - x0, 0.34])
        ax2 = fig.add_axes([x0, 0.08, 0.96 - x0, 0.40])
        for ax in (ax1, ax2):
            ax.set_facecolor("#191d26")
            for sp in ax.spines.values():
                sp.set_color("#333")
            ax.tick_params(colors=DIM, labelsize=10)
        for i, name in enumerate(AGENTS):
            xs = [e["turn"] for e in ev if e["agent"] == name and e["action"] == "A" and e["turn"] <= t]
            ax1.scatter(xs, [i] * len(xs), marker="s", s=46, color=COLORS[i])
            pts = [(e["turn"], e["energy"]) for e in ev if e["agent"] == name and e["turn"] <= t]
            if pts:
                ax2.plot(*zip(*pts), color=COLORS[i], linewidth=1.8, label=name)
        ax1.set_xlim(0.5, turns + 0.5); ax1.set_ylim(-0.7, 5.7)
        ax1.set_yticks(range(6), AGENTS); ax1.set_title("行動 A の実行（■）", color=FG, size=13)
        ax2.set_xlim(0.5, turns + 0.5); ax2.set_ylim(0, 21)
        ax2.set_title("エネルギー", color=FG, size=13)
        ax2.legend(ncol=6, fontsize=9, facecolor=BG, labelcolor=FG, edgecolor="#333")
        for _ in range(int(sec_per_turn * FPS)):
            w.grab_frame()


def main(out):
    fig = plt.figure(figsize=(16, 9), dpi=120)
    writer = FFMpegWriter(fps=FPS, bitrate=3200)
    with writer.saving(fig, out, dpi=120):
        card(writer, fig, [
            ("国家の体力は、毎朝の習慣でできている。", "t"),
            ("では習慣は、何でできているのか。", "t"),
            ("LLMマルチエージェントによる「定着」の創発観測", "a"),
            ("AIエージェント社会シミュレーションハッカソン Vol.2", "d"),
        ], 6)
        card(writer, fig, [
            ("世界のルール（これがすべて）", "t"),
            ("行動A：エネルギーを4消費する ／ rest：消費しない", "b"),
            ("回復は毎ターン。続けると遅れて増える（住人には教えない）", "b"),
            ("中断すると蓄積は減る", "b"),
            ("プロンプトに「習慣」「協力」「目標」等の語は一切ない（grepで機械検証済み）", "a"),
            ("6人の住人（Claude Sonnet 5）を30ターン放つ。会話チャネルあり／なしで比較", "b"),
        ], 9)
        card(writer, fig, [("実験1：チャットのある村", "t"), ("何も指示していない。何が起きるか。", "d")], 4)
        replay(writer, fig, "experiments/EXP-001_会話あり_seed1", "チャットのある村（村1）", 2.0, True)
        card(writer, fig, [
            ("チャットのある村：続いたのは 6人中1人", "t"),
            ("村人たちは仮説に名前を付け（「比例仮説」「20キャップ説」）、", "b"),
            ("検証の分業と再現実験まで発明した——", "b"),
            ("しかし変数統制のためのA/rest交互実行が、連続実行を妨げた", "a"),
            ("みんなで調べる文化が生まれ、実践が止まった", "t"),
        ], 8)
        card(writer, fig, [("実験2：チャットのない村", "t"), ("同じ村人たちから、チャットだけを消す。", "d")], 4)
        replay(writer, fig, "experiments/EXP-004_会話なし_seed1", "チャットのない村（村1）", 0.7, False)
        card(writer, fig, [
            ("チャットのない村：続いたのは 6人中5人", "t"),
            ("村人たちは黙って試し、効果の実感とともに続けた", "b"),
            ("唯一の脱落者は資源が最少の個体——", "b"),
            ("単発の試行はできても、投資の連続に届かない「資源の罠」", "a"),
        ], 8)
        card(writer, fig, [
            ("5つの村での判定", "t"),
            ("チャットあり: 1/6・5/6・4/6・3/6・5/6人   チャットなし: 5/6・4/6・4/6・2/6・5/6人", "b"),
            ("「チャットは習慣の敵」説は村2・村4で逆転 → 約束の基準どおり取り下げ", "b"),
            ("再現失敗を、隠さずそのまま提出する", "a"),
        ], 8)
        card(writer, fig, [
            ("認定した創発：命名された仮説の発生と伝播", "t"),
            ("「比例仮説」「20説」、真のメカニズムを言い当てた「連続A回数依存説」——", "b"),
            ("名前を付けて広める文化が5つの村すべてで発生（チャットなしでは0/5、p≈0.004）", "b"),
            ("資源の罠：余白が下位の村人の脱落率84% vs 余裕のある村人16%（延べ84人）", "b"),
        ], 9)
        card(writer, fig, [
            ("国家の体力は、毎朝の習慣でできている。", "t"),
            ("定着率10ポイント ＝ 年間 0.46〜1.44兆円（公的統計による換算）", "a"),
            ("コード・全ログ・判定基準: github.com/kyomei-community/hackathon", "d"),
        ], 7)
    plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "deliverables/動画/demo_draft.mp4")
