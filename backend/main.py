from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import PromptTemplate
#from vector import retriever
from pdf_to_vector import retriever
from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter


# LLMChain does not work with RetrievalQA, 
# so we will use a Runnable that takes the output of the retriever, 
# formats it, and then passes it to the prompt and model
model = OllamaLLM(model="qwen3.5:2b")

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
"""
prompt = PromptTemplate.from_template(template)

#chain = prompt | model. # this is LLMChain, but it doesn't work with RetrievalQA, so we will use RetrievalQA instead

chain = {"context": itemgetter("question")| retriever | format_docs, "question": RunnablePassthrough()} | prompt | model 
# this is a Runnable that takes the output of the retriever, formats it, and then passes it to the prompt and model

# test the chain with some questions about the document
"""

query = "What are the key steps in emergency medical care?"
result = chain.invoke({"question": query})
print("------------")
print(query)
print(result)


query = "what is this document mainly about?"
result = chain.invoke({"question": query})
print("------------")
print(query)
print(result)

query = "who is the first author of this document?"
result = chain.invoke({"question": query})
print("------------")
print(query)
print(result)

query = "what is the publication date of this document?"
result = chain.invoke({"question": query})
print("------------")
print(query)
print(result)     

query = "what are the key findings of this document?"
result = chain.invoke({"question": query})
print("------------")
print(query)
print(result)


query = "the email address of the corresponding author of this document?"
result = chain.invoke({"question": query})
print("------------")
print(query)
print(result)

query = "who is the first author of this document?"
result = chain.invoke({"question": query})
print("------------")
print(query)
print(result)
"""
query = "what is autism?"
result = chain.invoke({"question": query})
print("------------")
print(query)
print(result)

query = "what is the difference between autism and asperger's syndrome?"
result = chain.invoke({"question": query})
print("------------")
print(query)
print(result)

query = "what is " \
"asperger's syndrome?"
result = chain.invoke({"question": query})
print("------------")
print(query)
print(result)