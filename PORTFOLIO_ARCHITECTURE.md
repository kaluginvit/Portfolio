# Portfolio Architecture Map

> Архитектурные схемы showcase-проектов

---

## 1. finance-mcp-server

**Corporate Finance AI Layer — MCP Protocol**

```mermaid
flowchart LR
    subgraph client["AI Client"]
        CD[Claude Desktop / Cursor]
    end
    subgraph mcp["MCP Server (Python)"]
        REG[Registry — 19 tools]
        subgraph services["Business Services"]
            FS[Finance Service\nP&L, EBITDA, margins]
            TS[Treasury Service\nCash Flow, liquidity]
            IS[Investment Service\nNPV, IRR, PI]
            CS[Contract Service\nRisk scan, alerts]
            RS[Reporting Service\nJSON/TXT export]
        end
        DB[(SQLite\nfinance.db)]
        SEED[Seed Data\n2 companies, 12 mo.]
    end
    subgraph ui["Optional UI"]
        NEXT[Next.js Dashboard]
    end

    CD -- "MCP stdio transport" --> REG
    REG --> services
    services --> DB
    SEED --> DB
    NEXT -- REST --> REG
```

**Ключевые решения:**
- SQLite zero-deploy: данные не уходят за пределы машины
- Registry pattern: вызов tools без MCP-транспорта (для тестов)
- 19 tools → 6 сервисов → 1 БД-коннектор

---

## 2. finance-data-screener

**AI Financial Data Screener — Full Stack**

```mermaid
flowchart TB
    subgraph frontend["Frontend (React + TypeScript)"]
        UI[Web App\nDatasets / Collect / Showcase / Audit]
    end
    subgraph nginx["nginx :80"]
        PROXY[Reverse Proxy\n/api/ → backend:8000]
    end
    subgraph backend["Backend (FastAPI :8000)"]
        AI[LLM Planner\ngpt-4o-mini + instructor]
        subgraph collectors["Data Collectors"]
            MOEX[MOEX ISS\nStocks / Bonds]
            CBR[ЦБ РФ\nCurrency Rates]
            TASS[ТАСС RSS\nNews]
        end
        AUDIT[Audit Middleware\nlog all requests]
    end
    subgraph db["PostgreSQL :5432"]
        DS[(Datasets)]
        REC[(Records)]
        AR[(Agent Runs)]
        AUD[(Audit Runs)]
    end

    UI --> nginx
    nginx --> backend
    backend --> AI
    AI --> collectors
    collectors --> db
    AUDIT --> db
```

---

## 3. svo-payments-bot + svo-payouts-website

**Связная система: Web + Telegram**

```mermaid
flowchart LR
    subgraph user["Пользователь"]
        WEB[Браузер\nsvorazbor.ru]
        TG[Telegram]
    end
    subgraph web["Next.js (VPS)"]
        QUIZ[Квиз компонент]
        LEAD[Лид-форма]
        WH_W[Webhook → CRM]
    end
    subgraph bot["aiogram 3 (VPS)"]
        FSM[FSM Engine\nSQLite WAL]
        CALC[Calculator\nвиды выплат]
        LEAD_B[Lead Repository]
        WH_B[Webhook → CRM]
    end
    subgraph ci["CI/CD"]
        GHA[GitHub Actions]
        GHCR[GHCR Registry]
        SSH[SSH Deploy]
    end

    WEB --> QUIZ --> LEAD --> WH_W
    TG --> FSM --> CALC --> LEAD_B --> WH_B
    GHA --> GHCR --> SSH --> bot
```

---

## 4. hr-breaker

**Resume Optimizer — Multi-Agent Pipeline**

```mermaid
flowchart TD
    INPUT[Resume\nany format] --> EXTRACT[Extraction Agent\nPydantic-AI]
    JOB[Job Posting\nURL or text] --> SCRAPE[Job Scraper]
    EXTRACT --> OPT[Optimization Agent\nLiteLLM]
    SCRAPE --> OPT
    OPT --> FILTERS

    subgraph FILTERS["8-Layer Filter Pipeline"]
        F0[0: Content Length]
        F1[1: Data Validator]
        F3[3: Hallucination Checker]
        F4[4: Keyword Matcher TF-IDF]
        F5[5: LLM ATS Checker]
        F6[6: Vector Similarity]
        F7[7: AI-Generated Detector]
        F8[8: Translation Quality]
    end

    FILTERS -- "all pass" --> RENDER[HTML → PDF\nWeasyPrint]
    FILTERS -- "reject + feedback" --> OPT
    RENDER --> PDF[Output PDF]

    subgraph interface["Interfaces"]
        WEB[FastAPI + Alpine.js\nSSE real-time progress]
        CLI[Click CLI]
    end
```

---

## 5. rf-macro-risk-ai

**Macro Risk AI — Scoring Pipeline**

```mermaid
flowchart LR
    subgraph criteria["35 Criteria"]
        FAST[Fast react\n~10 criteria]
        MED[Medium react\n~15 criteria]
        SLOW[Slow react\n~10 criteria]
    end
    subgraph agent["LangChain Agent"]
        SEARCH[Tavily Web Search]
        LLM[LLM\nOpenAI/Gemini/GigaChat]
        LEDGER[Research Ledger\nlocal cache]
    end
    subgraph scoring["Scoring Engine"]
        SCORE[Weighted Sum\n0-100+]
        THRESH[Threshold\n🟢/🟡/🟠/🔴/⚫]
        DEP[Deposit Access Risk\n5 special criteria]
    end
    subgraph output["Output"]
        JSON[docs/data.json]
        HTML[GitHub Pages\ndashboard]
        TG[Telegram Channel\npost via reporter]
    end

    criteria --> agent
    agent --> scoring
    scoring --> output
```

