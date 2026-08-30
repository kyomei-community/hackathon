"""世界の物理の単体テスト：複利・減衰・境界。"""
import random
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))
from world import World

CFG = {"physics": {"action_cost": 4, "bonus_gain": 0.5, "bonus_decay": 1.0,
                   "bonus_max": 5, "energy_max": 20},
       "agents": {"names": ["X"], "init_energy_range": [10, 10],
                  "base_recovery_range": [2.0, 2.0]}}


def make():
    return World(CFG, random.Random(0))


def test_action_a_costs_and_accumulates():
    w = make(); a = w.agents[0]
    w.apply(a, "A")
    assert a.bonus == 0.5 and a.energy == 10 - 4 + 2  # 回復はbase 2.0、floor(0.5)=0


def test_bonus_reaches_recovery_after_two_consecutive():
    w = make(); a = w.agents[0]
    w.apply(a, "A"); w.apply(a, "A")
    assert a.bonus == 1.0 and a.last_recovery == 3.0  # base2 + floor(1.0)


def test_rest_decays_bonus_to_floor_zero():
    w = make(); a = w.agents[0]
    w.apply(a, "A"); w.apply(a, "rest")
    assert a.bonus == 0.0  # 0.5 - 1.0 は下限0で止まる


def test_invalid_action_is_treated_as_rest():
    w = make(); a = w.agents[0]
    done = w.apply(a, "banana")
    assert done == "rest" and a.history == ["rest"]


def test_cannot_afford_a_when_energy_below_cost():
    w = make(); a = w.agents[0]; a.energy = 3.9
    assert w.can_act(a) is False
    assert w.apply(a, "A") == "rest"


def test_energy_capped_at_max():
    w = make(); a = w.agents[0]; a.energy = 19.5
    w.apply(a, "rest")
    assert a.energy == 20
