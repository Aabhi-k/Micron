# Micron — Enterprise Legacy Code Documentation Platform

A high-performance enterprise documentation and reverse-engineering platform for mission-critical legacy codebases (C, C++, Java, Python). Engineered with **FastAPI**, an isolated **Model Context Protocol (MCP)** server for local AST parsing, **Vector Retrieval (RAG)** over authoritative Business Process Documents, and an IDE-grade user interface.

---

## Architecture & Project Structure

```text
micron/
├── docker-compose.yml              # Orchestrates Web, Backend, MCP, Vector DB
├── .env.example                    # Global environment configuration template
│
├── storage/                        # Persistent local mount (ignored in Git)
│   └── projects/                   # Where uploaded/cloned legacy codebases live
│
├── backend/                        # FastAPI Application (API Gateway + Orchestrator)
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── projects.py     # Upload, clone, list target codebases
│   │   │       ├── files.py        # File tree & file content endpoints
│   │   │       ├── chat.py         # RAG + MCP orchestration chat endpoint
│   │   │       └── symbols.py      # Symbol lookup & AST definitions
│   │   ├── core/
│   │   │   ├── config.py           # App settings and storage paths
│   │   │   └── security.py         # Path validation & sandbox helpers
│   │   ├── services/
│   │   │   ├── mcp_client.py       # MCP Client invoking the MCP Server
│   │   │   ├── rag_engine.py       # Vector search over business documents
│   │   │   ├── parser.py           # Tree-sitter symbol extractor
│   │   │   └── synthesizer.py      # LLM prompt synthesis & streaming
│   │   └── main.py                 # FastAPI application factory & lifespan
│   ├── Dockerfile
│   └── requirements.txt
│
├── mcp_server/                     # Dedicated Sandboxed MCP Server
│   ├── server.py                   # FastMCP tool definitions (AST, Tree, Symbols)
│   ├── tools/
│   │   ├── ast_extractor.py        # Tree-sitter C/C++/Python/Java parsers
│   │   ├── file_explorer.py        # Path-traversal-safe directory traversal
│   │   └── dependency_graph.py     # Call graph and symbol resolution
│   ├── Dockerfile.mcp              # Isolated container with zero network egress
│   └── requirements.txt
│
└── frontend/                       # React / Vite IDE UI
    └── src/
```

---

## Core Components

1. **Sandboxed MCP Server (`mcp_server/`)**:
   - Executes inside an isolated sandbox with zero external network egress.
   - Parses code structures (AST), extracts function boundaries, and scrubs intellectual property and secrets before data moves upstream.
2. **Backend Orchestrator (`backend/app/`)**:
   - FastAPI gateway enforcing strict path-jail boundaries within `storage/projects/`.
   - Coordinates deterministic MCP tool calls and hybrid vector search over Business Process Documents (BPD).
   - Synthesizes grounded, citation-backed documentation with LLMs.
3. **Storage Sandbox (`storage/projects/`)**:
   - Local directory mount for legacy repositories, keeping raw source code safely isolated.

---

## Getting Started

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+ & npm**
- **Docker & Docker Compose** (optional for containerized setup)

---

### 2. Docker Compose (Full Stack)

Start all services (Vector DB, MCP Server, Backend, Frontend) with a single command:

```bash
docker compose up --build
```

---

### 3. Local Development Setup

#### Backend & MCP Server
1. Navigate to backend:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r ../mcp_server/requirements.txt
   ```
4. Copy environment variables:
   ```bash
   cp ../.env.example .env
   ```
5. Run the FastAPI backend:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

#### Frontend
1. Navigate to frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

### 4. Observability (Langfuse Cloud)

Micron natively tracks LLM completions, embeddings, MCP tool invocations, and multi-tenant RAG retrieval queries using **Langfuse Cloud**.

1. Register at [cloud.langfuse.com](https://cloud.langfuse.com) (EU) or [us.cloud.langfuse.com](https://us.cloud.langfuse.com) (US).
2. Generate API Keys in **Project Settings -> API Keys**.
3. Set your keys in `.env`:
   ```env
   LANGFUSE_PUBLIC_KEY=pk-lf-...
   LANGFUSE_SECRET_KEY=sk-lf-...
   LANGFUSE_HOST=https://cloud.langfuse.com
   ```
4. Verify your setup with the automated check:
   ```bash
   python backend/verify_langfuse.py
   ```


## API Endpoints (v1)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health status |
| `GET` | `/api/v1/projects/` | List all legacy projects in storage |
| `POST` | `/api/v1/projects/upload` | Upload a zip archive of legacy code |
| `POST` | `/api/v1/projects/clone` | Git clone a repository into project sandbox |
| `GET` | `/api/v1/files/tree/{project_id}` | Hierarchical file tree of a project |
| `GET` | `/api/v1/files/content/{project_id}` | Path-safe source file viewer |
| `POST` | `/api/v1/chat/explain-function` | Grounded AST + BPD function explanation |
| `POST` | `/api/v1/chat/` | General RAG inquiry endpoint |
| `GET` | `/api/v1/symbols/ast` | Extract function AST boundaries via MCP |
| `GET` | `/api/v1/symbols/dependencies` | Extract imports and dependencies via MCP |
| `GET` | `/docs` | Interactive Swagger API documentation |
