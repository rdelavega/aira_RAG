# AIRA Architecture

This document describes the technical architecture of AIRA (Artificial Intelligence Research Assistant), including component design, data flows, and system interactions.

## System Overview

AIRA is a distributed system for intelligent document analysis and retrieval-augmented generation (RAG) using local language models. The system consists of three main layers:

1. **API Layer**: FastAPI backend providing REST endpoints
2. **RAG Processing Layer**: Document indexing and query processing
3. **Integration Layer**: Agent orchestration, Telegram notifications, Obsidian vault management
4. **Storage Layer**: Vector database (ChromaDB) and file storage

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface                          │
│  (Web UI, CLI, Telegram, Obsidian)                          │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼──────┐  ┌────▼──────┐  ┌────▼──────┐
    │ FastAPI   │  │ OpenClaw  │  │ Telegram  │
    │ Server    │  │ Agent     │  │ Bot       │
    │ (8000)    │  │ (18789)   │  │           │
    └────┬──────┘  └────┬──────┘  └───────────┘
         │               │
         └───────────────┼───────────────┐
                         │               │
    ┌────────────────────▼────┐    ┌────▼──────────┐
    │   RAG Pipeline           │    │   Obsidian    │
    │  ┌──────────────────┐   │    │   Vault       │
    │  │ Query Processing │   │    │   Manager     │
    │  ├──────────────────┤   │    └───────────────┘
    │  │ Embedding Gen    │   │
    │  ├──────────────────┤   │
    │  │ VectorDB Search  │   │
    │  ├──────────────────┤   │
    │  │ LLM Response     │   │
    │  └──────────────────┘   │
    └────────────────────┬───┘
                         │
    ┌────────────────────▼──────────────┐
    │      Storage Layer                 │
    │  ┌──────────┐  ┌──────────────┐  │
    │  │ ChromaDB │  │ PDF Inbox    │  │
    │  │(Vector)  │  │(Documents)   │  │
    │  └──────────┘  └──────────────┘  │
    └────────────────────────────────────┘

    External Services:
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ Ollama   │  │ Ollama   │  │ Telegram │
    │ (LLMs)   │  │ (Embed)  │  │ API      │
    └──────────┘  └──────────┘  └──────────┘
```

## Component Architecture

### 1. API Layer (FastAPI)

**Purpose**: Expose REST endpoints for document management and chat operations

**File**: `backend/api/main.py`

**Key Endpoints**:

- `GET /health` - Service health check
- `POST /chat` - Streaming chat with RAG context
- `POST /upload` - Document file upload
- `POST /populate` - Database population
- `POST /ingest` - Single document ingestion

**Features**:

- CORS middleware for cross-origin requests
- Streaming responses using Server-Sent Events (SSE)
- Background task processing for async operations
- Telegram notifications on document completion

**Models**:

```python
ChatRequest:
  - question: str        # User query
  - scope: Optional[str] # Filter by document folder
```

### 2. RAG Processing Layer

#### 2.1 Query Processing (`backend/rag/chat.py`)

**Responsibility**: Handle user queries with retrieval-augmented generation

**Pipeline**:

1. Generate multiple search queries from user input
2. Search vector database with each query
3. Deduplicate and rerank results
4. Assemble prompt with context
5. Stream LLM response

**Key Functions**:

- `query_rag(query_text, scope)` - Main RAG pipeline
- `generate_queries(question)` - Multi-query generation using LLM
- `rerank_documents(query, docs, top_k)` - Document ranking
- `format_history()` - Format chat history for context
- `update_history(user, ai)` - Maintain conversation history

**Conversation History**:

- Maintains in-memory chat history
- Trimmed to prevent context explosion
- Included in every prompt for context awareness

#### 2.2 Document Processing (`backend/rag/populate_database.py`)

**Responsibility**: Index documents into vector database

**Supported Formats**:

- PDF files (via PyPDFLoader)
- Markdown files (via UnstructuredMarkdownLoader)
- Text files

**Processing Pipeline**:

1. Load documents from directory or single file
2. Split into chunks (500 chars, 100 char overlap)
3. Generate embeddings for each chunk
4. Store embeddings and metadata in ChromaDB

**Key Functions**:

- `populate_database(reset)` - Batch index all documents
- `ingest_document(file_path)` - Index single document
- `load_documents()` - Load from fs
- `split_documents(docs)` - Chunk documents
- `add_to_chroma(chunks)` - Store embeddings

#### 2.3 Embedding Function (`backend/rag/get_embedding_function.py`)

**Model**: BAAI/bge-m3 via Ollama

- Dimensions: 384
- Multilingual capabilities
- Optimized for semantic search

**Configuration**:

- Uses Ollama for local inference
- Configurable via OLLAMA_HOST environment variable
- Automatic caching by HuggingFace Hub

### 3. Vector Database (ChromaDB)

**Purpose**: Persistent storage and retrieval of document embeddings

**Location**: `backend/chroma/`

**Schema**:

```
Collection: documents
├── id: string (unique identifier)
├── embedding: vector[384] (BAAI/bge-m3)
├── document: string (chunk content)
├── page_content: string (full text)
└── metadata:
    ├── source: string (document filename)
    ├── page: int (page number)
    └── carpeta: string (scope/folder)
