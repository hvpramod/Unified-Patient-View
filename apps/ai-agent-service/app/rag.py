"""RAG pipeline — retrieve clinical guideline chunks via pgvector similarity search."""
from __future__ import annotations
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from langchain_openai import OpenAIEmbeddings
import structlog

from app.config import settings

log = structlog.get_logger()

engine = create_async_engine(settings.database_url)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

_embeddings = OpenAIEmbeddings(model=settings.embedding_model, api_key=settings.openai_api_key)


async def retrieve_guidelines(query: str, top_k: int | None = None) -> list[dict]:
    """Embed query and return top-k similar clinical guideline chunks."""
    k = top_k or settings.rag_top_k
    try:
        embedding = await _embeddings.aembed_query(query)
        embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("""
                    SELECT id, source_doc, chunk_text, metadata,
                           1 - (embedding::vector <=> :embedding::vector) AS similarity
                    FROM clinical_guideline_chunks
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding::vector <=> :embedding::vector
                    LIMIT :k
                """),
                {"embedding": embedding_str, "k": k},
            )
            rows = result.fetchall()
            return [
                {
                    "chunk_id": str(row[0]),
                    "source_doc": row[1],
                    "chunk_text": row[2],
                    "metadata": row[3] or {},
                    "similarity": float(row[4]),
                }
                for row in rows
                if float(row[4]) >= settings.rag_similarity_threshold
            ]
    except Exception as e:
        log.error("rag_retrieval_error", error=str(e))
        return []


async def ingest_guideline_document(source_doc: str, chunks: list[str], metadata: dict | None = None) -> int:
    """Embed and store guideline chunks. Returns number of chunks stored."""
    stored = 0
    async with AsyncSessionLocal() as session:
        for idx, chunk_text in enumerate(chunks):
            try:
                embedding = await _embeddings.aembed_query(chunk_text)
                embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
                await session.execute(
                    text("""
                        INSERT INTO clinical_guideline_chunks (source_doc, chunk_index, chunk_text, embedding, metadata)
                        VALUES (:source_doc, :chunk_index, :chunk_text, :embedding::vector, :metadata::jsonb)
                        ON CONFLICT DO NOTHING
                    """),
                    {
                        "source_doc": source_doc,
                        "chunk_index": idx,
                        "chunk_text": chunk_text,
                        "embedding": embedding_str,
                        "metadata": json.dumps(metadata or {}),
                    },
                )
                stored += 1
            except Exception as e:
                log.error("guideline_ingest_error", chunk_index=idx, error=str(e))
        await session.commit()
    return stored
