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

## M1 Pages 先上線（2026-10-26）

**工具**：Claude Code（Claude Opus 5.5）

**Claude Code 做了什麼**
- `site/index.html`：作品頁空殼，四個區塊「做了什麼／怎麼執行／執行結果／AI 使用說明」加「參考資料」，頁尾註明以 FIBA 官方規則書為準；用少量 JS 讀取 `data/results.json`（還不存在時顯示預設文字）
- `.github/workflows/pages.yml`：push 到 main 或手動觸發時，把 `site/` 部署到 GitHub Pages
- 寫 workflow 前用 `git ls-remote --tags` 查各 action 目前的主版本：`actions/checkout@v7`、`configure-pages@v6`、`upload-pages-artifact@v5`、`deploy-pages@v5`（課程範例或網路教學常見的舊版號沒有照抄）

**Jimmy 修改或否決了什麼**
- （待填）

**驗證方式**
- 在瀏覽器以手機寬度（375px）預覽作品頁，確認不會橫向捲動
- 發現 M0 的 push 其實沒有成功（GitHub API 顯示 repo 沒有任何分支），M1 時一併重新 push
- 推送後確認 Actions 的 Deploy Pages 綠燈、Pages 網址打得開（待 Jimmy 設定 Settings → Pages 後確認）