```

**Operations**:

- Similarity search with filters
- Metadata-based filtering
- Deduplication by content
- Persistent storage on disk

**Search Strategy**:

- K=12 initial results per query
- Scope-based filtering via metadata
- Similarity score weighting

### 4. LLM Integration (Ollama)

**Model**: LLaMA 3.2 1B

- Parameters: 1 billion
- Quantization: Q4 (optimized)
- Context window: 8K tokens
- Speed: ~50-100 tokens/second (CPU-dependent)

**Configuration** (via `backend/rag/chat.py`):

```python
OllamaLLM(
    model="llama3.2:1b",
    num_predict=350,      # Max output tokens
    temperature=0.2,      # Deterministic responses
    streaming=True        # Stream tokens as generated
)
```

**Prompt Template**:

```
[Conversation History]
[Retrieved Context]
[User Question]
Generate answer based on context only
```

### 5. Agent Layer (OpenClaw)

**Purpose**: Intelligent workflow automation and multi-channel integration

**Components**:

- **Gateway**: Main agent service with Telegram bridge
- **CLI**: Command-line interface for manual operations
- **Skills**: Custom domain logic modules

**Skills Included**:

- `obsidian/`: Vault manipulation and note generation
- `spanish/`: Spanish language processing
- `example/`: Template for custom skills

**Configuration**: `config/openclaw.json`

### 6. Obsidian Vault Integration

**Responsibility**: Automatic note generation and knowledge base management

**Features** (Planned):

- Chapter extraction and organization
- Exam question generation
- Note generation from indexed documents
- Draft creation in Obsidian inbox

**File**: `backend/rag/obsidian_writer.py`

## Data Flow

### Document Ingestion Flow

```
User
  │
  ├─(Upload via Web UI or API)──→ FastAPI /upload
  │                               │
  │                               ├─(Store uploaded file)
  │                               │
  │                               ├─(Queue background task)
  │                               │
  │                               └─→ run_ingest()
  │                                  │
  │                                  ├─(Load PDF/MD)
  │                                  │
  │                                  ├─(Split into chunks)
  │                                  │
  │                                  ├─(Generate embeddings)
  │                                  │
  │                                  ├─(Store in ChromaDB)
  │                                  │
  │                                  └─(Notify Telegram)
  │
  └─(Telegram Notification)←────────┘
```

### Query Processing Flow

```
User Question
  │
  ├─────→ FastAPI /chat
  │
  ├─────→ generate_queries()
  │       │ LLM generates 3 search variations
  │       └─→ ["query1", "query2", "query3"]
  │
  ├─────→ For each query:
  │       │ similarity_search(query, k=12)
  │       │
  │       └─→ Collect results with scores
  │
  ├─────→ Deduplication
  │       │ Merge duplicate chunks
  │       │
  │       └─→ List of unique documents
  │
  ├─────→ rerank_documents()
  │       │ Select top-3 most relevant
  │       │
  │       └─→ Final context documents
  │
  ├─────→ Build prompt:
  │       │ [History] + [Context] + [Question]
  │       │
  │       └─→ Send to LLM
  │
  ├─────→ LLM Response (streaming)
  │       │ model.stream(prompt)
  │       │
  │       └─→ Yield tokens as they arrive
  │
  └─────→ Update chat history + Return sources
```

### Event Streaming

The `/chat` endpoint uses Server-Sent Events (SSE) for real-time response streaming:

```
Client                          Server
  │                               │
  ├─ POST /chat ─────────────────→│
  │                               │
  ├─ GET<event-stream>←──────────│ data: {"type": "chunk", "content": "token"}
  │                               │
  │◄──────────────────────────────│ data: {"type": "chunk", "content": "..."}
  │
  │◄──────────────────────────────│ data: {"type": "sources", "content": [...]}
  │
  │                               │
  └─ Close connection ────────────→│
