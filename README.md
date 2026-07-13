# 🚀 CodePilot AI

**What is CodePilot AI?**

CodePilot AI is an AI-powered developer assistant that helps engineers understand, search, and interact with source code using Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG).

Instead of relying only on keyword search, CodePilot AI understands the semantic meaning of code, allowing developers to ask natural language questions and receive accurate, context-aware answers grounded in the actual repository.

---

## 🌟 What Can CodePilot AI Do?

### 🔐 Secure User Authentication
- User registration and login using JWT authentication.
- Secure password hashing with BCrypt.
- Protected API endpoints.

### 🔗 GitHub Integration
- Connect GitHub accounts using OAuth 2.0.
- Access user repositories securely.
- Retrieve repository metadata and repository lists.

### 📥 Repository Cloning
- Clone public and authorized private GitHub repositories.
- Store repositories locally in a workspace for analysis.
- Manage multiple repositories for different users.

### 📂 Intelligent Repository Indexing
- Scan the repository structure recursively.
- Ignore unnecessary files and folders (`.git`, `node_modules`, `venv`, binaries, etc.).
- Detect programming languages based on file extensions.
- Build an index of all source files for efficient processing.

### ✂️ Semantic Code Chunking
- Parse source code using language-aware strategies.
- Create chunks based on: Classes, Functions, Large methods, Remaining module-level code.
- Preserve metadata such as: Repository, File path, Language, Class name, Function name, Line numbers.
- Split oversized classes and functions into multiple overlapping chunks while maintaining context.

### 🧠 Embedding Generation
- Convert every code chunk into a high-dimensional embedding using an AI embedding model.
- Represent the semantic meaning of code rather than simple keywords.

### 🗄️ Vector Database Storage
- Store embeddings in ChromaDB.
- Save metadata alongside vectors for filtering.
- Support efficient similarity search across thousands of code chunks.

### 🔎 Semantic Code Search
- Search repositories using natural language instead of keywords.
- Retrieve the most relevant code snippets based on semantic similarity.
- Filter search results by repository and metadata.
- Rank results by similarity score.

### 🤖 AI-Powered Code Assistant (RAG)
- Combine semantic search with an LLM to answer repository-specific questions.
- Generate grounded explanations using retrieved source code.
- Avoid hallucinations by providing answers based on actual repository content.
- Include references to the source files and functions used in the answer.

### 💬 Natural Language Repository Chat
Developers can ask questions such as:
- *"How is JWT authentication implemented?"*
- *"Where is the database connection configured?"*
- *"Explain the GitHub OAuth flow."*
- *"Which service generates embeddings?"*
- *"How are repositories indexed?"*
- *"Where is SQLAlchemy initialized?"*

The assistant retrieves the relevant code and generates a contextual explanation.

### 📚 Conversation Management
- Maintain conversation history.
- Support multi-turn interactions.
- Provide context-aware follow-up responses.

### ⚡ High Performance
- Dockerized deployment.
- PostgreSQL for structured data.
- Redis for caching/background tasks.
- ChromaDB for vector search.
- Optimized indexing and retrieval pipeline.

### 🛡️ Production-Ready Architecture
- Modular FastAPI architecture.
- Repository pattern & Dependency injection.
- SQLAlchemy ORM & Alembic migrations.
- Structured logging & Error handling.
- Environment-based configuration.
- RESTful APIs with OpenAPI/Swagger documentation.

---

## 🏗️ Project Architecture

```
User
 │
 ▼
JWT Authentication
 │
 ▼
GitHub OAuth
 │
 ▼
Clone Repository
 │
 ▼
Index Files
 │
 ▼
Semantic Chunking
 │
 ▼
Generate Embeddings
 │
 ▼
Store in ChromaDB
 │
 ▼
Semantic Search
 │
 ▼
LLM
 │
 ▼
AI Response
```

---

## 🛠️ Tech Stack

### Backend
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Redis

### AI
- Grok / OpenAI Compatible API
- ChromaDB
- Embedding Models
- RAG Pipeline

### DevOps
- Docker
- Docker Compose

---

## 🚀 Installation & Setup

### Clone the Repository
```bash
git clone https://github.com/<username>/codepilot-ai.git
cd codepilot-ai
```

### Environment Variables
Create a `.env` file in the root directory:
```env
DATABASE_URL=
SECRET_KEY=

GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITHUB_CALLBACK_URL=

AI_API_KEY=
AI_MODEL=

CHROMA_DB_PATH=
```

### Run with Docker (Recommended)
```bash
docker compose up -d
```
The API will be available at `http://localhost:8000/docs`

### Manual Setup (Without Docker)

Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python -m venv venv
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Run FastAPI locally:
```bash
uvicorn app.main:app --reload
```

---

## 💡 Example Workflow

1. Register an account and login.
2. Connect your GitHub account via OAuth.
3. Select and clone a target repository.
4. Index the source code.
5. Generate semantic chunk embeddings and store in ChromaDB.
6. Ask natural language questions about the codebase.
7. Receive accurate, grounded AI-powered answers.

---

## 🚀 Future Improvements

- Multi-language parsing
- Organization support
- Incremental indexing
- Webhooks
- CI/CD
- Monitoring
- Role-based access

---

## 📝 License
MIT License
