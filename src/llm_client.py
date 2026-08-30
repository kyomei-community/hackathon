"""LLM呼び出し層。claude CLI の非対話モード（claude -p）をサブプロセスとして呼ぶ。
各呼び出しは独立プロセス・独立コンテキストであり、エージェント間で内部状態を共有しない。
この1ファイルを差し替えれば他プロバイダ（Ollama等）にも切替可能。"""
import json
import os
import subprocess
import time


class ClaudeCLIClient:
    def __init__(self, model: str, workdir: str, timeout: int = 120):
        self.model = model
        # 空ディレクトリを作業場所にする: プロジェクトの CLAUDE.md 等が
        # エージェントのコンテキストへ混入するのを防ぐ（実験の汚染防止）
        self.workdir = workdir
        os.makedirs(workdir, exist_ok=True)
        self.timeout = timeout

    def decide(self, system_prompt: str, user_prompt: str):
        # JSON不正は即時再試行、レート制限等はバックオフして再試行する
        last_err = None
        for delay in (0, 5, 30, 90):
            if delay:
                time.sleep(delay)
            try:
                return self._call(system_prompt, user_prompt)
            except Exception as e:  # noqa: BLE001
                last_err = e
        raise RuntimeError(f"LLM call failed after retries: {last_err}")

    def _call(self, system_prompt, user_prompt):
        cmd = [
            "claude", "-p",
            "--model", self.model,
            "--no-session-persistence",
            "--output-format", "json",
            "--append-system-prompt", system_prompt,
            user_prompt,
        ]
        r = subprocess.run(cmd, capture_output=True,
                           timeout=self.timeout, cwd=self.workdir)
        stdout = r.stdout.decode("utf-8", errors="replace")
        if r.returncode != 0:
            stderr = r.stderr.decode("utf-8", errors="replace")
            raise RuntimeError(f"claude -p rc={r.returncode}: {stderr[:300]}")
        outer = json.loads(stdout)
        payload = self._extract_json(outer["result"])
        meta = {
            "cost_usd": outer.get("total_cost_usd", 0.0),
            "duration_ms": outer.get("duration_ms"),
            "model": ",".join(outer.get("modelUsage", {}).keys()),
        }
        return payload, meta

    @staticmethod
    def _extract_json(text: str) -> dict:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError(f"no JSON object in output: {text[:200]}")
        return json.loads(text[start:end + 1])
