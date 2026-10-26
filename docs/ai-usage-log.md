# AI 使用紀錄

每完成一個里程碑追加一段，M7 時整理成作品頁與 README 的「AI 使用說明」表格。

## M0 repo 初始化（2026-10-26）

**工具**：Claude Code（Claude Opus 5.5）

**Claude Code 做了什麼**
- 依 `CLAUDE.md` 建立 `.gitignore`（排除 `.env`、`.venv/`、`__pycache__/`、`data/index.npz` 等）、`.gitattributes`（`* text=auto eol=lf`）、`.env.example`
- `git init -b main`、設定 remote `https://github.com/kdwjzh/fiba-rules-faq.git`，分成數個 commit 後推上 GitHub
- `.env.example` 參考課程 Lab 5 的版本改寫：新增 `EMBED_MODEL`；註明雲端模型只讀 `{PROFILE}_MODEL`（對應 Lab 5 雲端 fallback 到 `LLM_MODEL` 造成 404 的問題）

**Jimmy 修改或否決了什麼**
- （待填）

**驗證方式**
- `git status` 確認 `.env` 不會被追蹤；`git ls-remote` 確認遠端原本是空的
- 推送後到 GitHub 確認 repo 為 Public、檔案齊全
