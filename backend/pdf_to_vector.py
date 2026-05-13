from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document # Import Document class
import os # Import os module to set environment variable
import pandas as pd
from pathlib import Path

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from bs4 import BeautifulSoup
from ebooklib import epub, ITEM_DOCUMENT


#load PDF files
pdf_path= ".\books"
base_dir = Path(__file__).resolve().parent.parent



book_dir = base_dir / "books"
documents = []

def load_epub_simple(path):
    book = epub.read_epub(str(path))
    docs = []

    for item in book.get_items_of_type(ITEM_DOCUMENT):
        html = item.get_content()
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n")

        text = "\n".join(line.strip() for line in text.splitlines() if line.strip())

        if text:
            docs.append(
                Document(
                    page_content=text,
                    metadata={"source": str(path), "type": "epub"}
                )
            )

    return docs

for path in book_dir.rglob("*"):
    suffix = path.suffix.lower()

    try:
        if suffix == ".pdf":
            documents.extend(PyPDFLoader(str(path)).load())

        elif suffix == ".epub":
            documents.extend(load_epub_simple(path))

    except Exception as e:
        print(f"Failed to load {path}: {e}")

print(f"Loaded {len(documents)} docs")
"""
loader = PyPDFLoader(pdf_path)
docs = loader.load()
print(f"Loaded {len(docs)} PDF pages") 
"""

#split text into chunks
from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunked_docs = text_splitter.split_documents(documents)
print(f"Split into {len(chunked_docs)} chunks")


# create Ollama embeddings


embeddings = OllamaEmbeddings(model="mxbai-embed-large")

# create Chroma database


#db_dir = "./chroma_db"
db_dir = base_dir / "chroma_db"
add_docs = not os.path.exists(db_dir) or len(os.listdir(db_dir)) == 0


db = Chroma(collection_name="my_collection", embedding_function=embeddings, persist_directory=db_dir)

# Add documents to Chroma database if it's empty
if add_docs:
    print(f"Adding PDF chunks to Chroma database...")
    db.add_documents(documents=chunked_docs)
    print(f"Added {len(chunked_docs)} chunks to Chroma database.")
else:
    print(f"Chroma database already has documents. Skipping add.")


#create retriever
retriever = db.as_retriever(
    search_kwargs={"k": 5}
)

"""

#test retrieval
query = "What are the key steps in emergency medical care?"
results = retriever.invoke(query)


query = "what is this document mainly about?"
results = retriever.invoke(query)
for i, r in enumerate(results):
    print("------------")
    print(f"\nResult {i+1}:\n{r.page_content[:500]}...")    

    """
