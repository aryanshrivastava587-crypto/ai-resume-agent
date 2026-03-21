import logging
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

logger = logging.getLogger(__name__)

# Load embedding model once at startup (singleton pattern)
_model = None

def _get_model():
    """Lazy-load the SentenceTransformer model (loaded once, reused forever)."""
    global _model
    if _model is None:
        logger.info("Loading SentenceTransformer model...")
        _model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("SentenceTransformer model loaded successfully.")
    return _model


def split_text(text, max_chunks=20):
    """Split text into meaningful chunks with better sentence-aware logic."""
    if not text or not text.strip():
        return ["No content available."]

    # Split by double newlines first (paragraph-level), then single newlines
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    # If too few paragraphs, fallback to line-level splitting
    if len(paragraphs) < 3:
        paragraphs = [line.strip() for line in text.split("\n") if line.strip()]

    # Merge very short chunks together for better context
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
    """Create embeddings for the given text chunks."""
    model = _get_model()
    chunks = split_text(text)
    embeddings = model.encode(chunks, show_progress_bar=False)
    return chunks, np.array(embeddings)


def build_index(embeddings):
    """Build a FAISS index for fast similarity search."""
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    return index


def retrieve(query, chunks, index, k=5):
    """Retrieve the top-k most relevant chunks for a given query."""
    model = _get_model()
    k = min(k, len(chunks))  # Prevent k > number of chunks
    query_embedding = model.encode([query])
    D, I = index.search(np.array(query_embedding), k)
    return [chunks[i] for i in I[0] if i < len(chunks)]