---

## 6. fedresurs-mvp

**Bankruptcy Lot Valuation — Dual Engine**

```mermaid
flowchart TB
    subgraph input["Input"]
        CB[Chrome Bookmarks\nFedresurs lots]
        API[Fedresurs Public API\nlot JSON]
    end
    subgraph db["SQLite"]
        LOTS[(Lots table)]
        MKTDATA[(Market data)]
        VALS[(Valuations)]
    end
    subgraph stat["Statistical Engine"]
        PARSE[Parse N1/CIAN\nanalogues]
        QUANT[P25/P50/P75\ncalculation]
        TARGET[target_price =\nP25 * area * 0.90]
    end
    subgraph llm["LLM Agentic Engine"]
        AG[LLM Agent\nGemini/OpenRouter]
        WS[Web Search\nTavily/Brave/Google]
        FOUR[4 price scenarios\nauction/lot/wholesale/retail]
    end
    subgraph ui["Interfaces"]
        CLI[CLI scripts]
        WEB[Flask Web UI\n:5000]
        HTML[HTML Dashboard]
    end

    input --> db
    db --> stat
    db --> llm
    llm --> WS
    stat --> ui
    llm --> ui
```

---

## 7. leadgen-n8n-system

**B2B Lead Generation — 11 Workflow System**

```mermaid
flowchart LR
    subgraph intake["Intake"]
        W1[01 Intent Radar\nearly signals]
        W2[02 Lead DNA\nenrichment]
    end
    subgraph decide["Decision"]
        W3[03 Multi-LLM\nconsensus]
        W4[04 Human\nin the loop]
    end
    subgraph engage["Engagement"]
        W5[05 Premium\noutreach]
        W6[06 Smart Nurture\nwarmth decay]
        W7[07 Competitive\nIntelligence]
    end
    subgraph ops["Operations"]
        W8[08 Command\nCenter]
        W9[09 Shadow\nValidation]
        W10[10 Global\nError Handler]
        W11[11 Live\nDashboard]
    end
    subgraph infra["Infrastructure"]
        N8N[n8n self-hosted]
        PG[(PostgreSQL)]
    end

    W1 --> W2 --> W3 --> W4
    W3 --> W5 --> W6
    W2 --> W7
    W8 --- W3
    W9 --- W3
    W10 --- W8
    W5 & W6 & W7 --> W11
    N8N --- PG
```

---

## 8. mini-crm-fastapi-react

**CRM + Google Integration — Full Stack**

```mermaid
flowchart LR
    subgraph fe["Frontend (React + TypeScript)"]
        PAGES[Clients / Deals / Tasks\nSettings / Reports]
    end
    subgraph be["Backend (FastAPI)"]
        ROUTERS[REST Routers]
        GINT[Google Integration\nOAuth + Drive + Sheets]
        MODELS[SQLAlchemy Models]
    end
    subgraph storage["Storage"]
        SQLITE[(SQLite crm.db)]
        TOKEN[(google_token.pickle)]
        SETTINGS[(google_settings.json)]
    end
    subgraph google["Google APIs"]
        DRIVE[Google Drive]
        SHEETS[Google Sheets]
        OAUTH[OAuth 2.0]
    end

    fe --> be
    ROUTERS --> MODELS --> SQLITE
    ROUTERS --> GINT
    GINT --> OAUTH --> google
    GINT --> DRIVE
    GINT --> SHEETS
    TOKEN --> GINT
    SETTINGS --> GINT
```

---

## 9. fintech-ab-test-credit-offer

**A/B Test Analytics Pipeline**

```mermaid
flowchart LR
    subgraph data["Data Layer"]
        RAW[Raw CSV\n20K rows]
        AUG[Augment\nbootstrap user trajectories]
    end
    subgraph pipeline["Analysis Pipeline (Makefile)"]
        PROC[data_processing.py\nclean + validate]
        ANA[ab_analysis.py\nWelch t-test]
        SS[sample_size.py\nMDE calculation]
        VIZ[visualization.py\ncharts]
        REP[run_analysis.py\nreport generator]
    end
    subgraph sql["SQL Layer"]
        SQL1[01 user_day_funnel]
        SQL2[02 user_level_metrics]
        SQL3[03 group_metric_summary]
        SQL4[04 srm_check]
    end
    subgraph output["Outputs"]
        CSV[processed CSVs]
        FIGS[Figures PNG]
        NB[Jupyter Notebook]
        REP2[final_report.md]
    end

    RAW --> AUG --> data
    data --> pipeline
    pipeline --> sql
    pipeline --> output
```

---

## 10. tg-digest-pipeline (TIER B)

**Personal Knowledge Extraction Pipeline**

```mermaid
flowchart TD
    subgraph sources["Telegram Sources"]
        CHATS[Finance / Coding\nchannels]
        SAVED[Saved Messages]
    end
    subgraph collect["Collection (Telethon)"]
        FETCH[collect.py\nincremental fetch]
        SQLITE1[(messages.db)]
    end
    subgraph process["Processing"]
        FILTER[filter.py\nrelevance scoring]
        EMBED[embed.py\nvector embeddings]
        LLM_S[llm_summarize.py]
        CLUSTER[cluster_queue.py]
        LINKS[index_links.py]
    end
    subgraph storage["Storage"]
        PINECONE[(Pinecone\nvector search)]
        NEO4J[(Neo4j\nknowledge graph)]
    end
    subgraph output["Output"]
        DIGEST[Markdown digest]
        CATALOG[Links catalog CSV]
        SEARCH[search.py]
        WEB[Flask review UI]
    end

    sources --> collect --> process
    process --> storage
    process --> output
    PINECONE --> SEARCH
```
