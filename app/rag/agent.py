from app.rag.retriever import retrive_relevant_chunks

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID

from langchain.prompts import ChatPromptTemplate
from langchain_community.llms import Ollama

class ClinicalRAGAgent:
    def __init__(self, clinic_id: UUID, db: AsyncSession):
        self.db = db
        self.clinic_id = self.clinic_id
        self.LLM = Ollama("llama2-7b-chat", temperature=0.7, max_tokens=2048) 

    async def query(self, question: str, top_k: int) -> dict:
        
        Prompt_Template = ChatPromptTemplate.from_template("""You are a clinical intelligence assistant. Answer the following medical
        question using ONLY the provided context. If the context does not contain
        enough information to answer, say "I don't have enough information in my
        knowledge base to answer this question."

        Do not make up information. Always cite which source document your answer
        comes from.

        Context:
        {context}

        Question: {question}

        Answer:""")

        chunks = await retrive_relevant_chunks(self.db, self.clinic_id, question, top_k=top_k)

        context_parts = []
        for c in chunks:
            context_parts.append(
                f"[Source: {c['source_filename']}, Chunk {c['chunk_index']}, Similarity {c['similarity']:.2f}]\n{c['chunk_text']}"
            )
        context = "\n\n".join(context_parts)


        prompt = Prompt_Template.format(context=context, question=question)
        llm_response = self.LLM.invoke(prompt)
        return {
            "answer": llm_response.content if hasattr(llm_response, "content") else str(llm_response),
            "sources": chunks,
            "query": question
        }

