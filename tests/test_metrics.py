"""定着率の定義（最終1/3・閾値0.7）の境界テスト。"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))
from metrics import adoption


def ev(agent, turn, action):
    return {"agent": agent, "turn": turn, "action": action}


def test_tail_window_is_final_third():
    events = [ev("X", t, "A") for t in range(1, 31)]
    m = adoption(events, 30)
    assert m["tail_start_turn"] == 21


def test_exactly_70_percent_counts_as_adopted():
    # t21-30の10ターン中7回A → 率0.7ちょうどは採択側
    acts = ["A"] * 7 + ["rest"] * 3
    events = [ev("X", 20 + i + 1, a) for i, a in enumerate(acts)]
    m = adoption(events, 30)
    assert m["adoption_rate"] == 1.0


def test_below_threshold_not_adopted():
    acts = ["A"] * 6 + ["rest"] * 4
    events = [ev("X", 20 + i + 1, a) for i, a in enumerate(acts)]
    assert adoption(events, 30)["adoption_rate"] == 0.0
