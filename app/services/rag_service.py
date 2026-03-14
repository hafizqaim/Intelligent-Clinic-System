from sqlalchemy.ext.asyncio import AsyncSession
from sqlaclchemy.dialects.postgresql import UUID

from app.rag.retriever import retrive_relevant_chunks
from app.rag.chunker import chunk_documents
from app.rag.loader import load_documents
from app.rag.embeddings import store_embeddings
from app.rag.agent import ClinicalRAGAgent

from app.models.chat_histories import ChatHistories

def ingest_documents(db: AsyncSession, clinic_id: UUID, directory: str) -> dict:
    documents = load_documents(directory)
    chunks = chunk_documents(documents)
    store_embeddings(chunks)

async def ask_question(db: AsyncSession, user_id: UUID, question: str) -> dict:
    agent = ClinicalRAGAgent(db, user_id)
    response = agent.query(question)

    # Store the question and answer in the chat history
    chat_history = ChatHistories(
        clinic_id=agent.clinic_id,
        user_id=user_id,
        message=response
    )
    db.add(chat_history)
    await db.commit()

    return {"answer": response}

async def get_chat_history(db: AsyncSession, user_id: UUID, limit: int = 50) -> list[dict]:
    result = await db.execute(
        ChatHistories.select().where(ChatHistories.user_id == user_id).order_by(ChatHistories.id.desc()).limit(limit)
    )
    chat_histories = result.scalars().all()
    return [{"message": chat.message} for chat in chat_histories]