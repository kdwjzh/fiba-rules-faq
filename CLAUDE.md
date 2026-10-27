@AGENTS.md

# 交接說明（給 Claude Code）

> 撰寫：2026-10-26。作者 Jimmy（學生）。截止：**2026-11-08（日）23:59**。
> 每次開始工作先讀這份；做完一個里程碑就更新第 8 節「進度紀錄」。

---

## 1. 這是什麼作業（老師的規定，不可違反）

課程「設計機器學習平台與系統架構」第 6 週個人作業「**AI 小專案上線**」，佔學期 **30%**。
題目：自選主題，用 **Python** 寫一支**呼叫 LLM** 的小程式，放上 **GitHub**，再用 **Actions** 發布**作品頁**。可以用 AI 輔助。

### 四項必要交付
| # | 交付 | 要求 |
|---|---|---|
| ① | GitHub repo | **Public**；有 **README** 與 **.gitignore**；**至少 5 個 commit** |
| ② | AI 程式 | **Python（uv）**呼叫本地 Ollama 或雲端模型；**至少用到** 串流／結構化輸出／工具呼叫／embedding **其中一種**（本專案：embedding ＋ 結構化輸出） |
| ③ | GitHub Actions | 至少一個 workflow，**由 Actions 自動部署 GitHub Pages**（Settings → Pages 的 Source 必須是 **GitHub Actions**，不是 branch） |
| ④ | GitHub Pages | 作品頁必須有四項：**做了什麼、怎麼執行、執行結果、AI 使用說明** |

### 評分（滿分 100，各項分優／良／可／待加強 = 100%／80%／60%／30%）
| 項目 | 配分 | 滿分標準 |
|---|---|---|
| repo 與 README | 20 | 結構清楚；README 寫明功能與執行步驟；commit ≥ 5 |
| AI 程式功能 | 30 | 能正常執行；至少用到 W6 一種能力；輸出結果合理 |
| GitHub Actions | 20 | workflow 綠燈，Pages 由 Actions 自動部署 |
| Pages 作品頁 | 20 | 四項齊全，排版清楚易讀 |
| AI 使用說明 | 10 | 用了什麼工具、用在哪裡、自己修改或驗證了什麼 |
| 加分 | 最多 +10（總分上限 100） | 附 Dockerfile 或 compose；Actions 加 pytest；本地 vs 雲端比較表 |
| **扣分** | **−20** | **金鑰推上 GitHub（含 commit 歷史）** |

繳交：在 iLearn 交 **repo 網址＋Pages 網址**。遲交每天扣 10%。

---

## 2. 已經做好的決定（不要再改，除非 Jimmy 要求）

- **主題**：籃球規則 FAQ 查詢，規則體系只用 **FIBA Official Basketball Rules 2026（v1.1，2026-10-01 生效）**
  - 規則書 PDF：https://assets.fiba.basketball/image/upload/documents-corporate-fiba-official-rules-2026-v1-1.pdf
  - 2026 修改摘要：https://assets.fiba.basketball/image/upload/documents-corporate-fiba-official-rules-2026-rule-changes-v10a.pdf
  - 不要混入 NBA／NCAA 規則；若要做「FIBA vs NBA」比較題，必須標清楚出處
- **核心能力**：embedding（必做）＋ 結構化輸出（加強版）
- **模型**：本地 Ollama，embedding 用 `qwen3-embedding:0.6b`，回答用 `qwen3:1.7b`（記憶體不足改 `qwen3:0.6b`）。雲端只用於比較表，非必要
- **題庫規模**：40–50 題，先做 10 題驗證流程再擴充

### 版權與內容規則（很重要）
- FIBA 網站與規則書為「© FIBA All rights reserved」。**不可把規則書原文整段複製進 repo**
- 答案用自己的話寫，每題附條號（例：`FIBA OBR 2026 Art. 29`），作品頁放規則書連結
- **答案由 Jimmy 撰寫或審核**。Claude Code 可以：提出題目清單、整理條號、起草答案；但自己起草的答案一律 `"status": "draft"`，並在回覆中提醒 Jimmy 對照 PDF 核對後改成 `"verified"`
- 2026 版有改動，舊中文資料常過時，起草時特別注意：
  - 「違反運動道德犯規」（unsportsmanlike）已取消，改為 disruptive foul（不計入取消資格）與 flagrant foul（計入取消資格）；中文譯名以中華民國籃協公布為準，未確定前保留英文
  - 技術犯規分為計入／不計入取消資格兩類
  - Art. 15 投籃動作的定義修改；IRS（重播）可檢視範圍擴大
