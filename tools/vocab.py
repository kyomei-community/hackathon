"""語彙の定着（02_観測設計の本命指標）の検出。
チャットログから「誰かが初出した言い回しが、何人に・何ターンで広がったか」を機械的に数える。
恣意的な語選びを避けるため、抽出は正規表現パターンの網羅で行う:
  - 「◯◯説」型（命名された仮説）
  - カギ括弧つきの言い回し「...」
使い方: python3 tools/vocab.py experiments/EXP-001_.../logs/messages.jsonl"""
import json
import re
import sys
from collections import defaultdict

PATTERNS = [
    re.compile(r"[一-龥ぁ-んァ-ヶA-Za-z0-9]{1,8}説"),
    re.compile(r"「([^」]{2,14})」"),
]


def main(path):
    msgs = [json.loads(l) for l in open(path)]
    first = {}                       # term -> (turn, agent)
    users = defaultdict(set)         # term -> {agents}
    last_turn = defaultdict(int)
    for m in msgs:
        found = set()
        for pat in PATTERNS:
            for g in pat.findall(m["message"]):
                found.add(g if isinstance(g, str) else g[0])
        for term in found:
            if term not in first:
                first[term] = (m["turn"], m["agent"])
            users[term].add(m["agent"])
            last_turn[term] = max(last_turn[term], m["turn"])
    rows = [(t, first[t][0], first[t][1], len(users[t]), sorted(users[t]), last_turn[t])
            for t in first if len(users[t]) >= 2]
    rows.sort(key=lambda r: (-r[3], r[1]))
    print(f"{'語':<16}{'初出t':>4} {'初出者':<5}{'使用者数':>4}  使用者（生存最終t）")
    for term, t0, who, n, agents, tl in rows[:20]:
        print(f"{term:<16}{t0:>4} {who:<5}{n:>4}  {','.join(agents)} (t{tl})")


if __name__ == "__main__":
    main(sys.argv[1])
