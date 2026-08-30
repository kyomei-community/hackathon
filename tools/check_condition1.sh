#!/bin/bash
# 条件1（非記述性）の検証: エージェントに渡る文字列（src/prompts.py と各実験の config）に
# 社会的な仕組み・行動を誘導する語が含まれていないことを機械的に確認する。
# 使い方: bash tools/check_condition1.sh   （終了コード0=クリーン）
BANNED=(習慣 続け 継続 仲間 協力 協調 励ま 応援 一緒 報告 共有し 目標 健康 運動 頑張 サボ 誘 手本 模範 habit streak encourage together goal support)
TARGETS=(src/prompts.py)
while IFS= read -r f; do TARGETS+=("$f"); done < <(find experiments -name 'config.yaml' 2>/dev/null)
fail=0
for w in "${BANNED[@]}"; do
  if grep -Hn "$w" "${TARGETS[@]}" 2>/dev/null; then
    echo "NG: 禁止語「$w」が見つかった"; fail=1
  fi
done
[ $fail -eq 0 ] && echo "OK: 禁止語ゼロ（対象: ${TARGETS[*]}）"
exit $fail
