# AIRA - Artificial Intelligence Research Assistant

A comprehensive AI-powered document analysis and knowledge synthesis platform using Retrieval-Augmented Generation (RAG) with local LLMs, vector databases, and intelligent agent capabilities. AIRA integrates document indexing, conversational AI, Obsidian vault integration, and Telegram notifications for a complete research workflow.

## Overview

AIRA is an intelligent research assistant that enables you to:

- Chat with your PDF documents using local AI models
- Index and retrieve information from large document collections
- Generate automatic notes and summaries in Obsidian
- Receive AI-powered insights via Telegram
- Control AI agents for automated tasks
- Maintain context across multi-turn conversations

Built with privacy-first principles, AIRA runs entirely locally using Ollama, eliminating external API dependencies.

## Architecture

```
User
  ↓
FastAPI (RAG Engine)
  ├── Chat Interface (Streaming)
  ├── Document Ingestion
  └── RAG Pipeline
       ↓
    Vector DB (ChromaDB)
       ↓
    Obsidian Vault

Agent Layer (OpenClaw)
  ├── Telegram Integration
  ├── Custom Skills
  └── Automated Workflows
```

## Key Features

### Core RAG Capabilities

- **Local LLM**: Uses Ollama with LLaMA 3.2 (1B model) for privacy-first operation
- **Fast Embedding**: BAAI/bge-m3 model via HuggingFace for semantic search
- **Vector Database**: ChromaDB for efficient similarity search and retrieval
- **Multi-Query Generation**: Generates multiple search queries to improve document retrieval
- **Smart Reranking**: Filters and prioritizes most relevant documents
- **Streaming Responses**: Real-time response generation via Server-Sent Events (SSE)

### Document Management

- **PDF Ingestion**: Automatic processing and indexing of PDF documents
- **Chunking Strategy**: Intelligent text splitting (500 char chunks with 100 char overlap)
- **Background Processing**: Asynchronous document ingestion without blocking API
- **Scope Filtering**: Query documents within specific folders/scopes

### Integration Features

- **FastAPI Backend**: RESTful API with CORS support for frontend integration
- **OpenClaw Agent**: Intelligent agent layer for complex workflows
- **Telegram Integration**: Notifications and alerts via Telegram
- **Obsidian Sync**: Automatic note generation and vault synchronization
- **Docker Deployment**: Complete containerization with Docker Compose

## Prerequisites

- **Docker & Docker Compose**: For containerized deployment
- **Ollama**: Running locally (accessible at `http://localhost:11434`)
- **LLaMA 3.2 1B Model**: Auto-downloaded by Ollama
- **Obsidian Vault**: Path to your Obsidian vault for note generation
- **Telegram Bot** (optional): For notifications via OpenClaw

## Quick Start

### 1. Environment Configuration

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Configure these variables:

```env
VAULT_PATH=/path/to/your/obsidian/vault
OLLAMA_HOST=http://172.17.0.1:11434  # Host Ollama access from Docker
TELEGRAM_CHAT_ID=your-chat-id        # Optional: for notifications
```

### 2. Start Services

Launch all services with Docker Compose:

```bash
./start.sh
```

This initializes:

- **FastAPI RAG Engine** → `http://localhost:8000`
- **OpenClaw Agent** → `http://localhost:18789`
- **Ollama** → `http://localhost:11434`
- **Obsidian Vault** → Mounted and ready for note generation

### 3. Ingest Documents

Upload PDF documents via the API or CLI:

```bash
curl -X POST -F "files=@document.pdf" http://localhost:8000/upload
```

The system will:

1. Process the PDF
2. Generate embeddings
3. Index in ChromaDB
4. Notify via Telegram (if configured)
5. Generate Obsidian notes (planned enhancement)

### 4. Query Documents

Chat with your documents using the streaming API:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic?", "scope": null}' \
  -N
