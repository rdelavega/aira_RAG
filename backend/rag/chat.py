from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM
from rag.get_embedding_function import get_embedding_function
from typing import Optional
import os

CHROMA_PATH = "chroma"


PROMPT_TEMPLATE = """
You answer questions using ONLY the provided context.

Rules:
- If the answer is not in the context, say:
  "En base a los documentos proporcionados, no lo sé."
- Quote the relevant sentence from the context.
- Then explain briefly in 3-4 sentences.

Context:
{context}

Question:
{question}

Answer:
"""


embedding_function = get_embedding_function()

db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2:3b")

model = OllamaLLM(
    model=OLLAMA_CHAT_MODEL,
    base_url=OLLAMA_HOST,
    num_predict=350,
    temperature=0.2,
    streaming=True,
)


def rerank_documents(query, docs, top_k=3):

    return docs[:top_k]


def generate_queries(question: str):

    query_prompt = f"""
Generate 3 different search queries for document retrieval.

Each query must use a different perspective:

1. Direct question
2. Rule explanation
3. Scenario description

Question: {question}

Queries:
"""

    try:
        response = model.invoke(query_prompt)
        queries = [
            q.strip("- ").strip().strip('"') for q in response.split("\n") if q.strip()
        ]
        return queries[:3] if queries else [question]
    except Exception as e:
        # If query-expansion model is unavailable, continue with the original query.
        print(f"Query expansion disabled, using raw query only: {e}")
        return [question]


def query_rag(query_text: str, scope: str = None):
    docs, sources = retrieve_documents(query_text, scope=scope, top_k=3)
    context_text = "\n\n---\n\n".join([doc.page_content for doc in docs])
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE).format(
        context=context_text, question=query_text
    )
    for chunk in model.stream(prompt):
        yield {"type": "chunk", "content": chunk}
    yield {"type": "sources", "content": sources}


def query_rag_sync(query_text: str, scope: str = None) -> dict:
    docs, sources = retrieve_documents(query_text, scope=scope, top_k=3)
    context_text = "\n\n---\n\n".join([doc.page_content for doc in docs])
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE).format(
        context=context_text, question=query_text
    )
    answer = model.invoke(prompt)
    compact_sources = [
        {"filename": s["filename"], "snippet": s["snippet"]}
        for s in sources
    ]
    return {"answer": answer, "sources": compact_sources}


def retrieve_documents(
    query_text: str,
    scope: Optional[str] = None,
    top_k: int = 3,
    k_per_query: int = 12,
):
    queries = generate_queries(query_text)
    queries = list(set(queries + [query_text]))

    all_results = []
    for q in queries:
        if scope:
            results = db.similarity_search_with_score(
                q, k=k_per_query, filter={"carpeta": scope}
            )
        else:
            results = db.similarity_search_with_score(q, k=k_per_query)
        all_results.extend(results)

    best_by_content = {}
    for doc, score in all_results:
        key = doc.page_content
        if key not in best_by_content or score < best_by_content[key][1]:
            best_by_content[key] = (doc, score)

    deduped = list(best_by_content.values())
    deduped.sort(key=lambda item: item[1])
    ranked_docs = [doc for doc, _ in deduped]
    docs = rerank_documents(query_text, ranked_docs, top_k=top_k)

    score_by_content = {doc.page_content: score for doc, score in deduped}
    sources = []
    for doc in docs:
        snippet = doc.page_content[:240].replace("\n", " ").strip()
        if len(doc.page_content) > 240:
            snippet += "..."
        sources.append(
            {
                "id": doc.metadata.get("id"),
                "filename": doc.metadata.get("filename"),
                "source": doc.metadata.get("source"),
                "page": doc.metadata.get("page"),
                "score": score_by_content.get(doc.page_content),
                "snippet": snippet,
            }
        )

    return docs, sources


