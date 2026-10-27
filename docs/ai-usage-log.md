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
- 自己下載安裝 WSL 2 和 Docker Desktop，再請 Claude Code 檢查 WSL 2 狀態（預設版本 2，docker-desktop 執行中）
- 對照 FIBA 2026 v1.1 規則書核對 10 題答案與條號後，把 status 全部改成 verified

**驗證方式**
- `uv run ruff check .`：All checks passed；`uv run pytest -q`：32 passed
- 電腦上沒有 Docker／Ollama／WSL，`build_index` 與 `ask` 還沒用真的模型跑過；Jimmy 選擇自己安裝 Docker Desktop
- Jimmy 裝好 Docker Desktop（WSL 2）後，用 Docker 啟動 Ollama，下載 `qwen3-embedding:0.6b`、`qwen3:1.7b`；`build_index` 10 題、維度 1024、約 7 秒
- 第一次跑 12 條測試查詢：Hit@1 6/10、Hit@3 8/10；3 秒（「中鋒一直站在籃下」）和回場（「隊友跑回中線另一邊才接到」）連前 3 名都沒有。題庫外 2 條最高分 0.452，跟題庫內最低分 0.469 幾乎黏在一起，原本門檻 0.5 會誤拒 2 條答對的
- 依 Qwen3-Embedding 的建議，查詢前面加英文任務說明（文件不加），並比較不加／英文／中文三種：英文最好，Hit@1 7/10、Hit@3 10/10，題庫外最高分降到 0.416、題庫內第 1 名最低 0.473，因此門檻改為 0.45
- 沒有為了讓測試查詢命中去改題庫的別名，避免只是對答案；剩下 3 條 Hit@1 沒中的都被 travelling 搶第 1，M4 擴充題庫時再觀察

## M4 擴充題庫（2026-10-27，待 Jimmy 審核）

**工具**：Claude Code（Claude Opus 5.5）

**Claude Code 做了什麼**
- 讀 2026 規則修改摘要（Art. 1、2、4、15、24、36、37、38、Appendix F 有改），再逐條讀規則書，新增 34 題草稿，題庫共 44 題（10 題 verified、34 題 draft）
- 新題目分類：比賽基本 8、2026 新制 4（投籃動作 Art. 15、技術犯規分兩類 Art. 36、flagrant foul Art. 38、重播 Appendix F）、違例 7、犯規 7、罰則 5、比賽管理 3
- 用腳本把新題目接在 `faq.json` 後面，並檢查原本 10 題的內容完全沒變
- `data/test_queries.json` 增加到 25 條（題庫內 22、題庫外 3）
- `tests/test_faq_data.py`：出處也接受 `FIBA OBR 2026 Appendix ...`，因為重播規定在附錄、沒有條號

**起草時自己抓到的錯**
- 無衝撞區的別名一開始寫成「1.25 公尺」（舊印象），規則書 Art. 2.5.7 是 **1.30 公尺**，已改
- 技術犯規的罰球人選一開始寫「任何隊員都可以罰」，Art. 44.2.2 是「由對方總教練指定」，已改
- 2026 版假摔（fake being fouled）屬於**第 1 類技術犯規**，會累計成取消資格；舊資料常只說是警告或一般技術犯規

**Jimmy 修改或否決了什麼**
- 對照 FIBA 2026 v1.1 規則書逐題核對 Claude Code 起草的 34 題新題目與條號，確認後把 status 改成 verified（題庫 44 題全部 verified）
- 同意重播（IRS）那題的出處寫成「FIBA OBR 2026 Appendix F」，因為規則書把它放在附錄、沒有條號

**驗證方式**
- `uv run ruff check .`：All checks passed；`uv run pytest -q`：100 passed
- 重建 44 題索引（約 16 秒），25 條查詢：Hit@1 16/22、Hit@3 20/22
- 題庫變大後，題庫外查詢的分數也變高（「排球一局打到幾分」0.561、「籃球鞋怎麼挑」0.491），題庫內第 1 名最低 0.473，兩邊重疊；比較 0.40–0.50 後把門檻改為 0.50（誤拒 1/22、題庫外拒答 2/3），剩下的留給 M5 由模型判斷
- 「中鋒一直站在籃下」（3 秒）和「灌籃後掛在籃框上」（技術犯規）連前 3 名都沒有

## M5 加強版：結構化回答＋guard（2026-10-27）

**工具**：Claude Code（Claude Opus 5.5）

**Claude Code 做了什麼**
- `faq/answer.py`：檢索 top-3 → 低於門檻直接拒答 → `qwen3:1.7b` 用 `chat.completions.parse` + Pydantic `RuleAnswer`（answer／source_ids／confidence）產生回答 → `guard` 檢查 → 沒通過就改顯示檢索第 1 名的題庫答案（人工審核過的文字）
- `guard` 規則：source_ids 必須是 top-3 的子集；有回答就要附出處；不超過 100 字；不能只寫 id；confidence「低」改成拒答
- `tests/test_answer_guard.py`：10 個測試，只測檢查函式，不呼叫模型
- `pydantic` 改成直接相依（原本只是 openai 間接裝進來）

