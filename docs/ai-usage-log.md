# AI 使用紀錄

每完成一個里程碑追加一段，M7 時整理成作品頁與 README 的「AI 使用說明」表格。

## M0 repo 初始化（2026-10-26）

**工具**：Claude Code（Claude Opus 5.5）

**Claude Code 做了什麼**
- 依 `CLAUDE.md` 建立 `.gitignore`（排除 `.env`、`.venv/`、`__pycache__/`、`data/index.npz` 等）、`.gitattributes`（`* text=auto eol=lf`）、`.env.example`
- `git init -b main`、設定 remote `https://github.com/kdwjzh/fiba-rules-faq.git`，分成數個 commit 後推上 GitHub
- `.env.example` 參考課程 Lab 5 的版本改寫：新增 `EMBED_MODEL`；註明雲端模型只讀 `{PROFILE}_MODEL`（對應 Lab 5 雲端 fallback 到 `LLM_MODEL` 造成 404 的問題）

**Jimmy 修改或否決了什麼**
- 自己在 GitHub 建立 repo `fiba-rules-faq`，並確認為 Public
- Claude Code 第一次 push 時認證失敗（Git Credential Manager 存的帳密無效），我改用瀏覽器登入 GitHub 授權後才推送成功
- 檢查 `.gitignore` 有排除 `.env`，確認金鑰不會被 commit

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
- 到 Settings → Pages 把 Source 設為 GitHub Actions；第一次設定時 repo 還是空的，設定沒有存下來，之後用 kdwjzh 帳號重新設定，並重新整理頁面確認
- 在 Actions 手動按 Run workflow 重新部署，確認 Deploy Pages 綠燈
- 打開 https://kdwjzh.github.io/fiba-rules-faq/ 確認作品頁四個區塊都有出現

**驗證方式**
- 在瀏覽器以手機寬度（375px）預覽作品頁，確認不會橫向捲動
- 發現 M0 的 push 其實沒有成功（GitHub API 顯示 repo 沒有任何分支），M1 時一併重新 push
- 第一次部署失敗：`configure-pages` 回報 `Get Pages site failed ... Not Found`。原因是 repo 還是空的時候就去 Settings → Pages 選 GitHub Actions，設定沒有存下來（GitHub API 顯示 `has_pages: false`）
- Jimmy 用 kdwjzh 帳號重新設定 Source、手動 Run workflow 後，Deploy Pages 綠燈；`curl` 確認 https://kdwjzh.github.io/fiba-rules-faq/ 回傳 200，頁面有五個區塊標題

## M2 骨架＋CI（2026-10-27）

**工具**：Claude Code（Claude Opus 5.5）

**Claude Code 做了什麼**
- 發現電腦上沒有 uv（交接說明寫有裝），經 Jimmy 同意後用 `winget install --id astral-sh.uv -e` 安裝 uv 0.13.6
- `pyproject.toml`、`.python-version`（3.12）、`uv.lock`：一般相依 `openai`、`python-dotenv`、`numpy`；dev 相依 `pytest`、`ruff`、`matplotlib`；ruff 規則沿用課程 Lab 5
- `faq/store.py`：純函式 `load_faq`、`doc_text`、`faq_hash`、`normalize`、`cosine`、`top_k`、`is_answerable`，門檻 `THRESHOLD = 0.5`
- `faq/llm.py`：改自 Lab 5 `agent/llm.py`。修正雲端 profile 會 fallback 到 `LLM_MODEL` 的問題（只有 local 讀 `LOCAL_MODEL`／`LLM_MODEL`）；新增 `EMBED_MODEL`；未知的 profile 直接報錯，不再默默改用 local
- `tests/test_store.py`：9 個測試，用手做的 3 維向量測正規化、cosine、top-k 排序、門檻拒答、題庫 hash
- `.github/workflows/ci.yml`：`checkout@v7` → `astral-sh/setup-uv@v7`（Python 3.12）→ `uv sync --locked --dev` → ruff → pytest

