# 📊 개인 투자 추천 Agent

> LangGraph 기반 Multi-Agent 한/미 주식 포트폴리오 분석 및 매매 추천 서비스

---

## 📌 프로젝트 개요

한국과 미국 주식 시장에 동시 투자하는 개인 투자자를 위한 AI Agent 서비스입니다.
매일 보유 종목의 종가와 환율을 자동 수집하고, 섹터 트렌드를 분석하여
데이터 기반의 매매 추천과 월 정기 투자금 배분 가이드를 제공합니다.

---

## 🏗️ 시스템 아키텍처

```
Streamlit UI (frontend/app.py)
        ↓
FastAPI Backend (backend/main.py)
        ↓
Supervisor Agent (요청 분류 및 라우팅)
        ↓
┌─────────────────────────────────────┐
│  데이터 수집 Agent                   │  ← pykrx / yfinance / 환율
│  포트폴리오 분석 Agent               │  ← 수익률 계산
│  섹터 분석 Agent          (A2A)      │  ← 섹터 트렌드 분류
│  RAG Enricher                        │  ← FAISS 벡터 검색
│  매매 추천 Agent                     │  ← Structured Output
│  리포트 생성 Agent                   │  ← 최종 출력
│  대화 Agent                          │  ← 맥락 유지 Q&A
└─────────────────────────────────────┘
        ↓
Azure OpenAI (GPT-4o / text-embedding-3-large)
```

---

## ✨ 주요 기능

| 기능 | 설명 |
|---|---|
| 📈 Daily 브리핑 | 매일 종가/환율 자동 수집 → 종목별/전체 수익률 계산 |
| 📡 섹터 트렌드 | 한/미 섹터 UPTREND/DOWNTREND/NEUTRAL 분류 |
| 💡 매매 추천 | 섹터 트렌드 기반 매도/매수 추천 + 근거 및 리스크 제공 |
| 💰 투자금 배분 | 월 150만원 정기 투자금 섹터 트렌드 기반 배분 가이드 |
| 💬 대화 질의 | 포트폴리오 컨텍스트 유지 개별 종목 질의응답 |

---

## 🛠️ 기술 스택

| 분류 | 기술 |
|---|---|
| **Agent Framework** | LangChain, LangGraph (StateGraph) |
| **LLM** | Azure OpenAI GPT-4o / GPT-4o-mini |
| **Embedding** | Azure OpenAI text-embedding-3-large |
| **RAG** | FAISS, LangChain RAG Chain |
| **데이터 수집** | pykrx (한국 주식), yfinance (미국 주식/환율) |
| **백엔드** | FastAPI, Uvicorn |
| **프론트엔드** | Streamlit, Plotly |
| **환경 관리** | python-dotenv |

---

## 📁 프로젝트 구조

```
investment-agent/
│
├── .env                          # 환경변수 (API Key)
├── .gitignore                    # Git 제외 파일
├── requirements.txt              # 패키지 의존성
├── README.md                     # 프로젝트 설명
├── config.py                     # LLM/Embedding 환경 전환
├── portfolio.txt                 # 보유 종목 입력 파일
│
├── agents/                       # LangGraph Multi-Agent
│   ├── state.py                  # PortfolioState 정의
│   ├── graph.py                  # StateGraph 전체 흐름
│   ├── supervisor.py             # 요청 분류 및 라우팅
│   ├── data_collector.py         # 종가/환율 수집
│   ├── portfolio_analyzer.py     # 수익률 계산
│   ├── sector_analyzer.py        # 섹터 트렌드 분류
│   ├── recommender.py            # 매매 추천 (Structured Output)
│   ├── report_generator.py       # 리포트 생성
│   └── conversation.py           # 대화 Agent
│
├── tools/                        # Tool Calling 함수
│   ├── kr_stock.py               # pykrx 한국 주식/섹터
│   ├── us_stock.py               # yfinance 미국 주식/섹터
│   └── exchange_rate.py          # yfinance 환율
│
├── rag/                          # RAG 파이프라인
│   ├── loader.py                 # 문서 로딩 및 청킹
│   ├── embedder.py               # 임베딩 생성
│   ├── vectorstore.py            # FAISS 저장/로드
│   └── retriever.py              # 검색 체인
│
├── backend/                      # FastAPI 백엔드
│   ├── main.py                   # FastAPI 진입점
│   └── routers/
│       ├── portfolio_router.py   # 포트폴리오 업로드
│       ├── briefing_router.py    # Daily 브리핑
│       ├── sector_router.py      # 섹터 분석
│       ├── recommendation_router.py # 매매 추천
│       └── chat_router.py        # 대화 질의
│
├── frontend/                     # Streamlit UI
│   ├── app.py                    # 진입점 + 사이드바
│   └── pages/
│       ├── briefing_page.py      # Daily 브리핑 탭
│       ├── sector_page.py        # 섹터 트렌드 탭
│       ├── recommendation_page.py# 매매 추천 탭
│       └── chat_page.py          # 대화 질의 탭
│
├── utils/                        # 공통 유틸
│   └── parser.py                 # portfolio.txt 파서
│
└── data/                         # 데이터 저장소
    ├── vectorstore/              # FAISS 인덱스
    ├── documents/                # RAG용 문서
    └── history/                  # 일별 포트폴리오 기록
```

