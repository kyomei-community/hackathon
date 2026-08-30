"""P3: ミクロの定着率差 → 日本経済インパクト（円）への換算。

これはシミュレーションではない。出典つき係数による決定論的な計算式である（CLAUDE.md 4条）。
シミュレーションが与えるのは「会話チャネルの有無による定着率の差 Δp」のみ。
それ以外はすべて公的統計・公開研究の値であり、楽観/保守の幅で示す。

使い方: python3 tools/convert_macro.py <定着率_会話あり> <定着率_会話なし>
"""
import sys

# ---- 出典つきパラメータ ----------------------------------------------------
# 国民医療費 46.7兆円（令和4年度, 厚生労働省「国民医療費の概況」）: 規模感の文脈用
# [1] 運動習慣の有無による一人当たり年間医療費の差。
#     文部科学省「スポーツや身体運動の促進による医療費削減効果」(第4章) ほかの
#     国内研究レンジから保守〜楽観で設定
MED_COST_DIFF_JPY = (30_000, 100_000)   # 円/人/年 (保守, 楽観)
# [2] 健康リスク保有による労働生産性損失 76.6万円/人/年（横浜市研究, 経産省
#     「予防・健康づくりの意義と課題」2019 資料2）。習慣定着はその一部を低減すると仮定
PRODUCTIVITY_LOSS_JPY = 766_000
PRODUCTIVITY_REDUCTION = (0.05, 0.15)   # 低減率 (保守, 楽観)
# [3] 対象人口シナリオ
COHORTS = {
    "セカプラ対象層（50〜64歳女性, 総務省人口推計）": 13_150_000,
    "就業者全体（総務省 労働力調査 約6,700万人）": 67_000_000,
}
# ---------------------------------------------------------------------------


def convert(p_with: float, p_without: float):
    dp = p_with - p_without
    print(f"## ミクロ→マクロ換算（Δ定着率 = {p_with:.2f} − {p_without:.2f} = {dp:+.2f}）\n")
    print("前提：一人が『会話のある集団』に属することで、属さない場合に比べ")
    print(f"習慣が定着する確率が Δp = {dp:.2f} 上がる、という実験結果を外挿する。\n")
    print("| 対象人口 | 医療費差のみ | 医療費差＋生産性 |")
    print("|---|---|---|")
    for name, pop in COHORTS.items():
        n = pop * dp  # 追加で定着する人数
        med_lo, med_hi = (n * MED_COST_DIFF_JPY[0], n * MED_COST_DIFF_JPY[1])
        prod_lo = n * PRODUCTIVITY_LOSS_JPY * PRODUCTIVITY_REDUCTION[0]
        prod_hi = n * PRODUCTIVITY_LOSS_JPY * PRODUCTIVITY_REDUCTION[1]
        f = lambda x: f"{x/1e12:.2f}兆円" if x >= 1e12 else f"{x/1e8:,.0f}億円"
        print(f"| {name} | {f(med_lo)}〜{f(med_hi)}/年 | {f(med_lo+prod_lo)}〜{f(med_hi+prod_hi)}/年 |")
    print("\n※ 係数の出典と限界は RESULTS.md に記載。生産性項は就業者にのみ適用するのが厳密だが、")
    print("  ここでは簡明のため同一係数で示し、その旨を明記する。")


if __name__ == "__main__":
    convert(float(sys.argv[1]), float(sys.argv[2]))