**Jimmy 修改或否決了什麼**
- Claude Code 發現電腦上沒有 uv，我選擇讓它用 winget 安裝（另一個選項是自己手動裝）

**驗證方式**
- 本機 `uv run ruff check .`：All checks passed；`uv run pytest -q`：9 passed
- 設定 `LLM_MODEL=qwen3:0.6b` 後呼叫 `get_llm('openai')`，模型仍是 `gpt-6-luna`，確認 Lab 5 的 404 問題已修（沒有連網路）
- 已知待辦：`PRICES` 沿用 Lab 5 價目表，沒有 `.env.example` 裡的 `gemini-3.8-flash`；M6 做 compare 前要依實際使用的雲端模型補上價格

## M3 10 題跑通（2026-10-27）

**工具**：Claude Code（Claude Opus 5.5）

**Claude Code 做了什麼**
- 從 FIBA 官網下載 2026 v1.1 規則書，用 pypdf 轉成文字（只放在暫存資料夾，沒有進 repo），核對目錄條號後起草 10 題 `data/faq.json`，全部是 `draft`：走步 Art. 25、二次運球 Art. 24、3 秒 Art. 26、8 秒 Art. 28、24 秒 Art. 29、回場 Art. 30、干擾球 Art. 31、五犯 Art. 41、團隊犯規 Art. 42、disruptive foul Art. 37
- `data/test_queries.json`：12 條口語查詢（10 條對應題庫、2 條題庫沒有）
- `faq/build_index.py`（呼叫本地 embedding，存 vectors＋ids＋題庫 hash）、`faq/ask.py`（top-3＋門檻拒答，題庫改過會提醒重建索引；草稿答案會標「尚未人工核對」）、`store.load_index`
- `tests/test_faq_data.py`：題庫欄位、category、條號格式、id 不重複、測試查詢的 id 都存在；答案若提到 unsportsmanlike 必須同時說明已取消

**條號核對時發現的差異**
- 2026 版 Art. 37 是 disruptive foul、Art. 38 flagrant foul、Art. 39 disqualifying foul、Art. 40 fighting；**五次犯規在 Art. 41**，不是交接說明裡 2024 版對照的 Art. 40
- Art. 25 走步、26 三秒、28 八秒、29 進攻計時與 2024 版相同

**Jimmy 修改或否決了什麼**
- Claude Code 找不到 Docker 和 Ollama，我選擇自己安裝 Docker Desktop，沒有改用 Windows 版 Ollama，照原本的課程環境做，M6 的 Dockerfile 也需要 Docker

**驗證方式**
- `uv run ruff check .`：All checks passed；`uv run pytest -q`：32 passed
- 電腦上沒有 Docker／Ollama／WSL，`build_index` 與 `ask` 還沒用真的模型跑過；Jimmy 選擇自己安裝 Docker Desktop
- Jimmy 裝好 Docker Desktop（WSL 2）後，用 Docker 啟動 Ollama，下載 `qwen3-embedding:0.6b`、`qwen3:1.7b`；`build_index` 10 題、維度 1024、約 7 秒
- 第一次跑 12 條測試查詢：Hit@1 6/10、Hit@3 8/10；3 秒（「中鋒一直站在籃下」）和回場（「隊友跑回中線另一邊才接到」）連前 3 名都沒有。題庫外 2 條最高分 0.452，跟題庫內最低分 0.469 幾乎黏在一起，原本門檻 0.5 會誤拒 2 條答對的
- 依 Qwen3-Embedding 的建議，查詢前面加英文任務說明（文件不加），並比較不加／英文／中文三種：英文最好，Hit@1 7/10、Hit@3 10/10，題庫外最高分降到 0.416、題庫內第 1 名最低 0.473，因此門檻改為 0.45
- 沒有為了讓測試查詢命中去改題庫的別名，避免只是對答案；剩下 3 條 Hit@1 沒中的都被 travelling 搶第 1，M4 擴充題庫時再觀察
