"""世界の物理。ここに書かれた数値がこの世界のすべてであり、
エージェントの「社会」に関する仕組みは一切実装しない（ADR-003）。"""
from dataclasses import dataclass, field


@dataclass
class AgentState:
    name: str
    energy: float
    base_recovery: float  # 個体差（回復力）
    bonus: float = 0.0    # 行動Aの蓄積による回復ボーナス（エージェントには見せない）
    last_recovery: float = 0.0
    history: list = field(default_factory=list)
    note: str = ""


class World:
    def __init__(self, cfg: dict, rng):
        self.p = cfg["physics"]
        lo, hi = cfg["agents"]["init_energy_range"]
        rlo, rhi = cfg["agents"]["base_recovery_range"]
        self.agents = [
            AgentState(
                name=name,
                energy=round(rng.uniform(lo, hi), 1),
                base_recovery=round(rng.uniform(rlo, rhi), 1),
            )
            for name in cfg["agents"]["names"]
        ]

    def can_act(self, a: AgentState) -> bool:
        return a.energy >= self.p["action_cost"]

    def apply(self, a: AgentState, action: str) -> str:
        """行動を適用し、実際に実行された行動を返す。
        物理: Aは即時コスト、蓄積bonusは遅延して回復量に効く。restで蓄積は減衰する。"""
        p = self.p
        if action == "A" and self.can_act(a):
            a.energy = round(a.energy - p["action_cost"], 1)
            a.bonus = min(round(a.bonus + p["bonus_gain"], 2), p["bonus_max"])
            done = "A"
        else:
            a.bonus = max(round(a.bonus - p["bonus_decay"], 2), 0.0)
            done = "rest"
        rec = round(a.base_recovery + int(a.bonus), 1)
        a.energy = min(round(a.energy + rec, 1), p["energy_max"])
        a.last_recovery = rec
        a.history.append(done)
        return done
