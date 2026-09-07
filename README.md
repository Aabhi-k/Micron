# Micron

A modern full-stack application featuring a FastAPI backend with async lifespan lifecycle management and a frontend service.

## Project Structure

```text
micron/
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI app definition with async lifespan & health check
│   ├── requirements.txt     # Python dependencies
│   └── .env.example         # Example environment variables
├── frontend/                # Frontend application directory
├── .gitignore               # Git ignore rules for Python, Node, IDEs, and OS
└── README.md                # Project documentation
```

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js & npm (for frontend development)

---

### Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - **macOS / Linux**:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**:
   Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```

5. **Run the development server**:
   From the repository root:
   ```bash
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```
   Or from within the `backend/` directory:
   ```bash
   python main.py
   ```

---

### Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Run the development server**:
   ```bash
   npm run dev
   ```

---

## API Endpoints

| Method | Endpoint  | Description               |
|--------|-----------|---------------------------|
| `GET`  | `/health` | Service health status     |
| `GET`  | `/docs`   | Interactive Swagger UI    |
| `GET`  | `/redoc`  | ReDoc API documentation   |

### Sample Request

```bash
curl http://127.0.0.1:8000/health
```

**Response:**
```json
{
  "status": "ok"
}
```
