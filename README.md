# BRS Prototype

This repository contains a working prototype of the Business Registration
System (BRS) described in the provided Business Requirements
Specification (BRS) document. The goal of this prototype is to
demonstrate a modular architecture across a PostgreSQL database,
a Python/FastAPI backend, a unified React front‑end for all roles,
and optional automation workflows via n8n. The OpenAI
API is integrated to show how large language models can augment the
workflow by summarising student justifications and providing intelligent
assistance.

## Project Structure

```
brs_prototype/
├── backend/           # FastAPI application with modular structure
│   ├── brs_backend/   # Main application module
│   │   ├── main.py    # FastAPI app entry point
│   │   ├── core/      # Configuration and logging
│   │   ├── database/  # Database connection
│   │   ├── models/    # SQLAlchemy models
│   │   ├── agents/    # AI agents and tools
│   │   ├── api/       # REST API endpoints
│   │   └── seed_personas.py # Database seeding
│   ├── entrypoint.sh  # Docker container startup
│   └── README.md      # Backend documentation
├── database/          # SQL schema definitions
├── frontend/          # Unified React UI for all roles
├── n8n/               # Example n8n workflow definitions
└── README.md          # You are here
```

## Quick Start with Docker

The fastest way to get started is using Docker Compose, which will automatically set up the database, backend, and frontend:

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env and configure your OpenAI API key
# OPENAI_API_KEY=your-openai-api-key-here

# 3. Launch the entire application stack
docker-compose up --build -d

# 4. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# Health Check: http://localhost:8000/health
```

### Prerequisites
- Docker & Docker Compose
- Optional: OpenAI API key for AI chatbot functionality (or Ollama for local AI)

## Architecture Overview

The BRS prototype follows a modern **microservices architecture** with clear separation of concerns, designed for scalability and maintainability. The system is **fully containerized** using Docker and orchestrated with Docker Compose for easy deployment and development.

### System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (React SPA)   │◄──►│  (FastAPI)      │◄──►│  (PostgreSQL)   │
│   Port 3000     │    │   Port 8000     │    │   Port 5432     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   OpenAI API    │
                       │ (AI Assistant)  │
                       └─────────────────┘
```

### Technology Stack

#### Frontend Layer
- **React 18** - Modern component-based UI library
- **Vite** - Fast build tool and development server
- **JavaScript (ES6+)** - Modern JavaScript with async/await
- **CSS-in-JS** - Inline styling for component encapsulation
- **Fetch API** - HTTP client for backend communication

#### Backend Layer
- **FastAPI** - High-performance Python web framework
- **SQLAlchemy** - Object-Relational Mapping (ORM) for database operations
- **Pydantic** - Data validation and serialization
- **Uvicorn** - ASGI server for serving the FastAPI application
- **OpenAI API** - Large Language Model integration for intelligent assistance
- **Python 3.11** - Modern Python runtime

#### Database Layer
- **PostgreSQL 14** - Relational database with ACID compliance
- **SQLAlchemy Core/ORM** - Database abstraction and query building
- **Connection Pooling** - Efficient database connection management

#### Infrastructure & DevOps
- **Docker** - Containerization platform
- **Docker Compose** - Multi-container application orchestration
- **uv** - High-performance Python package manager
- **Node.js** - JavaScript runtime for frontend tooling

## Current Features

### 🤖 AI-Powered Chatbot Interfaces
- **Natural Language Processing** - Students can request courses using conversational language
- **Function Calling Integration** - Structured intent detection with OpenAI API
- **Markdown Rendering** - Properly formatted AI responses with headers, lists, and emphasis
- **Fallback Detection** - Keyword-based processing when function calling unavailable
- **Multi-Model Support** - Compatible with OpenAI GPT models and local Ollama models

### 📚 Course Management
- **Enrollment Requests** - "I want to add CS201" or "Enroll me in database systems"
- **Course Dropping** - "Remove CS101 from my schedule" or "Drop linear algebra"
- **Status Checking** - "What's the status of my CS201 request?" or "Show my current courses"
- **Course Discovery** - "What courses are available?" or "Show me computer science classes"
- **Recent Updates** - Automatic highlighting of course changes since last login

### 👥 Role-Based Workflows
- **Students** - Conversational course management with AI assistance
- **Advisors** - AI-enhanced request review with intelligent summaries
- **Department Heads** - Final approval authority with context-aware recommendations
- **Administrators** - User management and system oversight

