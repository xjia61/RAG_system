from pathlib import Path
from datetime import datetime
import hashlib

from bs4 import BeautifulSoup
from ebooklib import epub, ITEM_DOCUMENT

from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_DIR = BASE_DIR / "chroma_db"

CHROMA_DIR.mkdir(exist_ok=True)

embeddings = OllamaEmbeddings(model="mxbai-embed-large")

db = Chroma(
    collection_name="my_collection",
    embedding_function=embeddings,
    persist_directory=str(CHROMA_DIR),
)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)


def get_file_hash(file_path: Path) -> str:
    hash_obj = hashlib.sha256()

    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            hash_obj.update(chunk)

    return hash_obj.hexdigest()


def load_epub_simple(path: Path):
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
                    metadata={
                        "source": str(path),
                        "type": "epub",
                    },
                )
            )

    return docs


def load_uploaded_file(file_path: Path):
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return PyPDFLoader(str(file_path)).load()

    if suffix == ".txt":
        return TextLoader(str(file_path), encoding="utf-8").load()

    if suffix == ".epub":
        return load_epub_simple(file_path)

    raise ValueError(f"Unsupported file type: {suffix}")


def add_document_to_vectorstore(file_path: Path, original_filename: str):
    """
    Add one uploaded document into the existing Chroma DB.
    It does NOT clear old documents.
    It does NOT rebuild the whole vector database.
    """

    file_hash = get_file_hash(file_path)

    docs = load_uploaded_file(file_path)
    chunks = text_splitter.split_documents(docs)

    chunk_ids = []
    final_chunks = []

    for i, chunk in enumerate(chunks):
        chunk_id = f"{file_hash}_{i}"

        chunk.metadata.update(
            {
                "source": original_filename,
                "file_hash": file_hash,
                "chunk_index": i,
                "uploaded_at": datetime.now().isoformat(),
            }
        )

        chunk_ids.append(chunk_id)
        final_chunks.append(chunk)

    existing = db.get(ids=chunk_ids)
    existing_ids = set(existing.get("ids", []))

    new_chunks = []
    new_ids = []

    for chunk_id, chunk in zip(chunk_ids, final_chunks):
        if chunk_id not in existing_ids:
            new_ids.append(chunk_id)
            new_chunks.append(chunk)

    if new_chunks:
        db.add_documents(new_chunks, ids=new_ids)

        if hasattr(db, "persist"):
            db.persist()

    return {
        "filename": original_filename,
        "file_hash": file_hash,
        "total_chunks": len(final_chunks),
        "new_chunks_added": len(new_chunks),
        "duplicate_chunks_skipped": len(final_chunks) - len(new_chunks),
    }


def retrieve_context(question: str, k: int = 5):
    docs = db.similarity_search(question, k=k)

    context_items = []

    for doc in docs:
        context_items.append(
            {
                "text": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "chunk_index": doc.metadata.get("chunk_index"),
                "file_hash": doc.metadata.get("file_hash"),
            }
        )

    return docs, context_items
