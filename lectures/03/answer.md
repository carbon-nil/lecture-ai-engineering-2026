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

- 取り組んだレベル：発展 (a)
- やったこと
  - `adk_agent/glossary_agent/` に `agent.py` と `__init__.py`（`from . import agent` の 1 行）を作った。`agent.py` は問題文の形のとおりで、`INSTRUCTIONS` を `app.agent` から、ツール 3 つ（`search_glossary`・`get_lecture_summary`・`make_quiz`）を `app.tools` から import して `tools=[...]` に渡した。モデル名は `app.config.MODEL`（既定 `gemini-3.5-flash-lite`）を使い、`app/` のファイルは変えていない。
  - 実行環境は手元の Linux（aarch64）。`uv run --with google-adk` で入った ADK は 2.14.0。`adk run` は対話型なので、記録のために `--replay <json>` で同じ質問を 1 問ずつ新しいセッションに投げた（json は `{"state": {}, "queries": ["..."]}`）。ツール呼び出しとトークン数は、`--log_level debug` を付けたときの `/tmp/agents_log/agent.*.log` から読んだ。

    ```bash
    # 問題文の指定どおり（対話型）
    PYTHONPATH=. uv run --with google-adk adk run adk_agent/glossary_agent
    # 記録用：1 問ずつ非対話で実行し、ツール呼び出しを debug ログに残す
    PYTHONPATH=. uv run --with google-adk adk run --in_memory --log_level debug --replay q.json adk_agent/glossary_agent
    ```

  - 比較相手は演習の Pydantic AI 版（`app.agent --trace`）。指示・ツール・docstring は同じものを使った。
- 結果
  - 演習と同じ 3 問への回答とツール呼び出し

    | 質問 | Pydantic AI 版（演習） | ADK 版 |
    |---|---|---|
    | 3レベルとは | `search_glossary({'query': '3レベル'})` 1 回。基礎・実装・発展の 3 段階、どれか 1 つで完了、採点なし。末尾「（関連する回：第1回）」 | `search_glossary({'query': '3レベル'})` 1 回。同じ内容を番号付きリストで。末尾「第1回」 |
    | LoRA と QLoRA の違い | `search_glossary` を LoRA・QLoRA で 2 回。LoRA は低ランク行列だけを学習、QLoRA は重みを 4 ビット量子化したうえで LoRA。末尾「（第2回）」 | 同じ 2 回・同じ引数。回答の構成も同じで、見出しに英語の正式名称（Low-Rank Adaptation、Quantized LoRA）が付いた。末尾「関係する回：第2回」 |
    | 第2回の確認問題を 1 問 | `make_quiz({'lecture': 2})`。「『ランク（LoRAのr）』の意味は？」と問題だけ出し、答えは伏せた | `make_quiz({'lecture': 2})`。同じ用語で「意味は何でしょうか？」と問題だけ出し、「答えを知りたいときは聞いて」と添えた。末尾「関連する回：第2回」 |

    - LLM 呼び出し回数はどちらも 1 問あたり 2 回（ツール呼び出しを決める 1 回と、結果から回答を作る 1 回）。この講座の知識を問う質問ではトークンの消費が微増したものの、全体として大きくトークン消費量は変わらなかった。

    | 質問 | Pydantic AI 版 入力 / 出力 | ADK 版 入力 / 出力（2 回の合計） |
    |---|---|---|
    | 3レベルとは | 1123 / 142 | 504+627=1131 / 18+112=130 |
    | LoRA と QLoRA の違い | 1536 / 183 | 493+1049=1542 / 37+165=202 |
    | 第2回の確認問題 | 938 / 46 | 494+574=1068 / 14+48=62 |

  - 書き方の比較

    | 観点 | Pydantic AI（`app/agent.py`） | ADK（`adk_agent/glossary_agent/agent.py`） |
    |---|---|---|
    | 指示の渡し方 | `Agent(instructions=INSTRUCTIONS)` | `Agent(instruction=INSTRUCTIONS, name="glossary_agent")`。`instruction` は単数形で、`name` が必須 |
    | ツールの渡し方 | `agent.tool_plain(tools.search_glossary)` と 1 つずつ登録 | `tools=[tools.search_glossary, ...]` と関数のリストで渡す。どちらも関数の docstring と型ヒントがそのまま説明文と引数の schema になる（ADK 側は `FunctionTool(...)._get_declaration().description` が docstring そのものだった） |
    | モデルの指定 | 実行時に `run_sync(..., model=GoogleModel(...))` で渡す（テストでは TestModel に差し替えられる） | `Agent(model=...)` と定義に書く。API キーは環境変数 `GEMINI_API_KEY` を ADK が読む |
    | 実行 | `argparse` で CLI を自分で書く | `adk run <dir>` が対話 CLI を提供する。`--replay` で非対話、`--log_level debug` でリクエスト全文が読める |
    | ツール呼び出しの観察 | `result.all_messages()` を走査して `[tool call]` を表示する処理を自分で書く | 標準出力には出ない。debug ログに `name: search_glossary, args: {...}` と `function_call` / `function_response` が記録される |
    | 置き場所の約束事 | `python -m app.agent` で動けばよい | フォルダ名がエージェント名。`__init__.py` に `from . import agent`、`agent.py` に `root_agent` が要る |
    | 指示への追記 | `INSTRUCTIONS` がそのまま system instruction になる | system instruction の末尾に `You are an agent. Your internal name is "glossary_agent".` が自動で足される（debug ログで確認） |

- 気づき・疑問
  - 指示とツールが同じなら、組み立てるフレームワークが違っても、回答の中身・LLM 呼び出し回数・トークン数はほぼ同じになった。エージェントのうちループを誰が回すかが変わっただけで、そのふるまいが指示とツールに依存していることが確かめられた。
  - 回答の細かい違い（末尾の回の書き方が「（第2回）」か「関係する回：第2回」か、英語名を付けるか）は、同じフレームワークで実行し直しても変わる程度には変動していた。
  - ADK は指示の末尾に名前の定型文を自動で足すようだが、今回は回答に影響した様子はなかった。
