# AGENTS.md

籃球規則 FAQ 查詢（FIBA 2026）：輸入口語問題，用 embedding 從自建題庫找出最相關的規則問答。
這是課程「設計機器學習平台與系統架構」的個人作業「AI 小專案上線」。

## 專案結構
- `faq/`：主程式（Python 套件）
  - `llm.py`：模型設定抽象化（本地 Ollama／雲端切換，改自課程 Lab 5）
  - `store.py`：純函式：載入題庫、cosine 相似度、top-k、門檻判斷（**不可呼叫模型**）
  - `build_index.py`：把題庫轉成 embedding，存到 `data/index.npz`
  - `ask.py`：命令列查詢
  - `answer.py`：加強版：根據 top-3 用結構化輸出產生回答
  - `report.py`：跑測試查詢，輸出作品頁要用的結果（`--answers` 另跑結構化回答）
  - 本地 vs 雲端比較表（`compare.py`）沒有做：Jimmy 決定不做
- `data/faq.json`：題庫（人寫的內容，見下方規則）
- `data/test_queries.json`：測試查詢與期望答案 id
- `tests/`：pytest（不呼叫模型）
- `site/`：GitHub Pages 作品頁（靜態檔）
- `docs/ai-usage-log.md`：每個里程碑的 AI 使用紀錄
- `.github/workflows/`：`pages.yml`（部署作品頁）、`ci.yml`（ruff + pytest）
- `Dockerfile`、`compose.yaml`：容器版（Ollama ＋ 命令列 app，非 root）

## 開發環境
- Python 3.12，一律用 uv，不要用 pip：`uv sync`
- 本地模型：Ollama（Docker）在 `127.0.0.1:11434`
- 執行：`uv run python -m faq.ask "拿球走三步會怎樣"`
- 使用者在 Windows + PowerShell；給使用者的指令用 PowerShell 寫法（換行用反引號 `` ` ``、用 `curl.exe`）

## 送出前必須通過
- `uv run ruff check .`
- `uv run pytest -q`

## 規則
- 金鑰一律從 `.env` 讀，不寫進程式碼；`.env` 永遠不 commit，只 commit `.env.example`
- 測試與 CI 不得呼叫任何模型或網路
- 不得把 FIBA 規則書原文整段貼進 repo；`data/faq.json` 的答案必須是自己的話，並附條號
- `data/faq.json` 中 `status` 不是 `"verified"` 的題目，不可當成已完成
- commit 訊息用 `feat:`、`fix:`、`docs:`、`chore:`、`test:` 開頭，一個 commit 只做一件事
