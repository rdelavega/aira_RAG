import time
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM
from sentence_transformers import CrossEncoder
from get_embedding_function import get_embedding_function

CHROMA_PATH = "chroma"

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

chat_history = []

PROMPT_TEMPLATE = """
You answer questions using ONLY the provided context.

Rules:
- If the answer is not in the context, say:
  "En base a los documentos proporcionados, no lo sé."
- Quote the relevant sentence from the context.
- Then explain briefly in 3-4 sentences.

Conversation History:
{history}

Context:
{context}

Question:
{question}

Answer:
"""


def main():

    print("\nAIRA Chat (type 'exit' to quit)\n")

    while True:

        query_text = input("You: ")

        if query_text.lower() == "exit":
            print("Bye bye!")
            break

        query_rag(query_text)


embedding_function = get_embedding_function()

db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

model = OllamaLLM(model="mistral:7b", num_predict=350, temperature=0.2, streaming=True)


def rerank_documents(query, docs, top_k=3):

    pairs = [(query, doc.page_content) for doc in docs]

    scores = reranker.predict(pairs)

    scored_docs = list(zip(docs, scores))

    scored_docs.sort(key=lambda x: x[1], reverse=True)

    return [doc for doc, _ in scored_docs[:top_k]]


def extract_relevant_sentences(query, docs):

    keywords = query.lower().split()

    filtered = []

    for doc in docs:

        sentences = doc.page_content.split(". ")

        relevant = [s for s in sentences if any(word in s.lower() for word in keywords)]

        filtered.append(". ".join(relevant))

    return filtered


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

    response = model.invoke(query_prompt)

    queries = [
        q.strip("- ").strip().strip('"') for q in response.split("\n") if q.strip()
    ]

    return queries[:3]


def query_rag(query_text: str):

    global chat_history
    start = time.time()
    queries = generate_queries(query_text)

    queries = list(set(queries))
    print("query generation:", time.time() - start)

    all_docs = []

    for q in queries:
        results = db.similarity_search_with_score(q, k=12)
        all_docs.extend([doc for doc, _ in results])

    unique_docs = list({doc.page_content: doc for doc in all_docs}.values())

    docs = rerank_documents(query_text, unique_docs, top_k=3)

    # context_text = "\n\n---\n\n".join([doc.page_content for doc in docs])

    # filtered_docs = extract_relevant_sentences(query_text, docs)

    # context_text = "\n\n".join(
    #     [f"[Document {i+1}]\n{text}" for i, text in enumerate(filtered_docs)]
    # )
    context_text = "\n\n---\n\n".join([doc.page_content for doc in docs])

    history_text = format_history()

    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

    prompt = prompt_template.format(
        history=history_text, context=context_text, question=query_text
    )

    print("Prompt chars:", len(prompt))

    start = time.time()

    response_text = "AIRA: "

    for chunk in model.stream(prompt):
        print(chunk, end="", flush=True)
        response_text += chunk

    print("\nllm:", time.time() - start)

    update_history(query_text, response_text)

    sources = [doc.metadata.get("id", None) for doc in docs]

    print("\nFuentes:", sources)

    return response_text


def format_history():

    history_text = ""

    for message in chat_history:
        role = message["role"]
        content = message["content"]

        if role == "user":
            history_text += f"Q: {content}\n"
        else:
            history_text += f"A: {content}\n"

    return history_text


def update_history(user, ai):

    chat_history.append({"role": "user", "content": user})

    chat_history.append({"role": "assistant", "content": ai})

    trim_history()


def trim_history():

    MAX_MESSAGES = 4

    global chat_history

    if len(chat_history) > MAX_MESSAGES:
        chat_history = chat_history[-MAX_MESSAGES:]


if __name__ == "__main__":
    main()
