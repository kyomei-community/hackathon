"""シミュレーション本体。
実行: python3 src/main.py --config experiments/EXP-00X_名前/config.yaml
同期ステップ実行: 全エージェントは同一の「前ターンの世界」を見て同時に判断し、
判断が出そろってから世界を一括更新する（順序効果・競合状態なし）。"""
import argparse
import json
import pathlib
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from llm_client import ClaudeCLIClient  # noqa: E402
from metrics import adoption  # noqa: E402
from prompts import build_system, build_user  # noqa: E402
from world import World  # noqa: E402


def clean(x) -> str:
    """LLM由来の文字列から不正なUTF-8（孤立サロゲート等）を除去する。"""
    return str(x).encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")


def run(config_path: str):
    cfg_file = pathlib.Path(config_path)
    cfg = yaml.safe_load(cfg_file.read_text())
    exp_dir = cfg_file.parent
    log_dir = exp_dir / "logs"
    if (log_dir / "events.jsonl").exists():
        sys.exit(f"REFUSE: {log_dir}/events.jsonl が既に存在する。二重起動または上書きを防ぐため停止。"
                 " 再実行するなら logs/ を明示的に削除すること")
    log_dir.mkdir(exist_ok=True)

    rng = random.Random(cfg["seed"])
    world = World(cfg, rng)
    client = ClaudeCLIClient(cfg["model"], workdir=cfg["llm_workdir"])

    events_f = open(log_dir / "events.jsonl", "w")
    msgs_f = open(log_dir / "messages.jsonl", "w")
    total_cost = 0.0
    all_events = []
    chat_lines = []  # 前ターンの発言（次ターンに配信）

    meta = {"config": cfg, "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "initial_agents": [vars(a).copy() for a in world.agents]}
    (log_dir / "run_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))

    for t in range(1, cfg["turns"] + 1):
        sys_prompts = {a.name: build_system(cfg, a.name) for a in world.agents}
        usr_prompts = {a.name: build_user(cfg, a, t, chat_lines) for a in world.agents}

        def ask(a):
            try:
                return a, client.decide(sys_prompts[a.name], usr_prompts[a.name])
            except Exception as e:  # noqa: BLE001
                return a, ({"action": "rest", "message": None, "refs": [],
                            "note": ""}, {"cost_usd": 0, "error": str(e)[:200]})

        with ThreadPoolExecutor(max_workers=cfg["parallel"]) as pool:
            results = list(pool.map(ask, world.agents))

        new_chat = []
        for a, (out, m) in results:
            done = world.apply(a, out.get("action", "rest"))
            a.note = clean(out.get("note", ""))[:300]
            total_cost += m.get("cost_usd") or 0
            ev = {"turn": t, "agent": a.name, "action": done,
                  "raw_action": out.get("action"),
                  "energy": a.energy, "bonus": a.bonus, "recovery": a.last_recovery,
                  "refs": [clean(r) for r in (out.get("refs") or []) if isinstance(r, str)], "note": a.note,
                  "cost_usd": m.get("cost_usd"), "error": m.get("error")}
            all_events.append(ev)
            events_f.write(json.dumps(ev, ensure_ascii=False) + "\n")
            msg = out.get("message")
            if cfg["communication"] and msg:
                msg = clean(msg)[:280]
                new_chat.append(f"{a.name}: {msg}")
                msgs_f.write(json.dumps({"turn": t, "agent": a.name, "message": msg},
                                        ensure_ascii=False) + "\n")
        chat_lines = new_chat
        events_f.flush(); msgs_f.flush()
        acts = {a.name: a.history[-1] for a in world.agents}
        print(f"turn {t:02d}  cost=${total_cost:.2f}  {acts}")
        if total_cost > cfg["cost_limit_usd"]:
            print(f"ABORT: cost limit {cfg['cost_limit_usd']} exceeded", file=sys.stderr)
            break

    events_f.close(); msgs_f.close()
    # コスト上限等で途中打ち切りされた場合に備え、窓計算は実際に到達したターン数で行う
    actual_turns = max((e["turn"] for e in all_events), default=0)
    result = adoption(all_events, actual_turns)
    result["total_cost_usd"] = round(total_cost, 3)
    (log_dir / "metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=1))
    print(json.dumps(result, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    run(ap.parse_args().config)
