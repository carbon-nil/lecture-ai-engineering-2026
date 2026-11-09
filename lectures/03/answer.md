# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い
  - `app.ask`（素の LLM）は講座のことを知らないので、「レベル 1：基礎 / レベル 2：応用 / レベル 3：発展」のような一般論を長文で答え、「AI の活用レベル」の可能性にも触れたうえで「LMS や講師に確認を」と締めた。内容は `data/glossary.json` の `homework-levels` と一致しない。
  - `app.agent` は `search_glossary` で用語集を引いてから答え、「基礎（講義内容の確認）・実装（自分でコードを書く）・発展（調査や試行）」の 3 段階と「どれか 1 つで完了」「原則として採点なし」を短く答えた。用語集の定義と一致し、最後に「関連する回：第1回」が付いた。
- `--trace` で見えたツール呼び出し（ツール名と引数）
  - 「3レベル」の質問：`search_glossary({'query': '3レベル'})`
  - 「LoRAとQLoRAの違いは？」：`search_glossary({'query': 'LoRA'})` と `search_glossary({'query': 'QLoRA'})`。docstring の「用語を1つだけ入れる」に従い、1 回の LLM 応答で 2 つの呼び出しを並べて出していた。
  - 「第2回の内容から確認問題を1問出して」：`make_quiz({'lecture': 2})`
- 1 つの質問での LLM 呼び出し回数（`requests`）
  - 3 問とも `requests=2`（1 回目でツール呼び出しを決め、2 回目でツールの結果から回答を作る）。「LoRAとQLoRA」は `tool_calls=2` でも `requests=2` で、2 つの検索は同じ応答の中で依頼されていた。
- 追加したツールと、docstring に書いた説明
  - `app/tools.py` に `make_quiz(lecture: int) -> str` を追加。用語集から `lecture` が一致する用語を集めて `random.choice` で 1 つ選び、`{"question": "「○○」の意味は？", "answer": <definition>}` を返す。該当する用語が無い回（`lecture=0` など）は「第 0 回の確認問題が見つかりませんでした。用意されている回: 1, 2, 3, 4, 6」を返す。
  - docstring：「指定した回の用語から 1 つを選び、確認問題と答えを返す。『第2回の確認問題を出して』のように、復習用の問題を求められたときに使う。」
  - `app/agent.py` で `agent.tool_plain(tools.make_quiz)` を登録し、`INSTRUCTIONS` に「確認問題や復習クイズを求められたら make_quiz を使い、問題だけを出して答えは聞かれるまで伏せる」を 1 行足した。
  - `--list-tools` に `make_quiz` と上の docstring が出ることを確認した。`--trace` では 2 回実行してどちらも `make_quiz({'lecture': 2})` が呼ばれ、問題だけを出して答えは伏せた（1 回目「『量子化』の意味は？」、2 回目「『ランク（LoRAのr）』の意味は？」、どちらも `requests=2, tool_calls=1`）。
  - 確認 2 回目の出力は以下の通り。

    ```text
    --- trace ---
    [tool call]   make_quiz({'lecture': 2})
    [tool return] make_quiz -> {"question": "「ランク（LoRAのr）」の意味は？", "answer": "LoRAで使う低ランク行列の大きさを決めるハイパーパラメータ。…
    [usage] RunUsage(… input_tokens=938, output_tokens=46, requests=2, tool_calls=1)
    ```

## 宿題

- 取り組んだレベル：基礎 / 実装 / 発展
- やったこと：
- 結果：
- 気づき・疑問：
