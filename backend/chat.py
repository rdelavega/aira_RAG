import time
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM

from get_embedding_function import get_embedding_function

CHROMA_PATH = "chroma"

chat_history = []

PROMPT_TEMPLATE = """
You are an AI research assistant.

Use the following conversation history and context from documents to answer the question.

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
            break

        response = query_rag(query_text)

        print(f"\nAIRA: {response}\n")


def query_rag(query_text: str):

    global chat_history

    embedding_function = get_embedding_function()

    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    start = time.time()

    results = db.similarity_search_with_score(query_text, k=3)

    print("retrieval:", time.time() - start)

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])

    history_text = format_history()

    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

    prompt = prompt_template.format(
        history=history_text, context=context_text, question=query_text
    )

    model = OllamaLLM(model="llama3.2:3b", num_predict=150)

    start = time.time()

    response_text = model.invoke(prompt)

    print("llm:", time.time() - start)

    update_history(query_text, response_text)

    sources = [doc.metadata.get("id", None) for doc, _score in results]
    formatted_response = f"{response_text}\nFuentes: {sources}"
    return formatted_response


def format_history():

    history_text = ""

    for message in chat_history:
        role = message["role"]
        content = message["content"]

        history_text += f"{role}: {content}\n"

    return history_text


def update_history(user, ai):

    chat_history.append({"role": "user", "content": user})

    chat_history.append({"role": "assistant", "content": ai})

    trim_history()


def trim_history():

    MAX_MESSAGES = 8

    global chat_history

    if len(chat_history) > MAX_MESSAGES:
        chat_history = chat_history[-MAX_MESSAGES:]


if __name__ == "__main__":
    main()