- 條號以 2026 v1.1 為準；2024 版的對照（Art. 25 走步、26 三秒、28 八秒、29 二十四秒、40 五次犯規）只能當線索，要核對

---

## 3. 技術設計

### 題庫格式 `data/faq.json`
```json
[
  {
    "id": "shot-clock",
    "question": "進攻時間是幾秒？超過會怎樣？",
    "aliases": ["24 秒", "shot clock", "進攻計時器"],
    "answer": "（自己的話，2–4 句）",
    "example": "（選填：情境例子）",
    "category": "違例",
    "source": "FIBA OBR 2026 Art. 29",
    "status": "draft"
  }
]
```
- `category` 限定：`比賽基本`、`違例`、`犯規`、`罰則`、`比賽管理`、`2026 新制`
- 算 embedding 的文字 = `question + aliases + answer`（`store.py` 提供 `doc_text(item)` 組字串）

### 測試查詢 `data/test_queries.json`
```json
[{"query": "拿球走三步會怎樣", "expected": ["travelling"]}]
```
口語、不用原題目字眼。至少 10 條，其中 2 條是題庫沒有的（`expected: []`），用來測門檻。

### 流程
1. `build_index`：讀 faq.json → 呼叫 embedding（`client.embeddings.create`）→ 正規化 → 存 `data/index.npz`（vectors＋ids＋題庫的 hash；題庫變更時提示重建）
2. `ask`：問題 → embedding → `store.top_k(query_vec, vectors, k=3)` → 若最高分 < `THRESHOLD`（先設 0.5，用測試查詢調整）就回「題庫沒有相關規則」
3. `answer`（加強版）：把 top-3 交給 `qwen3:1.7b`，用 `client.chat.completions.parse` + Pydantic：
   ```python
   class RuleAnswer(BaseModel):
       answer: str            # 100 字內
       source_ids: list[str]  # 只能是 top-3 的 id
       confidence: Literal["高", "中", "低"]
   ```
   system prompt 要求只根據提供的 FAQ 回答；程式端檢查 `source_ids` ⊆ top-3 的 id
4. `report`：跑 `test_queries.json` → 算 **Hit@1、Hit@3、拒答正確率** → 輸出 `site/data/results.json` 與 `site/similarity.png`（熱圖：測試查詢 × 題庫，matplotlib 字型用 `Microsoft JhengHei`, `Noto Sans CJK TC`）
5. `compare`（加分）：同樣的查詢比本地 vs 雲端的延遲、token、費用 → `site/data/compare.json`

### `faq/llm.py`（改自課程 Lab 5，修掉已知問題）
- 保留 `get_llm(profile)` 與 `PRESETS`、`cost_usd()` 的設計
- **修正**：雲端 profile 的模型名稱**不可** fallback 到 `LLM_MODEL`（Lab 5 原版會把 `qwen3:0.6b` 拿去打雲端導致 404）。順序改為 `{PROFILE}_MODEL` → `PRESETS`；只有 `local` 才讀 `LLM_MODEL`
- 新增 `EMBED_MODEL`（預設 `qwen3-embedding:0.6b`）
- `PRICES` 要包含實際使用的雲端模型，否則費用顯示 0
- `load_dotenv()` 讀 `.env`；本地金鑰用 `"ollama"`

### 相依
- 一般：`openai`、`python-dotenv`、`numpy`
- dev：`pytest`、`ruff`、`matplotlib`
- `uv.lock` 必須 commit

### 作品頁 `site/`
- `index.html`：純 HTML＋少量 JS（fetch `data/results.json` 畫表格），手機可讀，**四個區塊標題就用「做了什麼／怎麼執行／執行結果／AI 使用說明」**，另加「參考資料」
- 執行結果在 Jimmy 本機產生後 commit（Pages 是靜態的，Actions 沒有模型也沒有金鑰）
- 頁尾註明：規則以 FIBA 官方規則書為準，本工具僅供學習查詢

