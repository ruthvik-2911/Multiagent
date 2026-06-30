"""
supervisor.py — Fast, direct RAG pipeline.

Instead of asking an LLM planner to route to multiple agents (slow, unreliable),
we use a simple two-step approach:

  1. SEARCH: Hybrid search (semantic + keyword) across ALL Qdrant chunks.
  2. ANSWER: Send the retrieved context + question to the LLM.

This eliminates the planner Ollama call and multiple agent overhead,
cutting response time roughly in half.
"""

from backend.agents import document_agent, graph_agent, analytics_agent, memory_agent, email_agent
from backend.agents.registry import get_agent
from backend.services.activity_service import log_activity
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"


def run(question: str, context: dict):
    from backend.utils.dependencies import EMBEDDING_MODEL, QDRANT_CLIENT, COLLECTION_NAME
    from backend.services.profile_embedding_service import find_best_profile
    from backend.services.document_profile_service import get_profile
    from qdrant_client.http import models

    print(f"\n[AI Supervisor] Question: {question}")

    # ── STEP 1: Hybrid search ──────────────────────────────────────────
    # A) Semantic search across ALL chunks using the raw question
    question_embedding = EMBEDDING_MODEL.encode(question).tolist()
    semantic_results = QDRANT_CLIENT.query_points(
        collection_name=COLLECTION_NAME,
        query=question_embedding,
        limit=15,
    )

    # B) Try to identify the best-matching document by profile
    best_doc, profile_score = find_best_profile(question)
    print(f"[AI Supervisor] Profile match: {best_doc} (score: {profile_score:.3f})")

    # C) If we have a good profile match, also pull chunks from that specific document
    doc_chunks = []
    if best_doc and profile_score >= 0.40:
        doc_results = QDRANT_CLIENT.query_points(
            collection_name=COLLECTION_NAME,
            query=question_embedding,
            limit=10,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="file_name",
                        match=models.MatchValue(value=best_doc)
                    )
                ]
            )
        )
        doc_chunks = doc_results.points

    # D) Keyword search: also find chunks containing exact keywords from the question
    #    This catches structured text (workflow nodes) that semantic search misses.
    question_words = [w for w in question.lower().split() if len(w) > 2]
    keyword_results = QDRANT_CLIENT.scroll(
        collection_name=COLLECTION_NAME,
        limit=100,
        with_payload=True,
        with_vectors=False,
    )[0]

    keyword_chunks = []
    for point in keyword_results:
        content_lower = point.payload.get("content", "").lower()
        # Check if any significant question words appear in the chunk
        matches = sum(1 for w in question_words if w in content_lower)
        if matches >= 2:  # At least 2 keyword matches
            keyword_chunks.append((point, matches))

    # Sort keyword matches by number of matching words (most relevant first)
    keyword_chunks.sort(key=lambda x: x[1], reverse=True)
    keyword_chunks = [p for p, _ in keyword_chunks[:10]]

    # ── STEP 2: Merge & deduplicate results ────────────────────────────
    seen_ids = set()
    merged_contexts = []
    merged_sources = []

    def add_chunk(point, source_label=""):
        pid = point.id if hasattr(point, 'id') else id(point)
        if pid in seen_ids:
            return
        seen_ids.add(pid)
        payload = point.payload
        content = payload.get("content", "")
        file_name = payload.get("file_name", "Unknown")
        if content.strip():
            merged_contexts.append(f"--- From Document: {file_name} ---\n{content}")
            merged_sources.append({
                "file_name": file_name,
                "chunk_number": payload.get("chunk_number", "?")
            })

    # Priority 1: Document-specific chunks (if profile matched well)
    for p in doc_chunks:
        add_chunk(p, "doc")

    # Priority 2: Keyword-matched chunks (exact text matches)
    for p in keyword_chunks:
        add_chunk(p, "keyword")

    # Priority 3: Semantic search results (score > 0.15)
    for p in semantic_results.points:
        if p.score >= 0.15:
            add_chunk(p, "semantic")

    # Limit context to avoid overwhelming the LLM
    merged_contexts = merged_contexts[:10]

    total_context = "\n\n".join(merged_contexts) if merged_contexts else "No relevant documents found."

    print(f"[AI Supervisor] Found {len(merged_contexts)} context chunks")
    log_activity("Supervisor Search", f"{len(merged_contexts)} chunks found")

    # ── STEP 3: Generate answer ────────────────────────────────────────
    prompt = f"""You are an Enterprise AI Assistant. Answer using ONLY the context below.

Context from indexed documents:

{total_context}

Question: {question}

Instructions:
- Answer ONLY using the context above. Do NOT invent information.
- If the context has workflow NODES and CONNECTIONS, trace the path to answer.
  Example: if asked "what happens if X is No?", find node "X" in CONNECTIONS and follow the "No" arrow.
- If asked "which documents", list the file names from "From Document:" tags.
- If the answer is not in the context, say: "I could not find this information in the indexed documents."
- Be concise and professional.
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"num_ctx": 4096}
            }
        )
        answer = response.json().get("response", "")
    except Exception as e:
        answer = f"Error contacting Ollama: {str(e)}"

    # Build response metadata
    profile = get_profile(best_doc) if best_doc else None

    return {
        "question": question,
        "answer": answer,
        "selected_document": best_doc if profile_score >= 0.40 else None,
        "confidence": round(profile_score, 3) if best_doc else 0.0,
        "summary": profile["summary"] if profile else "",
        "keywords": profile["keywords"] if profile else [],
        "sources": merged_sources
    }
