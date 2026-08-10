# WaitWise – Intelligent Dynamic Queue & Token Management System

> "Don't wait in the queue. Let the queue wait for you."

WaitWise is an enterprise-grade digital token and queue management system designed for medical centers, banks, service centers, and offices. The application helps users secure digital tickets, trace real-time waiting metrics, and receive instant websocket notification alerts as their turn approaches, eliminating physical waiting lines.

---

## Technical Architecture & Core Stack

### Backend
* **Python 3.11+** & **Flask** framework.
* **Flask-SQLAlchemy** (ORM) & **Flask-Migrate** (DB migrations).
* **Flask-SocketIO** (WebSockets for real-time dashboard syncing).
* **Flask-Login** (Session-based secure user authentication).
* **SQLite** (local development database) / **PostgreSQL** compatibility.

### Frontend
* **HTML5** & **Tailwind CSS** (for rich responsive dashboard layouts).
* **Vanilla JavaScript** (using Fetch API and Socket.IO client, no heavy React compilation).
* **Chart.js** (for administrative dashboard performance visualization).

### AI Integration
* **Ollama API** (Local Gemma integration).
* **Mistral API** (Cloud model fallback).
* Supporting selection config: `AI_PROVIDER=ollama|mistral|auto`.

---

## Directory Structure

```
waitwise/
  app/
    __init__.py          # Flask factory configuration
    config.py            # Development & Production environment configs
    extensions.py        # Shared extensions: db, socketio, migrate, login_manager
    models/
      __init__.py
      user.py            # Password-hashed users & roles (USER, STAFF, ADMIN)
      organization.py    # Service provider metadata (Hospital, Bank)
      service.py         # Business actions (Billing, Consultation)
      queue.py           # Core queue status and counters
      token.py           # Sequential digital tickets
      notification.py    # Browser notification alert logs
      queue_event.py     # Operations logs for AI analysis audits
    routes/
      __init__.py        # Root routes & Main blueprint
      auth.py            # Auth views & API registration
      user.py            # User dashboards & profile managers
      queue.py           # Search lists & Queue join logic
      admin.py           # Admin dashboards & TV display hooks
      api.py             # Public RESTful API endpoints
      ai.py              # LLM integration endpoints
    services/
      __init__.py
      token_service.py   # Concurrency-safe ticket creations under DB lock
      estimation_service.py # Rounding wait time estimators
      queue_service.py   # State transitions (call, skip, complete)
      notification_service.py # Socket notifications triggers
      ai_service.py      # LLM prompts packaging
      mistral_service.py # Mistral API wrapper
      ollama_service.py  # Ollama API wrapper
    sockets/
      __init__.py
      queue_socket.py    # Socket rooms & connection handlers
    utils/
      decorators.py      # staff_required, admin_required filters
      validators.py      # Format validation regex checks
      helpers.py         # Standardized API response format helpers
      logger.py          # Log rotations setup
  frontend/
    templates/           # Jinja2 views (user, admin, public panels)
    static/
      css/style.css      # Transitions & styles overrides
      js/                # UI scripts (auth, AI assistant chatbot, etc.)
  tests/                 # Pytest testing suite
  requirements.txt
  .env.example
  seed.py                # Database seed script
  run.py                 # Application launcher
```

---

## Installation & Local Setup

### 1. Initialize Virtual Environment
```bash
# Create venv
python -m venv venv

# Activate venv (Windows)
venv\Scripts\activate

# Activate venv (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` into a new `.env` file:
```bash
copy .env.example .env
```
Ensure `AI_PROVIDER` is set (`ollama` or `mistral`). If using Mistral, supply `MISTRAL_API_KEY`.

### 3. Initialize & Seed Database
```bash
# Seed the development database (clears and recreates tables automatically)
python seed.py
```

### 4. Start Local AI Services (Ollama)
Ensure Ollama is running on your machine:
```bash
# Verify ollama is active
ollama list

# Pull the target model (e.g. gemma)
ollama pull gemma

# Start Ollama server
ollama run gemma
```

### 5. Launch Server
```bash
python run.py
```
Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

---

## Testing Credentials

The seed script creates the following testing accounts:

| Role | Email | Password |
| :--- | :--- | :--- |
| **System Admin** | `admin@waitwise.com` | `admin123` |
| **Staff Operator** | `staff@waitwise.com` | `staff123` |
| **Customer User** | `user1@waitwise.com` | `user123` |

---

## API Documentation

### Authentication
* `POST /api/auth/register` - Create account
* `POST /api/auth/login` - Secure login
* `POST /api/auth/logout` - Clear user session
* `GET /api/auth/me` - Inspect active user details

### Queues & Statuses
* `GET /api/queues` - List queues
* `GET /api/queues/<id>` - Fetch queue metadata
* `POST /api/queues/<id>/tokens` - Create sequential token for queue
* `GET /api/queues/<id>/status` - Fetch live serving & waiting counts

### Admin Operations
* `POST /api/admin/queues/<id>/next` - Advance queue and call next user
* `POST /api/admin/tokens/<id>/call` - Call specific waiting token
* `POST /api/admin/tokens/<id>/complete` - Mark active token as completed
* `POST /api/admin/tokens/<id>/skip` - Skip a token and notify user
* `POST /api/admin/queues/<id>/pause` - Temporarily lock queue joins
* `POST /api/admin/queues/<id>/resume` - Reopen queue joins
* `POST /api/admin/queues/<id>/reset` - Expire all tokens and reset counter

### AI Assistant
* `POST /api/ai/chat` - Chatbot interface for users
* `POST /api/ai/analyze-queue` - Diagnostic logs analysis
* `POST /api/ai/admin-insight` - Aggregated performance reports for admin

---

## Running Automated Tests

Run the testing suite using pytest:
```bash
pytest tests/ -v
```
All tests use an in-memory SQLite database, isolating tests from your development database.
