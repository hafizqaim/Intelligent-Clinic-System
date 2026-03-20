
from langchain_core.documents import Document
from sqlalchemy.dialects.postgresql import UUID

from app.models.document_embeddings import DocumentEmbeddings
from sqlalchemy.ext.asyncio import AsyncSession

def get_embedding_model(model_name: str):
    if model_name == "all-MiniLM-L6-v2":
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name=model_name)
    elif model_name.startswith("text-embedding"):
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model=model_name)
    else:
        raise ValueError(f"Unsupported embedding model: {model_name}")

    
async def store_embeddings(db: AsyncSession, clinic_id: UUID, documents: list[Document]):
    """Generate and store embeddings for a list of documents."""

    embedding_model = get_embedding_model("all-MiniLM-L6-v2")

    # Batch embed all chunks
    texts = [doc.page_content for doc in documents]
    vectors = embedding_model.embed_documents(texts)


    for doc, embedding in zip(documents, vectors):
        entry = DocumentEmbeddings(
            clinic_id=clinic_id,
            source_filename=doc.metadata.get("source", "unknown"),
            chunk_index=doc.metadata.get("chunk_index", 0),
            chunk_text=doc.page_content,
            embedding=embedding,
        )

        db.add(entry)
    await db.commit()