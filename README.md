# 🤖 DTDL Customer Intelligence Platform

**AI-Powered Multi-Agent Customer Support System for Telecom**

Built for The Talent Hack 2026 - Deutsche Telekom Digital Labs (DTDL) Hiring Challenge.

## 🎯 What It Does

An intelligent customer support platform using multiple AI agents to handle telecom queries:

| Agent | Role |
|-------|------|
| **Ingestion Agent** | Receives and preprocesses customer messages |
| **Classifier Agent** | Determines intent (billing, technical, retention, sales) |
| **Billing Agent** | Handles billing, payments, plans with RAG |
| **Technical Agent** | Resolves network, device, SIM issues with RAG |
| **Retention Agent** | Prevents churn with personalized offers |
| **Escalation Agent** | Routes complex cases to human agents |
| **Formatter Agent** | Personalizes and formats final responses |

## 🏗️ Architecture

```
Customer Message → Ingestion → Classifier → [Billing/Technical/Retention] → Formatter
                                          ↓
                                    [Escalation if needed]
```

## 🚀 Quick Start

### 1. Setup

```bash
git clone https://github.com/Tee808-bigD/AI-Expense-Procurement-Auditor.git
cd AI-Expense-Procurement-Auditor
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and add your NVIDIA_API_KEY
```

### 3. Initialize

```bash
python scripts/init_knowledge_base.py
```

### 4. Run

```bash
# Option A: Start both (API + Dashboard)
./run.sh

# Option B: Start separately
python -m uvicorn api.main:app --reload        # API: http://localhost:8000/docs
streamlit run dashboard/app.py                  # Dashboard: http://localhost:8501

# Option C: Docker
docker-compose up --build
```

## 🧪 Testing

```bash
pytest tests/ -v
```

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/process` | POST | Process customer message |
| `/api/v1/tickets` | GET | List tickets |
| `/api/v1/tickets/{id}` | GET | Ticket details |
| `/api/v1/stats` | GET | System stats |
| `/api/v1/analytics/dashboard` | GET | Dashboard data |
| `/api/v1/knowledge-base/{cat}` | POST/GET | Manage KB |

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | NVIDIA NIM (Llama 3.1 8B) |
| RAG | FAISS + LangChain |
| Embeddings | sentence-transformers |
| API | FastAPI |
| Dashboard | Streamlit |
| Database | SQLite |
| Deployment | Docker / Render |

## 📁 Structure

```
dtdl-customer-intelligence-platform/
├── agents/              # 7 specialized agents
├── api/                 # FastAPI backend
├── dashboard/           # Streamlit frontend
├── knowledge_base/      # RAG documents (billing, technical, retention)
├── data/                # Database & vector store
├── scripts/             # Setup scripts
├── tests/               # Unit tests
├── config.py            # Configuration
├── models.py            # Database models
├── orchestrator.py      # Agent orchestrator
├── rag_knowledge_base.py # RAG module
├── utils.py             # Utilities
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🎥 Demo

Record a 2-3 min video showing:
- Chat interface with different query types
- Ticket management
- Analytics dashboard
- Multi-agent pipeline

## 👨‍💻 Author

Built for The Talent Hack 2026 - DTDL

## 📄 License

MIT