```

Or populate the database first:

```bash
curl -X POST http://localhost:8000/populate
```

## Project Structure

```
aira_RAG/
├── README.md                      # This file
├── ARCHITECTURE.md                # Detailed architecture documentation
├── docker-compose.yml             # Multi-container orchestration
├── requirements.txt               # Python dependencies
├── start.sh                       # Deployment initialization script
│
├── backend/
│   ├── Dockerfile                # FastAPI container
│   ├── api/
│   │   ├── main.py               # FastAPI application with endpoints
│   │   └── chroma/               # Vector database persistence
│   └── rag/
│       ├── chat.py               # RAG query pipeline with streaming
│       ├── populate_database.py  # Document indexing engine
│       ├── get_embedding_function.py  # Embedding configuration
│       └── obsidian_writer.py    # Note generation for Obsidian
│
├── config/
│   ├── openclaw.json             # Agent configuration
│   ├── openclaw.example.json     # Configuration template
│   ├── agent/
│   │   ├── auth-profiles.json    # Authentication settings
│   │   └── auth-profiles.example.json
│   └── skills/                   # Custom agent skills
│       ├── example/
│       ├── obsidian/             # Obsidian automation skills
│       └── spanish/              # Spanish language skills
```

## API Endpoints

### Health Check

```bash
GET /health
```

### Chat (Streaming)

```bash
POST /chat
Content-Type: application/json

{
  "question": "What is in the documents?",
  "scope": null  # Optional: filter by folder
}
```

Response: Server-Sent Events (SSE) stream

### Document Upload

```bash
POST /upload
Content-Type: multipart/form-data

files: [file1.pdf, file2.pdf, ...]
```

Response: Returns job IDs for background processing

### Database Population

```bash
POST /populate?reset=false
```

Populates ChromaDB with all indexed documents

## How It Works

### Document Processing Pipeline

1. **Upload**: PDF files uploaded via `/upload` endpoint
2. **Async Processing**: Files processed in background without blocking
3. **Text Extraction**: PDFs split into chunks (500 chars, 100 char overlap)
4. **Embedding**: Chunks embedded using BAAI/bge-m3 model
5. **Storage**: Embeddings stored in ChromaDB with metadata
6. **Notification**: User notified via Telegram when complete

### Query/RAG Pipeline

1. **Query Input**: User question received
2. **Multi-Query Generation**: LLM generates 3 different search queries
3. **Semantic Search**: Each query searches ChromaDB (k=12 results)
4. **Deduplication**: Duplicate results merged
5. **Reranking**: Top-3 most relevant documents selected
6. **Context Assembly**: Retrieved docs combined into context
7. **LLM Response**: LLaMA generates answer with context
8. **Streaming**: Response streamed to client in real-time

### Conversation Memory

- Maintains chat history during session
- Includes history in prompt for context-aware responses
- History used for multi-turn conversations

## Configuration

### OpenClaw Skills

Custom skills located in `config/skills/`:

- **spanish/**: Spanish language processing
- **obsidian/**: Vault manipulation and note generation
- **example/**: Template for custom skills

Configure in `config/openclaw.json`:

```json
{
  "skills": {
    "obsidian": { "enabled": true },
    "spanish": { "enabled": true }
  }
}
```

### LLM Parameters

Modify in `backend/rag/chat.py`:

```python
model = OllamaLLM(
    model="llama3.2:1b",
    num_predict=350,  # Max tokens
    temperature=0.2,  # Lower = more deterministic
    streaming=True
)
```

## Docker Compose Services

### FastAPI RAG Engine

- **Image**: Built from `backend/Dockerfile`
- **Port**: 8000
- **Volumes**:
  - Obsidian vault mount
  - ChromaDB persistence
  - PDF inbox
  - HuggingFace cache

### OpenClaw Gateway

- **Image**: `ghcr.io/openclaw/openclaw:latest`
- **Port**: 18789
- **Features**: Agent orchestration, Telegram integration

### OpenClaw CLI (Optional)

- **Profile**: `cli`
- **Usage**: Manual agent commands

## Development

### Local Setup (Without Docker)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Ensure Ollama is running
ollama serve

# Populate database
cd backend
python populate_database.py

# Start API
python api/main.py
```

