"""
LangGraph Research Workflow for ResearchLens.
Implements a stateful agentic workflow for complex multi-step research queries.

Graph Flow:
    START → analyze_query → [route by type]
                              ├─ retrieve_single (1 paper)
                              └─ retrieve_multi (multiple papers)
                                    │
                              check_evidence
                              ├─ sufficient → synthesize
                              └─ insufficient → retrieve_more → synthesize
                                                    │
                                              attach_sources → END
"""
import time
import logging
from typing import TypedDict, List, Dict, Any, Optional, Literal
from langgraph.graph import StateGraph, START, END
from app.services.vector_store_service import search_by_text
from app.services.citation_service import format_citations_from_results
from app.services.llm_service import generate_answer

logger = logging.getLogger(__name__)

# Maximum retry cycles for evidence retrieval
MAX_RETRIEVAL_RETRIES = 2


class ResearchState(TypedDict):
    """State schema passed between graph nodes."""
    query: str
    query_type: str  # single_paper | multi_paper | comparison
    document_ids: List[str]
    retrieved_evidence: List[Dict[str, Any]]
    evidence_sufficient: bool
    retrieval_attempts: int
    answer: str
    citations: List[Dict[str, Any]]
    error: Optional[str]
    start_time: float


# ─────────────────────────────────────────────
# Node Functions
# ─────────────────────────────────────────────

def analyze_query(state: ResearchState) -> dict:
    """Classify the query type based on document count and keywords."""
    doc_count = len(state["document_ids"])
    query_lower = state["query"].lower()
    
    # Detect comparison intent
    comparison_keywords = ["compare", "comparison", "difference", "versus", "vs", "contrast", "between"]
    is_comparison = any(kw in query_lower for kw in comparison_keywords)
    
    if doc_count > 1 and is_comparison:
        query_type = "comparison"
    elif doc_count > 1:
        query_type = "multi_paper"
    else:
        query_type = "single_paper"
    
    logger.info(f"Query classified as: {query_type} (docs: {doc_count})")
    return {"query_type": query_type}


def retrieve_single(state: ResearchState) -> dict:
    """Retrieve evidence from a single document."""
    top_k = 10 + (state.get("retrieval_attempts", 0) * 5)
    results = search_by_text(state["query"], state["document_ids"], top_k=top_k)
    citations = format_citations_from_results(results)
    evidence = [c.model_dump() for c in citations]
    
    logger.info(f"Single-paper retrieval: {len(evidence)} chunks (top_k={top_k})")
    return {
        "retrieved_evidence": evidence,
        "retrieval_attempts": state.get("retrieval_attempts", 0) + 1,
    }


def retrieve_multi(state: ResearchState) -> dict:
    """Retrieve evidence from multiple documents separately."""
    all_evidence = []
    top_k = 5 + (state.get("retrieval_attempts", 0) * 3)
    
    for doc_id in state["document_ids"]:
        results = search_by_text(state["query"], [doc_id], top_k=top_k)
        citations = format_citations_from_results(results)
        all_evidence.extend([c.model_dump() for c in citations])
    
    logger.info(f"Multi-paper retrieval: {len(all_evidence)} total chunks from {len(state['document_ids'])} papers")
    return {
        "retrieved_evidence": all_evidence,
        "retrieval_attempts": state.get("retrieval_attempts", 0) + 1,
    }


def check_evidence(state: ResearchState) -> dict:
    """
    Evaluate whether retrieved evidence is sufficient to answer the question.
    Considers quantity and relevance scores.
    """
    evidence = state.get("retrieved_evidence", [])
    
    if len(evidence) < 2:
        sufficient = False
    else:
        # Check relevance scores — lower distance = more relevant
        scored = [e for e in evidence if e.get("relevance_score") is not None]
        if scored:
            relevant = [e for e in scored if e["relevance_score"] < 1.2]
            sufficient = len(relevant) >= 2
        else:
            sufficient = len(evidence) >= 2
    
    logger.info(f"Evidence check: {len(evidence)} chunks, sufficient={sufficient}")
    return {"evidence_sufficient": sufficient}


