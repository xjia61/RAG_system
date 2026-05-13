from operator import itemgetter

from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough

from pdf_to_vector import retriever
from chat_store import format_chat_history_for_prompt


#model = OllamaLLM(model="qwen3:1.7b")
model = OllamaLLM(model="qwen3.5:2b")
# Use the exact model name from: ollama list


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


template = """
You are a helpful assistant answering questions using the provided context.

Answer ONLY using the context below.

If the answer is not present in the context, say:
"I cannot find this information in the provided document."

Do not say "I am checking".
Do not pretend to search.
Do not repeat yourself.

Context:
{context}

Question:
{question}

Answer:
"""

prompt = PromptTemplate.from_template(template)
"""
chain = (
    {
        "context": itemgetter("question") | retriever | format_docs,
        "question": itemgetter("question"),
    }
    | prompt
    | model
)


def ask_rag(question: str) -> str:
    result = chain.invoke({"question": question})
    return result
"""

def ask_rag(question: str, session_id: str | None = None) -> str:
    docs = retriever.invoke(question)
    context = format_docs(docs)

    chat_history = format_chat_history_for_prompt(
        session_id=session_id,
        limit=10,
    )

    final_prompt = prompt.invoke(
        {
            "chat_history": chat_history,
            "context": context,
            "question": question,
        }
    )

    result = model.invoke(final_prompt)
    return result