### Accessing Logs

```bash
# View all logs
docker compose logs -f

# View specific service
docker compose logs -f fastapi
docker compose logs -f openclaw-gateway
```

### Stopping Services

```bash
# Stop all services
docker compose down

# Remove volumes (WARNING: Data loss)
docker compose down -v
```

## Key Dependencies

Core libraries used in AIRA:

- **LangChain**: Document processing, LLM orchestration, RAG pipeline
- **LangChain-Chroma**: Vector database integration
- **LangChain-Ollama**: Local LLM serving
- **ChromaDB**: Persistent vector storage with metadata filtering
- **HuggingFace Hub**: Embedding model distribution and caching
- **FastAPI**: High-performance REST API framework
- **Pydantic**: Data validation and serialization
- **PyPDF**: PDF document processing
- **Ollama**: Local LLM inference engine

See [requirements.txt](requirements.txt) for complete dependency list.

## Performance Optimization

### Vector Database

- ChromaDB supports persistent storage and fast similarity search
- Metadata filtering (`scope`) reduces search space
- Deduplication removes redundant chunks from multiple queries

### LLM Settings

- **Temperature 0.2**: Deterministic factual answers
- **Token Limit 350**: Concise responses within reasonable time
- **LLaMA 3.2 (1B)**: Balance quality vs speed on modest hardware

### Chunking Strategy

- 500 character chunks preserve context
- 100 character overlap prevents content loss at boundaries
- Embedding dimension: 384 (BAAI/bge-m3)

## Troubleshooting

### Services Won't Start

```bash
# Check Docker is running
docker ps

# View service logs
docker compose logs -f

# Verify Ollama is accessible
curl http://localhost:11434/api/tags
```

### No Documents Found

```bash
# Check database was populated
docker compose exec fastapi ls -la data/documents/

# Repopulate from scratch
docker compose exec fastapi python -m rag.populate_database --reset
```

### High Latency Responses

- Reduce `num_predict` in `backend/rag/chat.py` for shorter responses
- Reduce `k` parameter in similarity_search for fewer retrieved docs
- Ensure Ollama model is fully loaded: `ollama list`

### Out of Memory

- Reduce chunk size from 500 to 300 characters
- Switch to smaller embedding model (if available)
- Limit concurrent uploads in OpenClaw config

## Technology Stack

| Component         | Technology                | Purpose                       |
| ----------------- | ------------------------- | ----------------------------- |
| **Frontend**      | OpenClaw Web UI           | Agent orchestration interface |
| **Backend API**   | FastAPI                   | RESTful endpoints             |
| **LLM**           | Ollama + LLaMA 3.2        | Local inference               |
| **Embeddings**    | HuggingFace + BAAI/bge-m3 | Semantic search               |
| **Vector DB**     | ChromaDB                  | Persistent storage            |
| **Messaging**     | Telegram Bot              | Notifications                 |
| **Knowledge**     | Obsidian Vault            | Note management               |
| **Orchestration** | Docker Compose            | Containerization              |
| **Agents**        | OpenClaw                  | Workflow automation           |

## Future Enhancements

- [ ] Auto-generation of Obsidian notes from indexed documents
- [ ] Support for additional document formats (DOCX, TXT, Markdown)
- [ ] Advanced document relationships and knowledge graphs
- [ ] Fine-tuning capabilities for domain-specific tasks
- [ ] Multi-language support with automatic translation
- [ ] WebUI for document management and chat
- [ ] Export capabilities for summaries and insights
- [ ] Batch processing for large document sets

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. Check the repository for license details.

## Support

For issues, questions, or suggestions:

1. Check existing documentation in [ARCHITECTURE.md](ARCHITECTURE.md)
2. Review troubleshooting section above
3. Check Docker Compose logs for service errors
4. Open an issue on the repository

## Credits

Built with:

- **OpenClaw**: Intelligent agent framework
- **LangChain**: LLM orchestration framework
- **Ollama**: Local LLM runtime
- **ChromaDB**: Modern vector database
- **HuggingFace**: Open-source ML community