### 🔧 Technical Capabilities
- **Docker Containerization** - One-command deployment with `docker-compose up`
- **Database Management** - PostgreSQL with automatic schema creation and seeding
- **API Integration** - RESTful endpoints with comprehensive error handling
- **Environment Flexibility** - Support for both cloud (OpenAI) and local (Ollama) AI services
- **Development Tools** - Hot reload, logging, and health monitoring

### Key Components

#### 1. Chatbot-Powered Student Interface
- **Natural Language Processing** - Students interact using conversational language
- **OpenAI Integration** - Intelligent responses and course recommendations
- **Real-time Chat UI** - Modern messaging interface with message history
- **Fallback Traditional Forms** - Backup interface when AI is unavailable
- **Request Status Tracking** - Visual indicators for request progress

#### 2. RESTful API Architecture
- **Resource-Based Endpoints** - `/users/`, `/requests/`, `/courses/`, `/chat`
- **HTTP Method Semantics** - GET for retrieval, POST for creation
- **JSON Data Exchange** - Standardized data format
- **Error Handling** - Comprehensive HTTP status codes and error messages
- **CORS Support** - Cross-origin requests for frontend integration

#### 3. Database Schema Design
```sql
users              courses            sections           requests
├── id (PK)        ├── id (PK)        ├── id (PK)        ├── id (PK)
├── username       ├── code           ├── course_id (FK) ├── student_id (FK)
├── full_name      ├── name           ├── section_code   ├── course_id (FK)
├── role           ├── description    ├── schedule       ├── request_type
├── major          └── ...            ├── capacity       ├── status
├── gpa                               ├── instructor     ├── justification
└── ...                               └── seats_taken    └── timestamps
```

#### 4. Role-Based Access Control
- **Student Portal** - Course management via chatbot interface
- **Advisor Dashboard** - Request review and approval workflows
- **Department Head Interface** - Final decision authority for referred requests
- **Admin Panel** - User management and system oversight

#### 5. Data Flow Architecture
```
User Input → Frontend Validation → API Request → Backend Processing → Database Query → Response → UI Update
                                        ↓
                                 OpenAI Integration (for chat)
```

### Security Considerations
- **Input Validation** - Pydantic models ensure data integrity
- **SQL Injection Prevention** - SQLAlchemy ORM parameterized queries
- **CORS Configuration** - Controlled cross-origin access
- **Error Message Sanitization** - No sensitive data exposure
- **Environment Variable Management** - Secure configuration handling

### Scalability Features
- **Containerized Architecture** - Easy horizontal scaling
- **Database Connection Pooling** - Efficient resource utilization
- **Stateless Backend** - Enables load balancing
- **Microservices Pattern** - Independent component scaling
- **API-First Design** - Frontend/backend decoupling

## Component Details

### Database Layer (PostgreSQL)

The SQL schema is defined in `database/create_tables.sql` and automatically initialized when the Docker container starts. The database includes:

- **Automatic Schema Creation** - Tables created on container startup
- **Data Seeding** - Pre-populated with personas from `backend/seed_personas.py`
- **Persistent Storage** - Data preserved across container restarts
- **Development Access** - Available at `localhost:5432` with credentials `postgres/postgres`

**Reset Database:**
```bash
docker-compose down -v  # Remove volume
docker-compose up -d    # Restart with fresh data
```

### Backend API (FastAPI)

The FastAPI application provides RESTful endpoints and AI-powered chat functionality:

**Key Features:**
- **OpenAI Integration** - Intelligent chatbot responses and function calling
- **Ollama Support** - Local AI models (qwen2.5vl, llama3.2, gemma3)
- **Automatic Health Checks** - AI service status monitoring
- **Request Processing** - Course enrollment, drop, and status tracking
- **Advisor Workflows** - Request review and approval system

**API Endpoints:**
- `GET /health` - System status and AI configuration
- `POST /chat` - Student chatbot interaction
- `POST /advisor-chat` - Advisor chatbot interface
- `GET /users/` - User management
- `POST /requests/` - Request submission
- `GET /requests/` - Request listing with filters

**Environment Configuration:**
```bash
# OpenAI API (recommended)
OPENAI_API_KEY=your-api-key
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo

# OR Ollama (local AI)
OPENAI_API_KEY=ollama
OPENAI_API_BASE=http://host.docker.internal:11434/v1
OPENAI_MODEL=gemma3:27b
```

### Frontend (React SPA)

A modern single-page application serving all user roles with **AI-powered interfaces**:

**Role-Based Interfaces:**
- **Students** - AI chatbot for natural language course management
  - "I want to enroll in CS201"
  - "What courses am I taking?"
  - "Drop my math class"
  - Real-time status updates with markdown rendering
