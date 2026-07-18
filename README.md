# Apex Studio

**Build complete applications by chatting with AI.**

Apex Studio is a SaaS platform that lets anyone — regardless of technical knowledge — create full-stack software applications through natural language conversation. The AI handles the entire software development lifecycle: requirements, architecture, code generation, building, testing, and deployment.

## Architecture

```
┌──────────── User Browser (Flutter Web) ────────────┐
│  Sidebar | Chat Panel | Preview | Terminal | Logs   │
└──────────────────────┬──────────────────────────────┘
                       │ HTTPS / WSS
┌──────────────────────▼──────────────────────────────┐
│                    Nginx                              │
└──────┬───────────────────────────┬──────────────────┘
       │                           │
┌──────▼──────────┐   ┌───────────▼──────────────────┐
│  FastAPI (REST) │   │  FastAPI (WebSocket / Agent)  │
└──────┬──────────┘   └───────────┬──────────────────┘
       │                          │
┌──────▼──────────────────────────▼──────────────────┐
│            PostgreSQL  │  Redis  │  Omniroute        │
└────────────────────────────────────────────────────┘
```

## Tech Stack

| Component | Technology |
|---|---|
| Frontend | Flutter (Web) |
| Backend | FastAPI + Python |
| Database | PostgreSQL |
| Cache | Redis |
| Container | Docker |
| Proxy | Nginx |
| AI Gateway | Omniroute |
| Models | Claude, GPT, Gemini, OpenRouter |
| Storage | S3-compatible |

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Flutter SDK

### Development

1. Clone the repo:
```bash
git clone https://github.com/your-org/apex-studio.git
cd apex-studio
```

2. Copy environment:
```bash
cp .env.example .env
```

3. Start infrastructure:
```bash
docker compose -f infra/docker-compose.yml up -d
```

4. Start backend:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

5. Start frontend:
```bash
cd frontend
flutter pub get
flutter run -d chrome
```

6. Open http://localhost:8080

## Project Structure

```
apex-studio/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/       # Route handlers
│   │   ├── agents/    # AI agent system
│   │   ├── core/      # Config, DB, security
│   │   ├── models/    # SQLAlchemy models
│   │   ├── schemas/   # Pydantic schemas
│   │   ├── services/  # Business logic
│   │   └── generators/# Code generation
│   └── alembic/       # Migrations
├── frontend/          # Flutter Web
│   └── lib/
│       ├── core/      # Config, theme, API client
│       └── features/  # Feature modules
├── infra/             # Docker, Nginx, scripts
└── workspaces/        # Per-project workspaces
```

## License

Proprietary — All rights reserved.
