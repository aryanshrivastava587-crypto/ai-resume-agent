import logging
import faiss
import numpy as np
import google.generativeai as genai

logger = logging.getLogger(__name__)

def split_text(text, max_chunks=20):
    """Split text into meaningful chunks with better sentence-aware logic."""
    if not text or not text.strip():
        return ["No content available."]

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    if len(paragraphs) < 3:
        paragraphs = [line.strip() for line in text.split("\n") if line.strip()]

    merged = []
    buffer = ""
    for p in paragraphs:
        if len(buffer) + len(p) < 300:
            buffer = f"{buffer} {p}".strip()
        else:
            if buffer:
                merged.append(buffer)
            buffer = p
    if buffer:
        merged.append(buffer)

    return merged[:max_chunks] if merged else ["No content available."]


def create_embeddings(text):
    """Create embeddings via Gemini API (zero local memory usage)."""
    chunks = split_text(text)
    
    # Use Gemini's embedding API instead of heavy local PyTorch models
    # This prevents Out-Of-Memory (OOM) 502 Server Errors on Render's 512MB free tier
    try:
        response = genai.embed_content(
            model="models/text-embedding-004",
            content=chunks,
            task_type="retrieval_document"
        )
        embeddings = np.array(response['embedding']).astype('float32')
        return chunks, embeddings
    except Exception as e:
        logger.error(f"Failed to generate embeddings via Gemini: {e}")
        # Fallback to zeros if quota exhausted so graceful error handles it 
        return chunks, np.zeros((len(chunks), 768), dtype="float32")


def build_index(embeddings):
    """Build a FAISS index for fast similarity search."""
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    return index


def retrieve(query, chunks, index, k=5):
    """Retrieve the top-k most relevant chunks for a given query."""
    k = min(k, len(chunks))
    
    try:
        query_response = genai.embed_content(
            model="models/text-embedding-004",
            content=query,
            task_type="retrieval_query"
        )
        query_embedding = np.array([query_response['embedding']]).astype('float32')
        D, I = index.search(query_embedding, k)
        return [chunks[i] for i in I[0] if i < len(chunks)]
    except Exception as e:
        logger.error(f"Failed to search index: {e}")
        # Fallback to returning all chunks up to k
        return chunks[:k]