### workflows
- `pages.yml`：`on: push (main) + workflow_dispatch`；permissions `contents: read`、`pages: write`、`id-token: write`；`actions/checkout` → `actions/configure-pages` → `actions/upload-pages-artifact`（path: `site`）→ `actions/deploy-pages`。建立前查一下這幾個 action 的目前主版本
- `ci.yml`：`actions/checkout` → `astral-sh/setup-uv`（python 3.12）→ `uv sync --locked --dev` → `uv run ruff check .` → `uv run pytest -q`

### 測試（`tests/`，不可呼叫模型）
- `test_store.py`：用手做的 3–4 維向量測 cosine、top-k 排序、門檻拒答
- `test_faq_data.py`：題庫 schema 檢查（必要欄位、id 不重複、category 合法、source 以 `FIBA OBR 2026 Art.` 開頭）
- `test_answer_guard.py`：`source_ids` 不在 top-3 時被擋下（測檢查函式，不打模型）

---

## 4. 環境（Jimmy 的電腦）

- Windows 10/11、PowerShell、Docker Desktop（WSL 2）、uv、Git
- 課程用過的 Docker volume `ollama` 裡可能已有 qwen3 模型。啟動 Ollama：
  ```powershell
  docker run -d --name ollama -p 127.0.0.1:11434:11434 -v ollama:/root/.ollama ollama/ollama
  docker exec ollama ollama pull qwen3-embedding:0.6b
  docker exec ollama ollama pull qwen3:1.7b
  curl.exe http://127.0.0.1:11434/v1/models
  ```
