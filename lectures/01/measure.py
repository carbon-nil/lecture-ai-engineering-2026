"""
応答時間およびトークン数を、モデル・質問ごとに計測する。

使い方:
    uv run python -m lectures.01.measure

レート制限との関係を見るため、各キューの間に待ち時間を入れない。
失敗した回もエラーとして記録する。
"""

import time
from datetime import datetime
from pathlib import Path
from statistics import mean

from google import genai
from google.genai import errors

from app.ask import DEFAULT_QUESTION
from app.config import get_api_key

MODELS = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.1-flash-lite"]
QUESTIONS = {"LoRA": "LoRAとは何ですか？", "3レベル": DEFAULT_QUESTION}
REPEAT = 3

def main() -> None:
    client = genai.Client(api_key=get_api_key())
    results = []  # (model, 質問, 秒, 入力, 出力, 思考, エラー)
    lines = []  # ファイルに書く表
    answers = []  # ファイルに書く回答本文

    def emit(text: str = "") -> None:
        print(text)
        lines.append(text)

    emit("| モデル | 質問 | 回 | 秒 | 入力 | 出力 | 思考 | 結果 |")
    emit("|---|---|---|---|---|---|---|---|")
    for model in MODELS:
        for label, question in QUESTIONS.items():
            for i in range(1, REPEAT + 1):
                start = time.perf_counter()
                try:
                    response = client.models.generate_content(model=model, contents=question)
                except errors.APIError as e:
                    sec = time.perf_counter() - start
                    results.append((model, label, sec, None, None, None, e.code))
                    emit(f"| {model} | {label} | {i} | {sec:.2f} | - | - | - | エラー {e.code} |")
                    answers.append(f"## {model} / {label} / {i}回目（エラー {e.code}）\n\n{e.message}\n")
                    continue
                sec = time.perf_counter() - start
                u = response.usage_metadata
                row = (model, label, sec, u.prompt_token_count, u.candidates_token_count or 0, u.thoughts_token_count or 0, None)
                results.append(row)
                emit(f"| {model} | {label} | {i} | {sec:.2f} | {row[3]} | {row[4]} | {row[5]} | OK |")
                answers.append(f"## {model} / {label} / {i}回目（{sec:.2f}秒）\n\n{response.text}\n")

    emit("\n## 平均（成功した回のみ）\n")
    emit("| モデル | 質問 | 成功 | 秒 | 出力 | 思考 | 出力トークン/秒 |")
    emit("|---|---|---|---|---|---|---|")
    for model in MODELS:
        for label in QUESTIONS:
            ok = [r for r in results if r[0] == model and r[1] == label and r[6] is None]
            if not ok:
                emit(f"| {model} | {label} | 0/{REPEAT} | - | - | - | - |")
                continue
            sec = mean(r[2] for r in ok)
            out = mean(r[4] for r in ok)
            thought = mean(r[5] for r in ok)
            emit(f"| {model} | {label} | {len(ok)}/{REPEAT} | {sec:.2f} | {out:.0f} | {thought:.0f} | {(out + thought) / sec:.0f} |")

    path = Path(__file__).parent / "outputs" / f"{datetime.now():%Y%m%d-%H%M%S}.md"
    path.parent.mkdir(exist_ok=True)
    questions = "\n".join(f"- {label}: {q}" for label, q in QUESTIONS.items())
    path.write_text(
        f"# 計測結果 {datetime.now():%Y-%m-%d %H:%M}\n\n## 質問\n\n{questions}\n\n## 各回\n\n"
        + "\n".join(lines) + "\n\n# 回答本文\n\n" + "\n".join(answers),
        encoding="utf-8",
    )
    print(f"\n[保存] {path}")

if __name__ == "__main__":
    main()