def retrieve_more(state: ResearchState) -> dict:
    """Broaden search when evidence is insufficient."""
    logger.info(f"Broadening search (attempt {state.get('retrieval_attempts', 1)})")
    
    # Use a broader query variant
    broader_queries = [
        state["query"],
        f"key findings results conclusions {state['query']}",
        f"methodology approach {state['query']}",
    ]
    
    all_evidence = list(state.get("retrieved_evidence", []))
    existing_chunks = {e.get("chunk_index") for e in all_evidence}
    
    for bq in broader_queries[1:]:  # Skip original query (already searched)
        for doc_id in state["document_ids"]:
            results = search_by_text(bq, [doc_id], top_k=5)
            citations = format_citations_from_results(results)
            for c in citations:
                cd = c.model_dump()
                if cd.get("chunk_index") not in existing_chunks:
                    all_evidence.append(cd)
                    existing_chunks.add(cd.get("chunk_index"))
    
    return {
        "retrieved_evidence": all_evidence,
        "retrieval_attempts": state.get("retrieval_attempts", 0) + 1,
    }


def synthesize(state: ResearchState) -> dict:
    """Generate grounded answer from retrieved evidence using LLM."""
    evidence = state.get("retrieved_evidence", [])
    
    if not evidence:
        return {
            "answer": "I could not find sufficient evidence in the uploaded papers to answer this question.",
        }
    
    result = generate_answer(state["query"], evidence)
    
    return {"answer": result.get("answer", "")}


def attach_sources(state: ResearchState) -> dict:
    """Format citations from evidence metadata for the final response."""
    # Citations are already in evidence from retrieval — just pass through
    return {"citations": state.get("retrieved_evidence", [])}


# ─────────────────────────────────────────────
# Routing Functions
# ─────────────────────────────────────────────

def route_after_analyze(state: ResearchState) -> str:
    """Route to single or multi-paper retrieval."""
    if state["query_type"] == "single_paper":
        return "retrieve_single"
    return "retrieve_multi"


def route_after_check(state: ResearchState) -> str:
    """Route based on evidence sufficiency and retry budget."""
    if state.get("evidence_sufficient", False):
        return "synthesize"
    if state.get("retrieval_attempts", 0) < MAX_RETRIEVAL_RETRIES:
        return "retrieve_more"
    # Exceeded retry budget — synthesize with whatever we have
    logger.warning("Evidence insufficient after max retries, synthesizing anyway.")
    return "synthesize"


# ─────────────────────────────────────────────
# Graph Construction
# ─────────────────────────────────────────────

workflow = StateGraph(ResearchState)

# Add nodes
workflow.add_node("analyze_query", analyze_query)
workflow.add_node("retrieve_single", retrieve_single)
workflow.add_node("retrieve_multi", retrieve_multi)
workflow.add_node("check_evidence", check_evidence)
workflow.add_node("retrieve_more", retrieve_more)
workflow.add_node("synthesize", synthesize)
workflow.add_node("attach_sources", attach_sources)

# Add edges
workflow.add_edge(START, "analyze_query")
workflow.add_conditional_edges("analyze_query", route_after_analyze, {
    "retrieve_single": "retrieve_single",
    "retrieve_multi": "retrieve_multi",
})
workflow.add_edge("retrieve_single", "check_evidence")
workflow.add_edge("retrieve_multi", "check_evidence")
workflow.add_conditional_edges("check_evidence", route_after_check, {
    "synthesize": "synthesize",
    "retrieve_more": "retrieve_more",
})
workflow.add_edge("retrieve_more", "check_evidence")
workflow.add_edge("synthesize", "attach_sources")
workflow.add_edge("attach_sources", END)

# Compile
research_graph = workflow.compile()


def run_research_workflow(query: str, document_ids: List[str]) -> Dict[str, Any]:
    """
    Execute the LangGraph research workflow for complex multi-step queries.
    Returns dict with answer, citations, and processing time.
    """
    start_time = time.time()
    
    initial_state: ResearchState = {
        "query": query,
        "query_type": "",
        "document_ids": document_ids,
        "retrieved_evidence": [],
        "evidence_sufficient": False,
        "retrieval_attempts": 0,
        "answer": "",
        "citations": [],
        "error": None,
        "start_time": start_time,
    }
    
    try:
        result = research_graph.invoke(initial_state)
        processing_time_ms = round((time.time() - start_time) * 1000, 2)
        
        return {
            "answer": result.get("answer", ""),
            "citations": result.get("citations", []),
            "processing_time_ms": processing_time_ms,
        }
    except Exception as e:
        logger.error(f"Research workflow failed: {e}")
        return {
            "answer": "The research workflow encountered an error. Please try again.",
            "citations": [],
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }
