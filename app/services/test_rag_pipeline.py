import asyncio
import uuid

from app.rag.loader import load_documents
from app.rag.chunker import chunk_documents
from app.rag.embeddings import store_embeddings
from app.rag.agent import ClinicalRAGAgent

# Replace with your actual DB session factory
from app.database import async_session_factory


async def run_pipeline():
    # 1. Load and chunk documents
    docs = load_documents("./data/medical_docs/")
    print(f"Loaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"Chunked into {len(chunks)} pieces")

    # 2. Generate and store embeddings
    clinic_id = uuid.uuid4()  # test clinic ID
    async with async_session_factory() as db:  # AsyncSession
        await store_embeddings(db, clinic_id, chunks)

        # 3. Initialize RAG agent
        agent = ClinicalRAGAgent(db, clinic_id, llm_provider="ollama")  # or "ollama"

        # 4. Ask test questions
        questions = [
            "What are the symptoms of hypertension?",
            "What is the mechanism of action of aspirin?",
            "What causes low oxygen saturation?",
        ]

        for q in questions:
            response = await agent.query(q)
            print("\n---")
            print(f"Question: {response['query']}")
            print(f"Answer: {response['answer']}")
            print("Sources:")
            for s in response["sources"]:
                print(f"  - {s['source_filename']} (chunk {s['chunk_index']}, sim={s['similarity']:.2f})")


if __name__ == "__main__":
    asyncio.run(run_pipeline())