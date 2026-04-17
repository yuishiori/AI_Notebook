# 個人 AI 工作助理系統 — 系統設計規格書

> **System Design Specification**

| 項目 | 內容 |
|---|---|
| 文件版本 | v1.0 |
| 文件日期 | 2026-04-17 |
| 專案代號 | Personal-AI-Assistant |
| 作者 | ChiuYu (yuishiori@gmail.com) |
| 部署環境 | Windows 11 / 本機執行 |
| 文件狀態 | 初版 |

---

## 目錄

1. [系統概述](#1-系統概述)
2. [使用者與使用情境](#2-使用者與使用情境)
3. [功能需求](#3-功能需求)
4. [非功能需求](#4-非功能需求)
5. [系統架構](#5-系統架構)
6. [技術選型](#6-技術選型)
7. [資料模型](#7-資料模型)
8. [API 設計](#8-api-設計)
9. [前端設計](#9-前端設計)
10. [RAG 與 LLM 推論流程](#10-rag-與-llm-推論流程)
11. [排程與背景服務](#11-排程與背景服務)
12. [部署與目錄配置](#12-部署與目錄配置)
13. [開發里程碑](#13-開發里程碑)
14. [風險與對策](#14-風險與對策)
15. [附錄：Tool Use 函數簽章](#15-附錄tool-use-函數簽章)

---

## 1. 系統概述

### 1.1 系統目的

本系統為一套運行於本機環境的個人 AI 工作助理，主要用途為輔助使用者整理每日工作內容、根據既有背景知識撰寫每週工作週報、主動提醒到期專案並分析工作分配是否合理。系統採用 **Google Gemini API** 作為 LLM 推論引擎，搭配 RAG（Retrieval-Augmented Generation）機制檢索個人知識庫，以提供具備上下文理解能力的個人化輸出。所有與 Gemini API 相關的金鑰與參數皆透過 `.env` 檔案集中管理。

### 1.2 設計原則

- **本機優先**：所有個人資料、知識庫、對話歷史皆儲存於本機，不外洩至第三方。
- **雙環境分離**：公司電腦與家用電腦為獨立部署，不進行跨裝置同步。
- **常駐服務**：後端採用常駐背景服務 + UI 架構，以支援每日 08:00 定時 Briefing。
- **對話式互動**：主介面以聊天 UI 為核心，LLM 具備 Tool Use 能力以主動讀寫資料庫。
- **工作區隔離**：以「工作」、「生活」為獨立 Workspace，各自擁有專屬知識庫與對話歷史。

### 1.3 系統範圍

系統範圍涵蓋：知識庫匯入與管理、RAG 檢索、專案與工作日誌管理、對話式 AI 助理、週報產生與對話式修改、每日 Briefing 排程，以及桌面應用程式封裝。

**不在本次範圍內**：跨裝置同步、多使用者協作、雲端備份、語音輸入與 OCR。

---

## 2. 使用者與使用情境

### 2.1 使用者角色

本系統為單使用者系統，無多使用者權限設計。使用者同時扮演管理員與終端使用者兩種角色。

### 2.2 典型使用情境

#### 情境一：每日 Briefing（早上 08:00）

使用者於早上開機後，系統背景服務於 08:00 自動觸發 Briefing 流程，App 視窗自動彈出並在對話區顯示當日 Briefing 摘要，包含：快到期專案、昨日工作摘要、未更新進度之專案提醒、AI 對今日規劃的建議。同時系統會將 Briefing 以 `.txt` 形式存檔備查。

#### 情境二：知識庫維護

使用者手動匯入個人筆記（txt / md）、公司 PPT 文件、純文字會議記錄，或貼上 URL 讓系統抓取網頁內容並解析。所有知識以「專案」為單位分類並存入 ChromaDB。

#### 情境三：日常對話整理

使用者於 Chat UI 內以自然語言描述當日工作內容，例如「今天完成了 A 專案的 API 設計並與 PM 開了兩場會」。LLM 透過 Tool Use 能力自動建立工作日誌記錄，並在使用者未指定 KPI 時推論出合適的 KPI 項目。

#### 情境四：週報產出（週五）

使用者指示「幫我產生本週週報」，系統依據週一至週五的工作日誌、專案背景與 KPI 資料產出草稿（`.txt` 格式，結構為 Background → 本週事項與 KPI → 總結），使用者可於對話中以自然語言修改草稿直到滿意為止。

#### 情境五：家用記錄生活瑣事

使用者於家用電腦切換至「生活」Workspace，系統載入獨立的知識庫與對話歷史，記錄生活相關內容而與工作資料完全隔離。

---

## 3. 功能需求

### 3.1 功能清單總覽

| 編號 | 功能名稱 | 優先級 |
|---|---|---|
| FR-01 | Workspace 管理（工作 / 生活） | P0 |
| FR-02 | 知識庫匯入與管理（PPT / txt / md / URL / 會議記錄） | P0 |
| FR-03 | RAG 檢索（ChromaDB + bge-m3 embedding） | P0 |
| FR-04 | 專案管理（CRUD、到期日、狀態） | P0 |
| FR-05 | 工作日誌記錄（以週為單位） | P0 |
| FR-06 | KPI 管理（AI 推論 + 人工覆寫） | P0 |
| FR-07 | 對話式 AI 介面（多 Workspace、多輪記憶） | P0 |
| FR-08 | LLM Tool Use（主動讀寫資料庫） | P0 |
| FR-09 | 週報草稿產生與對話式修改 | P0 |
| FR-10 | 每日 08:00 Briefing 排程 | P0 |
| FR-11 | 專案到期自動提醒 | P0 |
| FR-12 | 工作分配分析與建議 | P1 |

### 3.2 功能詳細說明

#### FR-01 Workspace 管理

- 系統提供「工作」與「生活」兩個預設 Workspace，使用者可切換當前工作區。
- 每個 Workspace 擁有獨立的專案清單、知識庫向量集合、工作日誌與對話歷史。
- Workspace 切換時，前端需重新載入對應的側邊欄資料與對話記錄。

#### FR-02 知識庫匯入

- 支援格式：`.pptx`、`.txt`、`.md`、網頁 URL、純文字會議記錄。
- **PPT 解析**：使用 python-pptx 抽取每張投影片的文字與備註。
- **URL 抓取**：使用 `requests` + `readability-lxml` / `trafilatura` 擷取主文內容。
- **分類**：每筆知識須指定所屬 Workspace 與「專案」標籤。
- **分塊**：以 500~800 tokens 為一 chunk，overlap 100 tokens，存入 ChromaDB。

#### FR-03 RAG 檢索

- **向量資料庫**：ChromaDB（Persistent Client，本機檔案儲存）。
- **Embedding 模型**：`BAAI/bge-m3`（中英文雙語表現佳，支援長文本）。
- **檢索策略**：依 Workspace + 專案 metadata 過濾後進行 Top-K 向量相似度檢索（K=5），必要時以 BM25 做混合檢索。
- 檢索結果會作為 context 注入到 LLM 的 system prompt。

#### FR-04 專案管理

每個專案至少包含以下欄位：

- 專案 ID、名稱、描述（Background）、所屬 Workspace
- 狀態（進行中 / 暫停 / 完成）、開始日期、到期日
- KPI 清單（多筆，支援 AI 推論與人工輸入）
- 最近更新時間（用於「未更新提醒」）
- 標籤與關聯知識庫 chunks

#### FR-05 工作日誌

- 以「週」為單位組織，每筆日誌關聯至某個專案。
- 可由使用者手動輸入，或由對話中 LLM 透過 Tool Use 自動建立。
- 欄位：日誌 ID、週次、日期、專案 ID、內容、對應 KPI、建立時間。

#### FR-06 KPI 管理

- AI 根據工作日誌內容推論 KPI（例如「完成 API 設計」→「API 設計完成度 100%」）。
- 保留人工編輯介面，使用者可覆寫或新增自訂 KPI。
- KPI 需可量化或階段化，以便週報中呈現。

#### FR-07 對話式介面

- 類似 ChatGPT 的左側會話列表 + 右側對話主視窗。
- 支援 Streaming 顯示（若 API 提供）。
- 每個 Workspace 擁有獨立對話歷史，對話可命名、釘選、刪除。
- 對話歷史以 SQLite 儲存；每次推論時取最近 N 輪 + RAG context 組裝 prompt。

#### FR-08 LLM Tool Use

LLM 具備主動呼叫下列工具的能力（Function Calling 格式）：

- `create_work_log(project_id, date, content, kpi)`
- `update_project_status(project_id, status, progress)`
- `search_knowledge(query, workspace, project)`
- `list_projects(workspace, filter)`
- `generate_weekly_report(workspace, week)`
- `set_project_due_date(project_id, due_date)`

#### FR-09 週報產生

- **觸發方式**：使用者於對話中輸入指令或點擊「產生本週週報」按鈕。
- **範圍**：當週週一至週五。
- **輸出格式**：`.txt`，結構固定為：Background → 本週事項與對應 KPI → 總結。
- **草稿模式**：產出後於對話區顯示，使用者可以自然語言要求修改（如「第二段太長請縮短」），LLM 逐輪改寫直到使用者確認。
- 最終版本儲存於 `./reports/` 目錄並於資料庫建立 report 記錄。

#### FR-10 每日 Briefing

- **觸發時間**：每日 08:00（可於設定中調整）。
- **觸發方式**：後端常駐服務內的 APScheduler 排程。
- **行為**：呼叫 LLM 組合 Briefing 內容 → 透過 WebSocket 推送給前端 → 前端自動彈出 App 視窗並以系統訊息形式顯示於對話區 → 同時以 `.txt` 存檔至 `./briefings/`。

Briefing 內容組成：

- 今天要關注的專案（依到期日升冪排序，取 7 日內到期者）
- 昨天的工作摘要（取昨日工作日誌）
- 未更新進度的專案提醒（`last_update > 3 天`者）
- AI 對今日規劃的建議（基於上述資料由 LLM 產出）

#### FR-11 專案到期提醒

- 系統掃描所有進行中的專案，若距到期日 ≤ 3 天則標記為「即將到期」。
- 若某專案未設定到期日，系統於 Briefing 中提示「專案 X 尚未設定到期日，請補上」。

#### FR-12 工作分配分析

- LLM 根據當週工作日誌分析各專案的時間分配比例。
- 若某專案超過 7 天沒有任何工作日誌，於 Briefing 中提示使用者是否遺漏。
- 提供工作量是否過度集中的建議。

---

## 4. 非功能需求

| 類別 | 需求 |
|---|---|
| 效能 | 對話回應首字延遲 < 2 秒（依公司 API 實際延遲）；RAG 檢索 < 500 ms。 |
| 可用性 | 常駐服務需於 Windows 開機後自動啟動，不需手動執行。 |
| 資料安全 | 純本機儲存，不加密；不設應用程式密碼。 |
| 可維護性 | 前後端分離，API 以 OpenAPI 文件自動產生。 |
| 擴充性 | Tool Use 介面可註冊新工具，不需修改主流程。 |
| 在地化 | UI 採繁體中文；LLM 輸出依使用者語言自動適應。 |
| 備份 | SQLite 與 ChromaDB 目錄可由使用者手動複製；不提供自動備份。 |

---

## 5. 系統架構

### 5.1 整體架構

系統採用「前後端分離 + 本機常駐服務」架構，透過 Tauri 打包為桌面應用程式。後端 FastAPI 服務於 Windows 啟動時透過任務排程常駐，前端透過 HTTP + WebSocket 與後端通訊。

### 5.2 架構分層

| 層級 | 元件 | 職責 |
|---|---|---|
| 呈現層 | React + Vite + TypeScript + TailwindCSS | Chat UI、Workspace 切換、專案/日誌管理介面 |
| 通訊層 | HTTP REST + WebSocket | 一般 CRUD 用 REST；對話 streaming 與 Briefing 推播用 WebSocket |
| 應用層 | FastAPI (Python 3.11) | API 路由、業務邏輯、Tool Use 分派、週報與 Briefing 流程 |
| 排程層 | APScheduler | 每日 08:00 Briefing、過期掃描 |
| 推論層 | Gemini API Client (HTTPS POST) | 呼叫 Google Gemini API，金鑰讀自 `.env` |
| 資料層 | SQLite + ChromaDB | 結構化資料（SQLite）與向量資料（ChromaDB） |
| 封裝層 | Tauri | 桌面應用打包與系統常駐 |

### 5.3 架構圖

```
┌─────────────────────────────────────────────┐
│  Tauri Desktop App (Windows 11)             │
│  ┌───────────────────────────────────────┐  │
│  │  React Chat UI (WebView)              │  │
│  └──────────────┬────────────────────────┘  │
│                 │ HTTP + WebSocket           │
│  ┌──────────────▼────────────────────────┐  │
│  │  FastAPI  (127.0.0.1:8765)            │  │
│  │  ├── REST API                          │  │
│  │  ├── WebSocket /ws/chat, /ws/briefing │  │
│  │  ├── Tool Dispatcher                   │  │
│  │  └── APScheduler (08:00 Briefing)      │  │
│  └──┬───────────┬────────────┬───────────┘  │
│     │           │            │              │
│  ┌──▼──┐  ┌─────▼────┐  ┌────▼─────────┐   │
│  │SQLite│ │ChromaDB  │  │Gemini API    │   │
│  │(app  │ │(vectors +│  │(HTTPS POST,  │   │
│  │ .db) │ │ bge-m3)  │  │ .env key)    │   │
│  └──────┘ └──────────┘  └──────────────┘   │
└─────────────────────────────────────────────┘
```

---

## 6. 技術選型

| 類別 | 技術 | 理由 |
|---|---|---|
| 後端語言 | Python 3.11 | 生態豐富，ChromaDB/python-pptx/trafilatura 原生支援 |
| 後端框架 | FastAPI | 型別安全、OpenAPI 自動產生、async 支援 streaming |
| 關聯資料庫 | SQLite | 零依賴、本機單檔、適合單使用者場景 |
| ORM | SQLAlchemy 2.0 + Alembic | 型別明確、遷移管理成熟 |
| 向量資料庫 | ChromaDB (PersistentClient) | 純 Python、本機檔案儲存、metadata 過濾方便 |
| Embedding | BAAI/bge-m3 | 中英文雙語、長文本、本機可跑 |
| LLM | Google Gemini API (HTTPS POST) | 原生支援 function calling / streaming；金鑰由 `.env` 讀取 |
| 設定管理 | pydantic-settings + python-dotenv | 集中管理 `.env` 變數、型別驗證、啟動時檢查缺漏 |
| 排程 | APScheduler | 與 FastAPI 整合佳、支援 cron 與 interval |
| 前端框架 | React 18 + TypeScript | 成熟生態、型別安全 |
| 建構工具 | Vite | 開發伺服器快速、打包輕量 |
| UI 元件 | shadcn/ui + Radix + TailwindCSS | 可組裝、無障礙、客製化高 |
| 狀態管理 | Zustand | 輕量、適合中型應用 |
| 桌面封裝 | Tauri 2.x | 輕量（相較 Electron）、Rust 後端、Windows 安裝檔支援 |
| 啟動方式 | Windows 工作排程器（登入時） | 確保開機後背景服務常駐 |

---

## 7. 資料模型

### 7.1 SQLite Schema

#### workspaces

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | TEXT PK | UUID |
| name | TEXT | 工作 / 生活 |
| created_at | DATETIME | |

#### projects

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | TEXT PK | UUID |
| workspace_id | TEXT FK | 所屬 Workspace |
| name | TEXT | 專案名稱 |
| description | TEXT | Background / 背景描述 |
| status | TEXT | `active` / `paused` / `done` |
| start_date | DATE | |
| due_date | DATE NULL | 空值代表未設定（會被提醒） |
| last_updated_at | DATETIME | 最後一次新增日誌的時間 |
| created_at | DATETIME | |

#### project_kpis

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | TEXT PK | |
| project_id | TEXT FK | |
| title | TEXT | KPI 描述 |
| target | TEXT | 目標值（可為數值或階段） |
| source | TEXT | `ai_inferred` / `user_defined` |
| created_at | DATETIME | |

#### work_logs

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | TEXT PK | |
| project_id | TEXT FK | |
| workspace_id | TEXT FK | |
| log_date | DATE | 記錄發生日 |
| iso_week | TEXT | `YYYY-Www` 週次 |
| content | TEXT | 工作內容 |
| related_kpi_id | TEXT FK NULL | 對應 KPI |
| source | TEXT | `manual` / `ai_tool` |
| created_at | DATETIME | |

#### conversations

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | TEXT PK | |
| workspace_id | TEXT FK | |
| title | TEXT | 自動依首個訊息摘要 |
| pinned | BOOLEAN | |
| created_at | DATETIME | |
| updated_at | DATETIME | |

#### messages

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | TEXT PK | |
| conversation_id | TEXT FK | |
| role | TEXT | `user` / `assistant` / `tool` / `system` |
| content | TEXT | |
| tool_calls | JSON NULL | function call payload |
| created_at | DATETIME | |

#### knowledge_sources

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | TEXT PK | |
| workspace_id | TEXT FK | |
| project_id | TEXT FK NULL | 可不綁特定專案 |
| type | TEXT | `pptx` / `txt` / `md` / `url` / `meeting` |
| title | TEXT | |
| original_path_or_url | TEXT | |
| imported_at | DATETIME | |

#### reports

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | TEXT PK | |
| workspace_id | TEXT FK | |
| iso_week | TEXT | |
| file_path | TEXT | `.txt` 檔路徑 |
| status | TEXT | `draft` / `finalized` |
| created_at | DATETIME | |
| updated_at | DATETIME | |

#### briefings

| 欄位 | 型別 | 說明 |
|---|---|---|
| id | TEXT PK | |
| workspace_id | TEXT FK | |
| date | DATE | |
| content | TEXT | Briefing 全文 |
| file_path | TEXT | `.txt` 檔路徑 |
| created_at | DATETIME | |

### 7.2 ChromaDB Collections

- Collection 名稱：`kb_{workspace_id}`（每 Workspace 一個集合）
- Metadata 欄位：`source_id`、`project_id`、`type`、`title`、`chunk_index`、`imported_at`
- Embedding：使用 `bge-m3`（維度 1024）

---

## 8. API 設計

所有 API 以 REST 形式提供於 `http://127.0.0.1:8765`；streaming 與推播以 WebSocket `/ws` 提供。

### 8.1 REST API

| 方法 | 路徑 | 說明 |
|---|---|---|
| GET | `/api/workspaces` | 取得 Workspace 清單 |
| POST | `/api/workspaces` | 新增 Workspace |
| GET | `/api/projects?workspace_id=` | 取得專案列表 |
| POST | `/api/projects` | 新增專案 |
| PATCH | `/api/projects/{id}` | 更新專案（狀態 / 到期日 / KPI） |
| DELETE | `/api/projects/{id}` | 刪除專案 |
| GET | `/api/work-logs?project_id=&iso_week=` | 取得工作日誌 |
| POST | `/api/work-logs` | 新增工作日誌 |
| POST | `/api/knowledge/import/pptx` | 上傳 PPT 檔 |
| POST | `/api/knowledge/import/text` | 匯入純文字 / 會議記錄 |
| POST | `/api/knowledge/import/url` | 匯入 URL |
| GET | `/api/conversations?workspace_id=` | 取得對話列表 |
| POST | `/api/conversations` | 新增對話 |
| GET | `/api/conversations/{id}/messages` | 取得訊息 |
| POST | `/api/chat` | 送出訊息（非 streaming 備援） |
| POST | `/api/reports/generate` | 產生本週週報草稿 |
| PATCH | `/api/reports/{id}` | 更新週報內容 |
| GET | `/api/briefings/latest` | 取得最新 Briefing |
| POST | `/api/briefings/trigger` | 手動觸發 Briefing（測試用） |

### 8.2 WebSocket

- `/ws/chat`：客戶端送 `{ conversation_id, message }`，伺服器以 streaming 方式回傳 token 與 tool_call 事件。
- `/ws/briefing`：用於 08:00 Briefing 主動推播至前端。

### 8.3 Gemini API 呼叫

系統呼叫 Google Gemini API 時採用 HTTPS POST，所有連線參數、金鑰與模型名稱皆由 `.env` 載入並經由 `pydantic-settings` 驗證。封裝於 `gemini_client.py`，對上層提供統一介面。

**Endpoint**（非 streaming）：

```
POST {GEMINI_API_BASE_URL}/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}
```

**Endpoint**（streaming）：

```
POST {GEMINI_API_BASE_URL}/models/{GEMINI_MODEL}:streamGenerateContent?alt=sse&key={GEMINI_API_KEY}
```

**Request body 主要欄位**：

```json
{
  "contents": [
    { "role": "user", "parts": [{ "text": "..." }] },
    { "role": "model", "parts": [{ "text": "..." }] }
  ],
  "systemInstruction": { "parts": [{ "text": "system prompt + RAG context" }] },
  "tools": [{ "functionDeclarations": [ /* FR-08 之工具定義 */ ] }],
  "toolConfig": { "functionCallingConfig": { "mode": "AUTO" } },
  "generationConfig": {
    "temperature": 0.7,
    "maxOutputTokens": 8192,
    "responseMimeType": "text/plain"
  },
  "safetySettings": [ /* 依需要調整 */ ]
}
```

**Response 主要欄位**：`candidates[].content.parts[]` 可為 `text` 或 `functionCall`；`usageMetadata` 用於記錄 token 消耗。

**Tool Use 流程**：若 response 含 `functionCall`，後端執行對應工具後將結果以 `role: "function"` 的 `functionResponse` 格式塞回 `contents` 再次呼叫 Gemini，直到回傳純文字為止。

**錯誤處理**：若 API 回傳 429 / 5xx，以指數退避重試（最多 3 次）；所有失敗皆寫入 `logs/gemini.log` 並於前端對話區顯示錯誤訊息。

---

## 9. 前端設計

### 9.1 頁面結構

- **主視窗**：左側 Sidebar（Workspace 切換 + 對話列表 + 專案列表）、中央 Chat 主區、右側 Drawer（選填，顯示目前引用的知識 chunks）。
- **專案頁**：列表 / 詳情 / KPI 編輯 / 工作日誌。
- **知識庫頁**：匯入表單 + 已匯入列表（支援刪除 / 重新索引）。
- **週報頁**：草稿編輯 + 歷史週報列表。
- **設定頁**：API 端點、Briefing 時間、預設 Workspace。

### 9.2 關鍵互動

- 對話輸入框支援斜線指令（如 `/report` 產週報、`/log` 新增日誌）。
- LLM 執行 tool 時前端顯示「Assistant 正在查詢知識庫…」等過程訊息。
- Briefing 到達時：若 App 處於最小化，透過 Tauri API 呼叫 `window.show()` 並 focus。

### 9.3 狀態管理

- Zustand store：`currentWorkspace`、`currentConversation`、`projects`、`kpiDraft`。
- API 呼叫以 React Query 封裝，啟用背景重取與快取。

---

## 10. RAG 與 LLM 推論流程

### 10.1 知識匯入流程

① 使用者匯入檔案 / URL → ② 解析為純文字 → ③ 切塊（chunk）→ ④ 呼叫 bge-m3 取得 embedding → ⑤ 存入 ChromaDB 並於 SQLite 建立 `knowledge_sources` 記錄。

### 10.2 對話推論流程

① 使用者輸入訊息 → ② 後端讀取最近 N 輪訊息 → ③ 對最新訊息執行 embedding 並於 ChromaDB 檢索 Top-K → ④ 組裝 `systemInstruction` + `contents`（包含 workspace、tool 定義、檢索結果）→ ⑤ 透過 HTTPS POST 呼叫 Gemini API（`streamGenerateContent`）→ ⑥ 若回傳 `functionCall`，後端執行對應工具後以 `functionResponse` 塞回 `contents` 再次呼叫 Gemini → ⑦ 最終回覆以 WebSocket streaming 逐 token 推送至前端。

### 10.3 週報產生流程

① 讀取當週（週一至週五）所有 `work_logs` 與相關專案 KPI → ② 依專案分組 → ③ 對每個專案從 ChromaDB 取得 Background 摘要 → ④ 以固定 prompt 指示 LLM 產生三段式草稿（Background / 本週事項 + KPI / 總結）→ ⑤ 儲存為 `reports` 記錄 `status=draft` → ⑥ 使用者於對話中指示修改，每次修改沿用最新版本作為 context 並產生新版本。

---

## 11. 排程與背景服務

### 11.1 常駐機制

- 後端 FastAPI 以 Uvicorn 執行，由 Windows 工作排程器於「使用者登入時」啟動。
- Tauri 前端以一般 GUI 形式啟動；關閉視窗時僅最小化至系統匣，不終止後端。

### 11.2 排程工作

| 工作 | 頻率 | 內容 |
|---|---|---|
| 每日 Briefing | 每日 08:00 | 組合 Briefing 並透過 WebSocket 推播 + 存檔 |
| 專案到期掃描 | 每日 07:55 | 更新「即將到期」旗標以供 Briefing 使用 |
| 未更新提醒掃描 | 每日 07:55 | 標記 `last_updated_at > 3 天`的進行中專案 |

---

## 12. 部署與目錄配置

### 12.1 目錄結構

安裝後於 `%USERPROFILE%\PersonalAIAssistant\` 建立以下目錄：

```
PersonalAIAssistant\
├── app\                 應用程式執行檔（Tauri 打包）
├── data\
│   ├── app.db          SQLite 主資料庫
│   └── chroma\         ChromaDB 向量資料
├── uploads\             原始匯入檔備份
├── reports\             週報 .txt
├── briefings\           每日 Briefing .txt
├── logs\                後端日誌
└── config.yaml          API 端點 / Briefing 時間 / 預設 Workspace
```

### 12.2 安裝流程

① 安裝 Tauri MSI 安裝檔 → ② 複製 `config/.env.example` 為 `%USERPROFILE%\PersonalAIAssistant\.env` 並填入 `GEMINI_API_KEY` 等必要參數 → ③ 首次啟動時 `pydantic-settings` 驗證 `.env`，缺漏則跳出設定精靈提示補齊 → ④ 建立預設 Workspace（工作、生活）→ ⑤ 啟用 Windows 工作排程器項目以常駐後端。

### 12.3 .env 配置說明

所有 Gemini 相關金鑰與可調整參數集中於 `.env` 檔，啟動時由 `pydantic-settings` 載入並驗證。`.env` 位置預設為 `%USERPROFILE%\PersonalAIAssistant\.env`，在開發環境可放於專案根目錄。

**分類與必填欄位**：

| 分類 | 變數 | 必填 | 預設 / 範例 | 說明 |
|---|---|---|---|---|
| Gemini | `GEMINI_API_KEY` | ✅ | *(空)* | Google AI Studio 取得的金鑰 |
| Gemini | `GEMINI_MODEL` | ✅ | `gemini-3.1-pro-preview` | 推論模型名稱 |
| Gemini | `GEMINI_API_BASE_URL` | ⭕ | `https://generativelanguage.googleapis.com/v1beta` | 可替換為 Vertex AI endpoint |
| Gemini | `GEMINI_TEMPERATURE` | ⭕ | `0.7` | 0.0 ~ 1.0 |
| Gemini | `GEMINI_MAX_OUTPUT_TOKENS` | ⭕ | `8192` | 單次輸出上限 |
| Gemini | `GEMINI_TIMEOUT_SECONDS` | ⭕ | `60` | HTTP 逾時 |
| Gemini | `GEMINI_STREAM` | ⭕ | `true` | 是否使用 streaming |
| Gemini | `GEMINI_SAFETY_THRESHOLD` | ⭕ | `BLOCK_NONE` | 對個人使用放寬安全過濾 |
| Embedding | `EMBEDDING_PROVIDER` | ⭕ | `local` | `local` / `gemini` |
| Embedding | `EMBEDDING_MODEL` | ⭕ | `BAAI/bge-m3` | local 模式使用 |
| Embedding | `GEMINI_EMBEDDING_MODEL` | ⭕ | `text-embedding-004` | gemini 模式使用 |
| 後端 | `APP_HOST` | ⭕ | `127.0.0.1` | 僅綁本機 |
| 後端 | `APP_PORT` | ⭕ | `8765` | |
| 後端 | `LOG_LEVEL` | ⭕ | `INFO` | |
| 資料目錄 | `DATA_DIR` | ⭕ | `./data` | SQLite / Chroma |
| 資料目錄 | `UPLOADS_DIR` | ⭕ | `./uploads` | |
| 資料目錄 | `REPORTS_DIR` | ⭕ | `./reports` | |
| 資料目錄 | `BRIEFINGS_DIR` | ⭕ | `./briefings` | |
| 排程 | `BRIEFING_TIME` | ⭕ | `08:00` | 每日 Briefing 時間（24h） |
| 排程 | `BRIEFING_TIMEZONE` | ⭕ | `Asia/Taipei` | IANA tz |
| 排程 | `DUE_WARNING_DAYS` | ⭕ | `3` | 到期前幾天開始提醒 |
| 排程 | `STALE_PROJECT_DAYS` | ⭕ | `3` | 未更新幾天視為停滯 |
| Workspace | `DEFAULT_WORKSPACE` | ⭕ | `work` | `work` / `life` |
| RAG | `RAG_TOP_K` | ⭕ | `5` | 檢索筆數 |
| RAG | `CHUNK_SIZE` | ⭕ | `800` | chunk token 上限 |
| RAG | `CHUNK_OVERLAP` | ⭕ | `100` | chunk 重疊 tokens |

**安全性提醒**：`.env` 含 API 金鑰，務必加入 `.gitignore`；若備份資料目錄需同步注意此檔案。

**pydantic-settings 對應類別（示意）**：

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str
    gemini_model: str = "gemini-2.5-pro"
    gemini_api_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_temperature: float = 0.7
    gemini_max_output_tokens: int = 8192
    gemini_timeout_seconds: int = 60
    gemini_stream: bool = True
    gemini_safety_threshold: str = "BLOCK_NONE"

    embedding_provider: str = "local"
    embedding_model: str = "BAAI/bge-m3"
    gemini_embedding_model: str = "text-embedding-004"

    app_host: str = "127.0.0.1"
    app_port: int = 8765
    log_level: str = "INFO"

    data_dir: str = "./data"
    uploads_dir: str = "./uploads"
    reports_dir: str = "./reports"
    briefings_dir: str = "./briefings"

    briefing_time: str = "08:00"
    briefing_timezone: str = "Asia/Taipei"
    due_warning_days: int = 3
    stale_project_days: int = 3

    default_workspace: str = "work"
    rag_top_k: int = 5
    chunk_size: int = 800
    chunk_overlap: int = 100
```

---

## 13. 開發里程碑

| 里程碑 | 時程（估） | 交付內容 |
|---|---|---|
| M1 基礎框架 | 第 1-2 週 | FastAPI + SQLite schema + React 骨架 + Gemini API client 封裝 + `.env` 載入 |
| M2 Workspace 與專案 | 第 3 週 | Workspace/專案/工作日誌 CRUD + 前端對應頁面 |
| M3 知識庫 + RAG | 第 4-5 週 | PPT/txt/URL/會議記錄 匯入 + ChromaDB + bge-m3 檢索 |
| M4 對話 + Tool Use | 第 6-7 週 | Chat UI + WebSocket streaming + Function Calling 分派 |
| M5 週報 + KPI | 第 8 週 | 週報草稿產生 + 對話式修改 + KPI 推論 |
| M6 Briefing + 排程 | 第 9 週 | APScheduler + 08:00 推播 + 未更新掃描 |
| M7 Tauri 打包 + 穩定化 | 第 10 週 | MSI 打包、工作排程器、錯誤回報、使用者測試 |

---

## 14. 風險與對策

| 風險 | 對策 |
|---|---|
| Gemini API 格式與 OpenAI 不同（`contents` vs `messages`、`functionCall` 結構） | `gemini_client.py` 建立轉換層，將內部統一格式對應至 Gemini request / response；對上層隱藏差異 |
| Gemini API 金鑰外洩風險 | 金鑰僅存於 `.env`，加入 `.gitignore`；日誌遮罩金鑰；必要時改用 Vertex AI + Service Account |
| Gemini 免費額度 / Rate Limit 觸發 | 內建指數退避重試；於設定中可調整 `GEMINI_TIMEOUT_SECONDS`；超額時前端顯示友善訊息 |
| PPT 內容包含大量圖表，純文字抽取不足 | 以 python-pptx 抽文字 + 備註；圖片部分標註為 `[圖片]` 佔位；未來視需要加入 OCR |
| Briefing 08:00 時使用者未開機 | 服務於下次啟動時檢查今日是否已推播，若否則補推播 |
| LLM 在 Tool Use 中誤寫入資料庫 | 所有寫入工具在執行前於對話中顯示確認訊息；保留操作日誌 |
| SQLite 長期成長影響查詢效能 | `work_logs` 與 `messages` 建立 `(workspace_id, date)` 索引；必要時做歷史歸檔 |
| 公司與家用環境不同、設定易漏掉 | 首次啟動提供設定精靈；`config.yaml` 可直接 git-ignore 或備份 |

---

## 15. 附錄：Tool Use 函數簽章

```python
create_work_log(
    project_id: str,
    log_date: date,
    content: str,
    kpi_id: Optional[str]
) -> WorkLog

update_project_status(
    project_id: str,
    status: Literal['active', 'paused', 'done'],
    progress: Optional[str]
) -> Project

search_knowledge(
    query: str,
    workspace_id: str,
    project_id: Optional[str],
    top_k: int = 5
) -> List[Chunk]

list_projects(
    workspace_id: str,
    status: Optional[str],
    due_within_days: Optional[int]
) -> List[Project]

generate_weekly_report(
    workspace_id: str,
    iso_week: str
) -> Report

set_project_due_date(
    project_id: str,
    due_date: date
) -> Project

infer_kpi(
    project_id: str,
    recent_logs_count: int = 10
) -> List[KPI]
```

---

*— 規格書結束 —*
