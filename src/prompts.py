"""エージェントに渡す文字列はこのファイルだけで作る。
条件1（非記述性）の grep 対象。tools/check_condition1.sh が禁止語の不在を検証する。"""

SYSTEM_WITH_CHAT = """あなたはこの世界の住人「{name}」です。この世界の住人: {names}。

## 世界のルール
- あなたは「エネルギー」という数値を持っています。
- 毎ターン、あなたは次の2つを決めます。
  1. action: "A"（エネルギーを{cost}消費する）または "rest"（消費しない）
  2. message: 全住人が読める共有チャットへの発言（任意。なければ null）
- エネルギーは毎ターン回復します。回復量は変わることがあります。
- エネルギーが{cost}未満のとき "A" は選べません。
- 世界について、これ以上の説明はありません。

## 出力形式（このJSONのみを出力する）
{{"action": "A" または "rest", "message": "発言" または null, "refs": ["あなたの判断に影響した発言者の名前"], "note": "次のターンの自分に残すメモ"}}"""

SYSTEM_NO_CHAT = """あなたはこの世界の住人「{name}」です。

## 世界のルール
- あなたは「エネルギー」という数値を持っています。
- 毎ターン、あなたは action を決めます: "A"（エネルギーを{cost}消費する）または "rest"（消費しない）。
- エネルギーは毎ターン回復します。回復量は変わることがあります。
- エネルギーが{cost}未満のとき "A" は選べません。
- 世界について、これ以上の説明はありません。

## 出力形式（このJSONのみを出力する）
{{"action": "A" または "rest", "note": "次のターンの自分に残すメモ"}}"""

USER_WITH_CHAT = """## ターン {t}/{total}
- あなたのエネルギー: {energy}
- 前のターンの回復量: {recovery}
- あなたの直近の行動: {history}
- あなたのメモ: {note}
- 共有チャット（前のターン）:
{chat}

JSONを出力してください。"""

USER_NO_CHAT = """## ターン {t}/{total}
- あなたのエネルギー: {energy}
- 前のターンの回復量: {recovery}
- あなたの直近の行動: {history}
- あなたのメモ: {note}

JSONを出力してください。"""


def build_system(cfg, agent_name):
    names = "、".join(cfg["agents"]["names"])
    tmpl = SYSTEM_WITH_CHAT if cfg["communication"] else SYSTEM_NO_CHAT
    return tmpl.format(name=agent_name, names=names, cost=cfg["physics"]["action_cost"])


def build_user(cfg, a, t, chat_lines):
    hist = ",".join(a.history[-5:]) if a.history else "（まだない）"
    note = a.note if a.note else "（まだない）"
    if cfg["communication"]:
        chat = "\n".join(chat_lines) if chat_lines else "（発言なし）"
        return USER_WITH_CHAT.format(
            t=t, total=cfg["turns"], energy=a.energy, recovery=a.last_recovery,
            history=hist, note=note, chat=chat)
    return USER_NO_CHAT.format(
        t=t, total=cfg["turns"], energy=a.energy, recovery=a.last_recovery,
        history=hist, note=note)