- 參考程式（唯讀，不要修改）：`D:\2026_設計機器學習平台與系統架構\第6週_Lab5_範例程式\`（`agent/llm.py`、`labs/w06/s3_structured.py`、`s5_embeddings.py`、`s6_compare.py`）
- 專案路徑用英文，避免中文路徑出錯；`.gitattributes` 設 `* text=auto eol=lf`

---

## 5. 執行步驟與里程碑（依序做，每個里程碑至少一個 commit）

| # | 里程碑 | 完成條件 | 建議日期 |
|---|---|---|---|
| M0 | repo 初始化 | GitHub 建 **Public** repo `fiba-rules-faq`；`git init`／設 remote；先 commit `.gitignore`（`.env`、`.venv/`、`__pycache__/`、`data/index.npz`）、`.gitattributes`、`AGENTS.md`、`CLAUDE.md`、`.env.example` | 10/26 |
| M1 | Pages 先上線 | `site/index.html`（四區塊空殼）＋ `pages.yml`；Jimmy 到 Settings → Pages 選 GitHub Actions；Actions 綠燈、網址打得開 | 10/26–27 |
| M2 | 骨架＋CI | `uv init`、相依、`faq/` 套件、`store.py` + `tests/`、`ci.yml` 綠燈 | 10/27–28 |
| M3 | 10 題跑通 | 10 題題庫（draft 可）、`build_index`、`ask` 能正確找到；10 條測試查詢 | 10/28–29 |
| M4 | 擴充題庫 | 40–50 題，Jimmy 審核後 `verified` ≥ 40；測試查詢 ≥ 15 | 10/30–11/02 |
| M5 | 加強版 | 門檻拒答、`answer.py` 結構化回答＋guard | 11/02–03 |
| M6 | 結果與加分 | `report` 產出 Hit@1/Hit@3、熱圖；`compare`（若 Jimmy 有雲端金鑰）；Dockerfile（multi-stage、非 root，參考 Lab 4） | 11/03–05 |
| M7 | 作品頁與文件 | 作品頁四項＋參考資料；README（功能、安裝、執行步驟、截圖）；AI 使用說明 | 11/06–07 |
| M8 | 繳交前檢查 | 第 7 節清單全打勾；Jimmy 在 iLearn 繳交 | 11/07–08 |

---

## 6. AI 使用說明素材（邊做邊記，M7 時整理）

作品頁與 README 都要放一個表格：**用了什麼工具｜用在哪裡｜我自己修改或驗證了什麼**。
Claude Code 每完成一個里程碑，把以下內容追加到 `docs/ai-usage-log.md`（這個檔要 commit）：
- 這次 Claude Code 做了什麼（產生哪些檔案）
- Jimmy 修改或否決了什麼
- 驗證方式（跑了哪些指令、對照了哪條規則、發現什麼錯）
特別記錄：AI 或舊資料寫錯的規則（例如仍用「違反運動道德犯規」）、條號對不上的地方。

---

## 7. 繳交前檢查清單
- [ ] repo 是 Public；README 有功能與執行步驟
- [ ] `git log --oneline` ≥ 5 個 commit（GitHub 自動產生的 Initial commit 不算進去比較保險）
- [ ] `uv.lock` 已 commit；`git status` 看不到 `.env`、`.venv`
- [ ] **整個歷史沒有金鑰**：`git log -p | Select-String "sk-|AIza|sk-ant"` 查無結果
- [ ] ruff、pytest 通過；`ci.yml`、`pages.yml` 最新一次都是綠燈
- [ ] Settings → Pages 的 Source 是 GitHub Actions；網址打得開
- [ ] 作品頁四項：做了什麼／怎麼執行／執行結果／AI 使用說明，加上參考資料
- [ ] 題庫答案都是自己的話、都有 2026 條號、`verified` ≥ 40
- [ ] 加分：Dockerfile、CI 跑 pytest、比較表（有做的打勾）
- [ ] iLearn 填了 repo 網址＋Pages 網址，時間在 11/08 23:59 前

---

## 8. 進度紀錄（Claude Code 每次做完更新）

| 日期 | 里程碑 | 狀態 | 備註 |
|---|---|---|---|
| 2026-10-26 | — | 交接說明建立 | 尚未建立 GitHub repo |
| 2026-10-26 | M0 | 完成 | git init、remote 設好；`.gitignore`／`.gitattributes`／`.env.example`／`docs/ai-usage-log.md` 已 commit。repo 已確認 Public；第一次 push 實際未成功，M1 時一起 push |
| 2026-10-26 | M1 | 完成 | `site/index.html` 四區塊空殼＋`pages.yml`（checkout@v7、configure-pages@v6、upload-pages-artifact@v5、deploy-pages@v5）。Deploy Pages 綠燈；作品頁 https://kdwjzh.github.io/fiba-rules-faq/ 可開啟 |
| 2026-10-27 | M2 | 完成 | 用 winget 裝 uv 0.13.6；`pyproject.toml`＋`uv.lock`、`faq/store.py`、`faq/llm.py`（修 Lab 5 雲端 fallback）、`tests/test_store.py`（9 passed）、`ci.yml` 綠燈。`PRICES` 尚缺 `gemini-3.8-flash` |
| 2026-10-27 | M3 | 完成 | 10 題（Jimmy 已改 verified；條號對照 2026 v1.1，五犯是 Art. 41）、12 條測試查詢、`build_index`、`ask`、`test_faq_data.py`。Ollama 跑在 Docker；查詢加 Qwen3 instruction 後 Hit@1 7/10、Hit@3 10/10，門檻改 0.45 |
| 2026-10-27 | M4 | 完成 | 題庫 44 題全部 verified（Jimmy 審核）、測試查詢 25 條；Hit@1 16/22、Hit@3 20/22；門檻改 0.50（誤拒 1/22、題庫外拒答 2/3） |
| 2026-10-27 | M5 | 完成 | `answer.py`：門檻拒答＋qwen3:1.7b 結構化回答＋guard（id ⊆ top-3、≤100 字、不可只有 id、低信心拒答），沒通過改顯示題庫答案。最後一輪：題庫外 3/3 拒答，模型回答採用 13/22（引用正確 10）。思考模式只能用 `reasoning_effort="none"` 關，但品質較差所以保留 |
| 2026-10-27 | M5 補充 | 完成 | 依 Jimmy 試跑：travelling 補定義句、新增 offensive-foul、修正 throw-in-foul（漏 Art. 34.1.2 最後 2 分鐘條件），這 3 題為 draft；回答去掉 id 前綴；測試查詢 27 條，Hit@1 17/24、Hit@3 22/24 |
| 2026-10-27 | M6 | 完成 | `report.py`＋`site/data/results.json`＋`site/similarity.png`：Hit@1 17/24、Hit@3 22/24、誤拒 0、題庫外拒答 2/3；模型回答採用 19（出處正確 17）、guard 擋 5。Dockerfile（multi-stage、非 root）＋compose 測過。比較表 Jimmy 決定不做。注意：Ollama 現在由 compose 啟動（`docker compose up -d ollama`），原本手動的 `ollama` 容器已停止 |
| 2026-10-27 | M7 | 完成（待 Jimmy 看過） | 作品頁四區塊＋參考資料（結果由 results.json 動態產生、熱圖、回答範例、已知限制、AI 使用說明表格與 AI 寫錯清單）；README 完成。手機 375px 檢查過 |