**試跑時發現的問題與修正**（25 條測試查詢，每輪約 5 分鐘）
1. 第一版 prompt 的 id 標成 `[id: travelling]`，模型把 `id: travelling` 整段抄進 source_ids，guard 擋下 → 改格式並列出可用 id
2. 讓模型自己決定拒答時，題庫內 22 條有 9–12 條被誤拒（模型推理過程顯示它沒把「被包夾帶不過半場」連到 8 秒規則）→ 改成拒答交給檢索門檻，模型只挑條目，信心「低」才拒答
3. 比較思考模式：`/no_think`、`think=false` 都沒效，只有 `reasoning_effort="none"` 能關（14 秒 → 1–2 秒）；但關掉後引用正確率較低（14 vs 16／22），還出現 FAQ 以外的知識（回答「排球一局打到 25 分」），所以保留思考模式
4. 模型有時把整段 FAQ 原文貼進 answer、或 answer 只寫 id → guard 加上 100 字上限與「只有 id」檢查

**最後一輪結果（本機 qwen3:1.7b，同一設定每次跑結果會略有不同）**
- 題庫外 3 條：全部拒答（2 條被門檻擋、「排球」由模型低信心擋下）
- 題庫內 22 條：模型回答被採用 13 條，其中引用正確 10 條；guard 擋下 8 條改顯示題庫答案；門檻誤拒 1 條
- guard 擋不住語意錯誤：例如「切入被撞倒」的回答把撞人與阻擋講反、「球碰到腳」內容對但出處引用 goaltending。小模型的生成品質有限，作品頁的主要結果還是以檢索（M3／M4 的 Hit@1、Hit@3）為主

**Jimmy 修改或否決了什麼**
- 同意 Claude Code 把拒答改由檢索門檻決定、保留思考模式（較慢但較準）的做法
- 自己用 faq.answer 測了 3 題：「拿球跑三步會被吹嗎」回答正確；「什麼是走步」只回答步數規則，沒有解釋名詞；「什麼是進攻犯規」完全答錯，引用了 team-fouls，回答開頭還帶著 id。我把這些情況回報給 Claude Code 分析
- 也注意到這是兩種不同的問法：情境題（某個情況會不會違例）和名詞解釋題（某個規則是什麼），後者需要題庫答案裡有定義句

**驗證方式**
- `uv run ruff check .`：All checks passed；`uv run pytest -q`：112 passed

## M5 補充：依 Jimmy 試跑結果修正（2026-10-27）

**起因**：Jimmy 自己用 `faq.answer` 試了 3 題，發現「什麼是走步」只回答步數規則、沒有解釋名詞；「什麼是進攻犯規」完全答錯（引用 team-fouls，回答開頭還有「team-fouls：」）

**Claude Code 分析與修正**
- 「什麼是走步」：模型照抄 travelling 答案的前兩句，因為題庫答案本身沒有定義句 → 在答案開頭補「走步是指持著活球時，腳的移動超出規則允許的範圍」（Art. 25.1.1），改回 draft
- 「什麼是進攻犯規」：題庫沒有這題，檢索前 3 名（投籃犯規、團隊犯規、24 秒）都不相關，但分數 0.64 以上超過門檻 → 新增 `offensive-foul` 草稿（Art. 33.8 撞人、Art. 42.2.2 控球方犯規由對方發球）
- 程式端：guard 會先拿掉回答開頭的「id：」或「id（條號）：」
- 測試查詢加入「請告訴我什麼是走步」「請告訴我什麼是進攻犯規」

**AI 寫錯的規則（Claude Code 自己起草、Jimmy 已審成 verified 的題目）**
- `throw-in-foul` 寫成「發界外球時發生的犯規只罰 1 球」，漏掉 Art. 34.1.2 的條件：**只有第四節和延長賽最後 2 分鐘內**才算 throw-in foul。查規則書回答 Jimmy 的問題時才發現，已修正並改回 draft

**驗證方式**
- `uv run pytest -q`：115 passed
- 重建 45 題索引，27 條查詢：Hit@1 17/24、Hit@3 22/24；門檻 0.50 時題庫內誤拒 0、題庫外拒答 2/3
- 重跑 Jimmy 的 3 題：三題都引用正確，「什麼是走步」先給定義，「什麼是進攻犯規」檢索第 1 名 offensive-foul 0.900
- 副作用：「快攻的時候故意從後面拉人」的第 1 名從 disruptive-foul 變成 offensive-foul（0.513 vs 0.473），Hit@1 少 1 條

**Jimmy 修改或否決了什麼**
- 依我的試跑結果，請 Claude Code 補 travelling 的定義句、新增 offensive-foul、去掉回答開頭的 id，修正後重跑 3 題都答對
- 對照 Art. 34.1.2，確認 throw-in-foul 原本漏了「最後 2 分鐘」條件；這題我之前審核時也沒發現

## M6 結果與加分（2026-10-27）

**工具**：Claude Code（Claude Opus 5.5）