---

## 🚀 시작하기

### 1. 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정

`.env` 파일을 프로젝트 루트에 생성합니다.

```bash
# 환경 선택 (local / azure)
ENV_MODE=local

# LOCAL - OpenAI
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_DEPLOY_GPT4O=gpt-4o
OPENAI_DEPLOY_GPT4O_MINI=gpt-4o-mini
OPENAI_DEPLOY_EMBED_3_LARGE=text-embedding-3-large
OPENAI_DEPLOY_EMBED_3_SMALL=text-embedding-3-small

# AZURE - AOAI
AOAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AOAI_API_KEY=your_api_key
AOAI_DEPLOY_GPT4O=gpt-4o
AOAI_DEPLOY_GPT4O_MINI=gpt-4o-mini
AOAI_DEPLOY_EMBED_3_LARGE=text-embedding-3-large

# 서비스 설정
ANALYSIS_PERIOD_WEEKS=4
MONTHLY_DEPOSIT_KRW=1500000
VECTORSTORE_PATH=./data/vectorstore
HISTORY_PATH=./data/history
```

### 3. 포트폴리오 파일 작성

`portfolio.txt` 파일을 프로젝트 루트에 작성합니다.

```
INVESTOR_NAME=홍길동
MONTHLY_DEPOSIT=1500000
BASE_CURRENCY=KRW

# 한국 주식 (종목코드 | 종목명 | 시장 | 섹터 | 수량 | 매입가 | 매입일)
005930 | 삼성전자 | KOSPI | 반도체 | 50 | 220000 | 2023-03-15
000660 | SK하이닉스 | KOSPI | 반도체 | 20 | 130000 | 2023-06-01

# 미국 주식 (티커 | 종목명 | 시장 | 섹터 | 수량 | 매입가USD | 매입일)
AAPL | Apple Inc. | NASDAQ | 기술주 | 10 | 178.50 | 2023-01-10
NVDA | Nvidia Corp. | NASDAQ | AI 반도체 | 5 | 55.00 | 2023-06-01
VOO  | Vanguard S&P500 ETF | NYSE | ETF-미국전체 | 5 | 410.00 | 2022-11-20
```

### 4. RAG 벡터 저장소 초기 빌드 (최초 1회)

```bash
python rag/vectorstore.py
```

### 5. 서버 실행

**터미널 1 - FastAPI 백엔드**
```bash
uvicorn backend.main:app --reload --port 8000
```

**터미널 2 - Streamlit UI**
```bash
streamlit run frontend/app.py
```

### 6. 접속

| 서비스 | URL |
|---|---|
| Streamlit UI | http://localhost:8501 |
| FastAPI Swagger | http://localhost:8000/docs |

---

## 📊 Multi-Agent 실행 흐름

```
사용자 입력
    ↓
Supervisor Agent → 요청 유형 분류
    ├── "브리핑/추천" → full_pipeline
    │       데이터 수집 → 포트폴리오 분석 → 섹터 분석
    │       → RAG 보강 → 매매 추천 → 리포트 생성
    │
    ├── "섹터 분석"  → sector_only
    │       데이터 수집 → 섹터 분석 → 리포트 생성
    │
    └── "개별 질의"  → conversation
            대화 Agent (포트폴리오 컨텍스트 유지)
```

---

## 🔑 핵심 기술 요소

### Prompt Engineering
- 역할 기반 프롬프트 (각 Agent별 명확한 Role 부여)
- Chain-of-Thought (섹터 분류 단계별 추론)
- Few-shot (매매 추천 출력 형식 예시 제공)
- Structured Output (Pydantic 기반 일관된 JSON 출력)

### LangGraph Multi-Agent
- StateGraph 기반 7개 Agent 협업
- Conditional Edge로 요청별 실행 경로 분기
- A2A (섹터 분석 ↔ 포트폴리오 분석 교차 검증)
- ConversationBufferMemory 대화 컨텍스트 유지

### RAG
- yfinance 뉴스 + 투자 용어 사전 문서화
- RecursiveCharacterTextSplitter (chunk_size=500)
- FAISS 로컬 벡터 저장소
- 섹터 메타데이터 필터링 검색

### Structured Output
- Pydantic BaseModel 기반 매매 추천 스키마
- `llm.with_structured_output()` 적용
- 일관된 JSON 출력으로 UI 렌더링 안정성 확보

---

## ⚠️ 주의사항

- 레버리지 상품 및 펀드는 추천하지 않습니다.
- 본 서비스의 추천은 참고용이며 투자 결정의 최종 책임은 사용자에게 있습니다.
- API Key는 `.env` 파일로 관리하며 절대 공개 저장소에 업로드하지 마세요.

---

## 📝 개발 환경

- Python 3.11+
- Azure OpenAI (GPT-4o, text-embedding-3-large)
- Windows 10/11 또는 Ubuntu 22.04