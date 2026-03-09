# AIRA - Artificial Intelligence Research Assistant

A local AI-powered document analysis and knowledge synthesis system using Retrieval-Augmented Generation (RAG) with Ollama and ChromaDB.

## Overview

AIRA is a research assistant that allows you to chat with your documents using local AI models. It processes PDF documents, creates embeddings, and provides conversational answers based on the content using advanced retrieval and reranking techniques.

## Features

- **Local AI**: Uses Ollama with Mistral 7B model for privacy and offline operation
- **Document Processing**: Automatically loads and processes PDF documents from a data directory
- **Vector Search**: Employs ChromaDB for efficient similarity search with HuggingFace embeddings (BAAI/bge-m3)
- **Advanced Retrieval**: Multi-query generation and document reranking using Cross-Encoder for improved relevance
- **Conversational Memory**: Maintains chat history for context-aware responses
- **Streaming Responses**: Real-time response generation with streaming output

## Prerequisites

- Python 3.8+
- Ollama installed and running locally
- Mistral 7B model downloaded via Ollama (`ollama pull mistral:7b`)

## Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd aira
   ```

2. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Ensure Ollama is running:

   ```bash
   ollama serve
   ```

4. Pull the required model:
   ```bash
   ollama pull mistral:7b
   ```

## Usage

### 1. Prepare Your Documents

Place your PDF documents in the `backend/data/` directory.

### 2. Populate the Database

Run the database population script to process and index your documents:

```bash
cd backend
python populate_database.py
```

To reset the database and reprocess all documents:

```bash
python populate_database.py --reset
```

### 3. Start the Chat Interface

Launch the interactive chat system:

```bash
python chat.py
```

Type your questions and get AI-powered answers based on your documents. Type 'exit' to quit.

## Project Structure

```
aira/
├── README.md
├── requirements.txt
└── backend/
    ├── chat.py                 # Main chat interface with RAG
    ├── populate_database.py    # Document processing and indexing
    ├── get_embedding_function.py # Embedding configuration
    ├── chroma/                 # Vector database storage
    └── data/                   # Directory for PDF documents (create this)
```

## How It Works

1. **Document Loading**: PDFs are loaded using LangChain's PyPDFDirectoryLoader
2. **Text Splitting**: Documents are split into manageable chunks (500 chars with 100 char overlap)
3. **Embedding**: Chunks are embedded using BAAI/bge-m3 model via HuggingFace
4. **Storage**: Embeddings are stored in ChromaDB with unique IDs
5. **Query Processing**: User queries generate multiple search variations
6. **Retrieval**: Similarity search finds relevant document chunks
7. **Reranking**: Cross-encoder reranks results for better relevance
8. **Generation**: Mistral model generates answers using retrieved context and chat history

## Configuration

- **Embedding Model**: BAAI/bge-m3 (configured in `get_embedding_function.py`)
- **LLM**: Mistral 7B via Ollama (configured in `chat.py`)
- **Chunk Size**: 500 characters with 100 character overlap
- **Reranking**: Top 3 documents after reranking
- **Chat History**: Last 4 messages maintained

## Dependencies

Key libraries used:

- LangChain: For document processing and LLM integration
- ChromaDB: Vector database for embeddings
- HuggingFace Transformers: For embedding generation
- Sentence Transformers: For document reranking
- Ollama: Local LLM serving

See `requirements.txt` for complete dependency list.

## Troubleshooting

- Ensure Ollama is running before starting the chat
- Check that PDF files are in the `data/` directory
- For GPU acceleration, modify device settings in embedding function
- Monitor token limits for long documents