- **Advisors** - Request review with AI assistance for processing
- **Department Heads** - Final decision authority with AI insights
- **Administrators** - User management and system oversight

**Key Features:**
- **Markdown Rendering** - Proper formatting of AI responses
- **Function Calling** - Structured AI interactions with fallback keyword detection
- **Real-time Updates** - Recent request changes highlighted for students
- **Consistent UI** - Unified chatbot interface across all roles
- **Error Handling** - Graceful degradation when AI services are unavailable

### AI Integration Capabilities

**OpenAI Function Calling:**
- Structured intent detection for course requests
- Automatic parameter extraction (course codes, justifications)
- Context-aware responses with course catalog integration

**Fallback Mechanisms:**
- Keyword detection when function calling fails
- Traditional form interface backup
- Error recovery with user guidance

**Supported AI Models:**
- **OpenAI**: GPT-3.5-turbo, GPT-4 (recommended for best function calling)
- **Ollama Local**: gemma3:27b, llama3.2, qwen2.5vl

### n8n Automation

Although a full n8n instance is not included, the `n8n/` folder
contains example workflow JSON files demonstrating how automation could
be used to send email notifications when a request status changes or
trigger reminders for advisors to process pending requests. Import
these files into your n8n instance to explore further.

## Extending the Prototype

This prototype demonstrates modern web application architecture with AI integration. Features to consider adding include:

### Core System Enhancements
* **Authentication and access control** (e.g. JWTs or session tokens).
* **Course and section catalog management** with real-time availability.
* **Student dashboards** showing graduation progress and degree requirements.
* **Integration with university systems** for real schedule updates.
* **Enhanced exception handling** for financial holds, prerequisite violations, and other cases described in the BRS document.

### AI and Chatbot Enhancements
* **Persistent chat history** across user sessions.
* **Course recommendation engine** based on student profile and academic history.
* **Multi-language support** for international students.
* **Voice interface integration** for accessibility.
* **Sentiment analysis** of student requests for proactive support.
* **Advanced NLP** for complex scheduling queries and constraint handling.

### Analytics and Insights
* **Request pattern analysis** to identify popular courses and bottlenecks.
* **Advisor workload balancing** through intelligent request routing.
* **Predictive modeling** for course demand forecasting.
* **Student success tracking** and intervention recommendations.

With its modular architecture, each component can evolve independently
while communicating via well‑defined APIs and a shared database.

## Running with Docker Compose

A `docker-compose.yml` file is provided to launch the entire stack with
a single command. It defines three services:

* **db** – a PostgreSQL database with persisted storage.
* **backend** – a FastAPI service built from `./backend`. It installs
  dependencies using the high‑performance `uv` tool, waits for the
  database to be ready, seeds the personas, and starts the API using
  Uvicorn.
* **frontend** – a static site built from `./frontend` and served via
  a lightweight Node HTTP server.

### Configuration

Before running the application, you need to configure your environment variables:

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file** and add your OpenAI API key:
   ```bash
   # Required for AI chatbot functionality
   OPENAI_API_KEY=your-actual-openai-api-key-here
   ```

3. **Launch the application:**
   ```bash
   docker-compose up --build
   ```

**Important:** Without a valid `OPENAI_API_KEY`, the AI chatbot will not function and students will see an error message directing them to use the traditional form interface.

### Services

The services will then be available at:

* **Front‑end:** <http://localhost:3000>
* **Backend API:** <http://localhost:8000>
* **Database:** `localhost:5432` with user/password `postgres`
* **Health Check:** <http://localhost:8000/health> (shows OpenAI configuration status)

### Environment Variables

The application supports the following environment variables in your `.env` file:

#### OpenAI Configuration (Cloud AI - Recommended)
```bash
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo
# Alternative: gpt-4 (better function calling support)
```

#### Ollama Configuration (Local AI - Alternative)
```bash
OPENAI_API_KEY=ollama
OPENAI_API_BASE=http://host.docker.internal:11434/v1
OPENAI_MODEL=gemma3:27b
# Alternatives: llama3.2:latest, qwen2.5vl:latest
```

#### Core Application Settings
```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@db:5432/brs_prototype_db

# Frontend Configuration
VITE_API_BASE=http://localhost:8000

# Optional: Development Settings
DEBUG=false
LOG_LEVEL=info
```

**Note:** The system will automatically fall back to keyword-based detection if AI function calling is not available.

## Troubleshooting

### Common Issues

#### AI Chatbot Not Working
**Problem:** Student gets error "AI assistant is not available"