```

## Database Schema

### ChromaDB Collection: documents

**Metadata Fields**:

```json
{
  "id": "uuid-or-content-hash",
  "embedding": [...384 floats...],
  "document": "chunk text content",
  "metadata": {
    "source": "document-name.pdf",
    "page": 1,
    "carpeta": "10_Books"
  }
}
```

**Key Indexes**:

- Primary: id
- Semantic: embedding vector
- Filter: carpeta (for scope queries)

## Communication Protocols

### FastAPI to Client

- **Protocol**: HTTP/1.1 or HTTP/2
- **Endpoints**: REST JSON API
- **Streaming**: Server-Sent Events (text/event-stream)
- **Authentication**: CORS open (configurable)

### FastAPI to Ollama

- **Protocol**: HTTP
- **Port**: 11434
- **Format**: JSON
- **Operations**: Model inference, embeddings

### FastAPI to OpenClaw

- **Protocol**: HTTP
- **Port**: 18789
- **Messages**: JSON commands
- **Notifications**: Telegram bridge

### Telegram Integration

- **Protocol**: HTTPS (Telegram Bot API)
- **Trigger**: Document processing completion
- **Format**: Plain text messages via openclaw CLI

## Deployment Architecture

### Local Development

```
Host Machine
├── Ollama (port 11434)
├── Python venv
├── FastAPI dev server (port 8000)
├── ChromaDB (local directory)
└── PDFs (data/documents/)
```

### Docker Deployment

```
Host Machine
│
└── Docker Network: aira-net (bridge)
    │
    ├── Container: fastapi
    │   ├── Port: 8000->8000
    │   ├── Volumes:
    │   │   ├── /vault (RO Obsidian)
    │   │   ├── chroma_data (ChromaDB)
    │   │   ├── pdf_inbox (Documents)
    │   │   └── hf_cache (HF Hub cache)
    │   └── Networks: aira-net
    │
    ├── Container: openclaw-gateway
    │   ├── Port: 18789->18789
    │   ├── Volumes:
    │   │   ├── /vault (RO Obsidian)
    │   │   ├── ./config/openclaw.json
    │   │   ├── ./config/skills
    │   │   └── ./config/agent
    │   └── Networks: aira-net
    │
    └── Container: openclaw-cli (on-demand)
        ├── Profile: cli
        └── Networks: aira-net

Host Services (External)
├── Ollama (accessed via 172.17.0.1:11434)
├── Telegram API (HTTPS)
└── HuggingFace Hub (HTTPS)
```

### Configuration Files

**Environment** (`.env`):

- VAULT_PATH: Obsidian vault location
- OLLAMA_HOST: Ollama server endpoint
- TELEGRAM_CHAT_ID: Notification recipient
- (Optional) API keys for external services

**Docker Compose** (`docker-compose.yml`):

- Service definitions
- Volume mounts
- Network configuration
- Environment injection

**OpenClaw** (`config/openclaw.json`):

- Agent settings
- Skill configuration
- Telegram credentials
- Behavior parameters

## Performance Characteristics

### Throughput

- **Document indexing**: ~10-50 PDFs/minute (CPU-dependent)
- **Query processing**: 2-5 seconds (including LLM time)
- **Token generation**: 50-100 tokens/second at 1B model
- **Embedding generation**: 100-500 chunks/minute

### Latency

- API response time: <100ms (excluding LLM)
- Multi-query generation: 1-2 seconds
- Vector search: <100ms
- LLM inference: 3-7 seconds (varies by response length)
- **Total query latency**: 4-10 seconds typically

### Memory Usage

- FastAPI process: ~200-300 MB
- LLaMA 3.2 1B model: ~2-2.5 GB (quantized)
- ChromaDB: 100-500 MB (varies by document count)
- **Total**: ~2.5-3.5 GB recommended

### Storage

- LLaMA 3.2 model: ~600 MB (Q4 quantized)
- HuggingFace embeddings: ~200 MB
- ChromaDB database: ~50-100 MB per 1000 documents
- **Total**: 1-2 GB for typical setup

## Security Considerations

### Data Privacy

- ✅ All processing local (no cloud APIs for core functions)
- ✅ Ollama runs locally
- ✅ Embeddings generated locally
- ⚠️ Ollama host accessible from Docker (configure firewall)

### API Security

- CORS enabled for all origins (production: restrict)
- No authentication on FastAPI endpoints (add if needed)
- Background tasks process files in `/data/documents/`
- File upload validation recommended

### Vault Access

- Obsidian vault mounted read-only (recommended)
- Agent can generate notes with proper permissions
- Consider SELinux/AppArmor for container isolation

## Scalability Considerations

### Horizontal Scaling

- FastAPI can be scaled behind load balancer
- Independent ChromaDB instance via remote connection
- Multiple Ollama instances for parallel inference
- Async task queue for document processing (Redis/Celery)

### Vertical Scaling

- Larger LLM models (7B, 13B) need more VRAM
- Multiple embeddings in parallel
- Batch processing for bulk ingestion
- GPU acceleration for Ollama

### Optimization

- Implement document caching layer
- Query result caching with TTL
- Batch embedding generation
- Async I/O for file operations

## Error Handling

### Document Processing

- Invalid file format → Skip with notification
- Corrupt PDF → Log error, continue
- Out of memory → Queue and retry

### Query Processing

- Ollama unavailable → Return error response
- No embeddings found → Return "not found" message
- LLM error → Return error to user

### Storage

- ChromaDB corruption → Reset and reingest
- Disk full → Alert and stop ingestion
- File permissions → Log and skip

## Future Architecture Enhancements

- [ ] GraphQL API for flexible queries
- [ ] Real-time collaboration features
- [ ] Multi-tenant support
- [ ] Advanced caching layer (Redis)
- [ ] GPU-accelerated embeddings
- [ ] Distributed vector database
- [ ] Advanced authentication/authorization
- [ ] API rate limiting and quotas
- [ ] Comprehensive logging and monitoring
- [ ] WebSocket support for real-time chat
