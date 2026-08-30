"""マクロ指標の集計。定義は docs/02_観測設計.md と docs/01_世界設計.md に従う。"""


def adoption(events: list, turns: int, threshold: float = 0.7) -> dict:
    """定着率: 最終1/3のターンで行動Aの実行率が threshold 以上の個体の割合。"""
    tail_start = turns - turns // 3 + 1
    per_agent = {}
    for ev in events:
        if ev["turn"] >= tail_start:
            per_agent.setdefault(ev["agent"], []).append(ev["action"])
    rates = {k: v.count("A") / len(v) for k, v in per_agent.items() if v}
    adopted = [k for k, r in rates.items() if r >= threshold]
    return {
        "tail_start_turn": tail_start,
        "per_agent_A_rate": {k: round(r, 3) for k, r in rates.items()},
        "adopted_agents": adopted,
        "adoption_rate": round(len(adopted) / len(rates), 3) if rates else 0.0,
    }