**Solutions:**
1. **Check OpenAI API Key:**
   ```bash
   # Verify .env file has valid key
   cat .env | grep OPENAI_API_KEY
   ```

2. **Test API Connection:**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Alternative: Use Local AI (Ollama)**
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.ai/install.sh | sh

   # Download a model
   ollama pull gemma3:27b

   # Update .env for local AI
   OPENAI_API_KEY=ollama
   OPENAI_API_BASE=http://host.docker.internal:11434/v1
   OPENAI_MODEL=gemma3:27b
   ```

#### Database Connection Issues
**Problem:** Backend can't connect to database

**Solutions:**
1. **Reset Database:**
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

2. **Check Database Status:**
   ```bash
   docker-compose ps
   docker-compose logs db
   ```

#### Environment Variable Conflicts
**Problem:** Shell environment variables override .env file

**Solutions:**
1. **Unset Shell Variables:**
   ```bash
   unset OPENAI_API_KEY
   unset OPENAI_MODEL
   unset OPENAI_API_BASE
   ```

2. **Verify Docker Environment:**
   ```bash
   docker-compose config
   ```

#### Frontend Build Issues
**Problem:** Frontend fails to start or build

**Solutions:**
1. **Clear Node Modules:**
   ```bash
   docker-compose down
   docker-compose build --no-cache frontend
   docker-compose up
   ```

2. **Check Frontend Logs:**
   ```bash
   docker-compose logs frontend
   ```

### Development Tips

#### Testing Different AI Models
```bash
# Test with OpenAI GPT-3.5
OPENAI_MODEL=gpt-3.5-turbo

# Test with GPT-4 (better function calling)
OPENAI_MODEL=gpt-4

# Test with local Ollama models
OPENAI_MODEL=llama3.2:latest
OPENAI_MODEL=qwen2.5vl:latest
```

#### Database Management
```bash
# View current data
docker exec -it brs_prototype_db-1 psql -U postgres -d brs_prototype_db

# Reset with fresh data
docker-compose down -v && docker-compose up -d

# Backup database
docker exec brs_prototype_db-1 pg_dump -U postgres brs_prototype_db > backup.sql
```

#### Log Monitoring
```bash
# Follow all logs
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Database only
docker-compose logs -f db
```

### Getting Help

If you encounter issues not covered here:

1. **Check Application Health:** Visit `http://localhost:8000/health`
2. **Review Logs:** Use `docker-compose logs -f` to see real-time output
3. **Verify Configuration:** Use `docker-compose config` to check environment variables
4. **Test API Manually:** Use `curl` or Postman to test backend endpoints
5. **Database Access:** Connect directly to PostgreSQL at `localhost:5432`

### Known Limitations

- **Function Calling:** Not all AI models support OpenAI function calling (fallback keyword detection available)
- **Markdown Rendering:** Complex markdown may not render perfectly in chat interface
- **Session Management:** No persistent user sessions across browser restarts
- **File Upload:** No support for document attachments in current version

## Current Status & Roadmap

### ✅ Completed Features
- **AI-Powered Chatbot Interface** - Full natural language processing for course management
- **Function Calling Integration** - Structured intent detection with OpenAI API
- **Fallback Mechanisms** - Keyword detection when function calling unavailable
- **Markdown Rendering** - Properly formatted AI responses in chat interface
- **Database Update Tracking** - Recent changes highlighted for students
- **Multi-Model Support** - Compatible with OpenAI GPT and local Ollama models
- **Docker Containerization** - One-command deployment with full environment setup
- **Comprehensive Documentation** - Complete setup and troubleshooting guides

### 🚀 Future Enhancements
- **Authentication System** - Secure login with JWT tokens
- **Real-time Notifications** - WebSocket integration for instant updates
- **Mobile Responsive Design** - Optimized interface for mobile devices
- **Advanced Analytics** - Course enrollment trends and system usage metrics
- **File Upload Support** - Document attachments for course requests
- **API Rate Limiting** - Production-ready API protection
- **Automated Testing** - Unit and integration tests for reliability

### 📊 Current Architecture Maturity
- **Development Ready:** ✅ Fully functional for demonstration and testing
- **Production Considerations:** ⚠️ Requires authentication, security hardening, and scaling considerations
- **AI Integration:** ✅ Production-ready with proper fallback mechanisms
- **Database Design:** ✅ Normalized schema with proper relationships and constraints

### 💡 Technology Decisions
The current implementation prioritizes **developer experience** and **rapid prototyping** while maintaining **production-quality code patterns**. The architecture supports easy migration to production with minimal changes required for authentication, security, and scaling.