**Claude Code 做了什麼**
- `faq/report.py`：跑 27 條測試查詢 → 算 Hit@1、Hit@3、題庫外拒答、題庫內誤拒 → 輸出 `site/data/results.json` 與 `site/similarity.png`（測試查詢 × 45 題的相似度熱圖，藍框標期望答案）；加 `--answers` 會另外跑 `answer.py`，統計模型回答被採用、出處正確、guard 擋下的數量
- `tests/test_report.py`：用手寫的檢索結果測統計函式，不呼叫模型
- `Dockerfile`（參考 Lab 4：multi-stage、相依分層快取、非 root 使用者 `app`）、`.dockerignore`、`compose.yaml`（Ollama ＋ 命令列 app，沿用課程的 `ollama` volume，`./data` 掛載回主機）
- 修正：回答開頭「id」後面接換行時也會被拿掉
- 本地 vs 雲端比較表：Jimmy 決定先不做（不想花錢，也避免金鑰外洩被扣 20 分）

**結果**（本機 qwen3-embedding:0.6b ＋ qwen3:1.7b）
- 檢索：Hit@1 17/24（71%）、Hit@3 22/24（92%）；門檻 0.50：題庫內誤拒 0、題庫外拒答 2/3
- 模型回答：題庫內採用 19（出處正確 17）、guard 擋下 5、拒答 0；題庫外拒答 2/3；平均 14.1 秒
- 已知問題：「排球一局打到幾分」檢索分數 0.561 過了門檻，模型也照答（第一輪 M5 時模型曾拒答，可見每輪會有差異）；「傳球傳太大力…」模型回答只有一個英文字「context」，guard 沒擋到（不是 id，長度也夠）

**驗證方式**
- `uv run ruff check .`：All checks passed；`uv run pytest -q`：119 passed
- 看過熱圖：中文字型正常，大部分藍框是該列最紅的格子
- `docker compose build app`：映像檔 327 MB，`id` 顯示 uid=999(app)；`docker compose run --rm app faq.build_index`、`faq.answer`、`faq.ask` 在容器內都正常，題庫外問題正確拒答
- `grep -r "sk-|AIza|sk-ant" site/`：沒有金鑰

**Jimmy 修改或否決了什麼**
- 決定不做本地 vs 雲端比較表；加分項改靠 Dockerfile／compose 和 CI 跑 pytest

## M7 作品頁與文件（2026-10-27）

**工具**：Claude Code（Claude Opus 5.5）

**Claude Code 做了什麼**
- `site/index.html`：四區塊（做了什麼／怎麼執行／執行結果／AI 使用說明）＋參考資料。執行結果用 JS 讀 `data/results.json` 畫整體指標、27 條查詢的 top-3 表格、6 條代表性的模型回答（其餘收在「看全部」），並放熱圖與已知限制
- AI 使用說明表格的「我自己修改或驗證了什麼」只從本檔 Jimmy 寫的段落整理，沒有另外加內容；另列「AI 或舊資料寫錯、被抓出來的地方」
- `README.md`：功能、安裝與執行（PowerShell）、執行範例、結果、專案結構、AI 使用說明、參考資料，加上 CI／Pages 徽章

**驗證方式**
- 在本機用 `python -m http.server` 開 site/ 預覽：results.json 讀取正常（指標 10 列、查詢 27 列、回答 6＋27 列），熱圖載入，console 沒有錯誤
- 手機寬度 375px：整頁不會橫向捲動；發現查詢表格第一欄被擠成一字一行，加上最小寬度後改成表格內左右捲動
- 一開始我把 M6「不做比較表」的理由寫成「不想花錢，也避免金鑰外洩」，但 Jimmy 貼的版本沒有這句，已改成只寫 Jimmy 自己寫的內容

**Jimmy 修改或否決了什麼**
- 確認作品頁、README 與 AI 使用說明表格的內容都是我實際做過的事

## M8 繳交前檢查（2026-10-27）

**工具**：Claude Code（Claude Opus 5.5）

**Claude Code 做了什麼**
- 照 CLAUDE.md 第 7 節逐項檢查並打勾，更新 AGENTS.md 的專案結構（拿掉沒做的 `compare.py`，補上 Dockerfile／compose、AI 使用紀錄）

**驗證方式**
- GitHub API：repo `visibility: public`、`has_pages: true`；作品頁回 200
- `git ls-files`：有 `uv.lock`，沒有 `.env`、`.venv`、`data/index.npz`
- `git log -p --all` 搜 `sk-|AIza|sk-ant`：只有 `.env.example` 的 `sk-...` 佔位文字和檢查清單本身；改用金鑰長度的嚴格比對（如 `sk-` 後面 16 字以上）查無結果
- `uv sync --locked --dev`、`uv run ruff check .`、`uv run pytest -q`（119 passed）；CI 與 Deploy Pages 最新一次都是 success
- README 與作品頁裡的外部連結都回 200
- 從 GitHub 重新 clone 到暫存資料夾，`uv sync --locked --dev` 後 pytest 通過，確認沒有依賴本機才有的檔案

**Jimmy 修改或否決了什麼**
- （待填）
