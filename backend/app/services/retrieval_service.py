"""
Retrieval Service for ResearchLens.
Orchestrates the full RAG pipeline: query → embed → retrieve → LLM → citations.
Handles single-paper Q&A, structured analysis, multi-paper comparison, and claim verification.
"""
import time
import logging
from typing import List, Dict, Any, Optional
from app.services.vector_store_service import search_by_text, get_document_chunk_count
from app.services.llm_service import (
    generate_answer,
    generate_analysis,
    generate_metrics_extraction,
    generate_comparison,
    generate_claim_verification,
    generate_podcast_script,
)
from app.services.citation_service import format_citations_from_results, group_citations_by_document
from app.models.schemas import (
    QueryResponse, CitationModel, AnalysisResponse, AnalysisSection,
    CompareResponse, ClaimVerifyResponse,
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Analysis section definitions
# ─────────────────────────────────────────────

ANALYSIS_SECTIONS = [
    {
        "title": "Research Problem",
        "query": "What is the main research problem or motivation addressed in this paper?",
    },
    {
        "title": "Main Research Question",
        "query": "What is the main research question or hypothesis investigated?",
    },
    {
        "title": "Methodology",
        "query": "What methodology, approach, model architecture, or experimental design was used?",
    },
    {
        "title": "Dataset / Participants",
        "query": "What dataset, data sources, or participants were used in the study? What is the sample size?",
    },
    {
        "title": "Key Findings",
        "query": "What are the main findings, results, and conclusions of this research?",
    },
    {
        "title": "Important Numbers & Metrics",
        "query": "What are the key quantitative results, accuracy, precision, recall, F1 scores, statistical significance, improvements, and performance metrics?",
    },
    {
        "title": "Limitations",
        "query": "What are the stated limitations, weaknesses, or threats to validity?",
    },
    {
        "title": "Future Work",
        "query": "What future work, open questions, or next steps do the authors suggest?",
    },
]


def retrieve_evidence(query: str, document_ids: List[str], top_k: int = 10) -> tuple:
    """
    Retrieve relevant evidence chunks from ChromaDB.
    Returns (citations: List[CitationModel], raw_results: dict).
    """
    results = search_by_text(query, document_ids, top_k)
    citations = format_citations_from_results(results)
    return citations, results


def _check_evidence_sufficiency(citations: List[CitationModel], min_chunks: int = 2) -> bool:
    """
    Check if retrieved evidence is sufficient to answer a question.
    Considers both quantity and relevance scores.
    """
    if len(citations) < min_chunks:
        return False
    
    # If we have relevance scores, check that at least some are reasonably relevant
    scored = [c for c in citations if c.relevance_score is not None]
    if scored:
        # ChromaDB distances: lower = more similar. Threshold varies by metric.
        # For cosine distance, values < 1.0 are generally relevant
        relevant = [c for c in scored if c.relevance_score < 1.2]
        return len(relevant) >= min_chunks
    
    return True


def answer_question(query: str, document_ids: List[str]) -> QueryResponse:
    """
    Full RAG pipeline: retrieve evidence → call LLM → format citations.
    """
    start = time.time()
    
    citations, _ = retrieve_evidence(query, document_ids, top_k=10)
    evidence_sufficient = _check_evidence_sufficiency(citations)
    
    # Convert citations to evidence dicts for LLM
    evidence_for_llm = [c.model_dump() for c in citations]
    
    # Generate answer
    llm_result = generate_answer(query, evidence_for_llm)
    
    return QueryResponse(
        answer=llm_result.get("answer", ""),
        citations=citations,
        evidence_sufficient=evidence_sufficient,
        query=query,
        processing_time_ms=round((time.time() - start) * 1000, 2),
    )


import concurrent.futures

def analyze_document(document_id: str, document_name: str = "Document") -> AnalysisResponse:
    start = time.time()
    
    def process_section(section_def):
        citations, _ = retrieve_evidence(section_def["query"], [document_id], top_k=5)
        if citations:
            content = generate_analysis(section_def["title"], [c.model_dump() for c in citations])
        else:
            content = "This information was not clearly identified in the available evidence from the paper."
        return AnalysisSection(title=section_def["title"], content=content, citations=citations)
        
    def process_metrics():
        metrics_citations, _ = retrieve_evidence(
            "key metrics results accuracy precision recall F1 dataset size sample improvements statistics",
            [document_id], top_k=15
        )
        return generate_metrics_extraction([c.model_dump() for c in metrics_citations])

    analysis_sections = []
    key_metrics = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=9) as executor:
        section_futures = {executor.submit(process_section, s): i for i, s in enumerate(ANALYSIS_SECTIONS)}
        metrics_future = executor.submit(process_metrics)
        
        # Collect sections in original order
        results = [None] * len(ANALYSIS_SECTIONS)
        for future in concurrent.futures.as_completed(section_futures):
            results[section_futures[future]] = future.result()
            
        analysis_sections = results
        key_metrics = metrics_future.result()

    return AnalysisResponse(
        document_name=document_name,
        sections=analysis_sections,
        key_metrics=key_metrics,
        processing_time_ms=round((time.time() - start) * 1000, 2),
    )


def compare_papers(document_ids: List[str], question: str) -> CompareResponse:
    """
    Compare multiple research papers by retrieving evidence separately per document.
    Sources are never mixed — each claim is attributed to its specific paper.
    """
    start = time.time()
    
    per_paper_evidence: Dict[str, List[Dict[str, Any]]] = {}
    per_paper_citations: Dict[str, List[CitationModel]] = {}
    
    for doc_id in document_ids:
        citations, _ = retrieve_evidence(question, [doc_id], top_k=5)
        
        # Use document name from first citation, or fall back to ID
        doc_name = citations[0].document_name if citations else doc_id
        
        per_paper_evidence[doc_name] = [c.model_dump() for c in citations]
        per_paper_citations[doc_name] = citations
    
    # Generate comparison
    comparison_result = generate_comparison(question, per_paper_evidence)
    
    return CompareResponse(
        answer=comparison_result.get("answer", ""),
        per_paper_evidence=per_paper_citations,
        comparison_table=comparison_result.get("comparison_table"),
        processing_time_ms=round((time.time() - start) * 1000, 2),
    )


def verify_claim(document_id: str, claim: str, document_name: str = "Document") -> ClaimVerifyResponse:
    """
    Verify whether a specific claim is supported by the research paper.
    Retrieves evidence and classifies as SUPPORTED, PARTIALLY_SUPPORTED, or NOT_CLEARLY_SUPPORTED.
    """
    start = time.time()
    
    # Retrieve evidence related to the claim
    citations, _ = retrieve_evidence(claim, [document_id], top_k=10)
    evidence_for_llm = [c.model_dump() for c in citations]
    
    # Generate verification
    result = generate_claim_verification(claim, evidence_for_llm)
    
    # Separate supporting vs contradicting evidence based on verdict
    verdict = result.get("verdict", "NOT_CLEARLY_SUPPORTED")
    if verdict == "SUPPORTED":
        supporting = citations
        contradicting = []
    elif verdict == "PARTIALLY_SUPPORTED":
        # Split evidence — top half as supporting, rest as context
        mid = max(1, len(citations) // 2)
        supporting = citations[:mid]
        contradicting = citations[mid:]
    else:
        supporting = []
        contradicting = citations
    
    return ClaimVerifyResponse(
        verdict=verdict,
        explanation=result.get("explanation", ""),
        supporting_evidence=supporting,
        contradicting_evidence=contradicting,
        processing_time_ms=round((time.time() - start) * 1000, 2),
    )

def create_podcast(document_id: str, document_name: str = "Document") -> Dict[str, Any]:
    """
    Generate a podcast script from a paper.
    """
    start = time.time()
    
    # Retrieve top 20 most central/important chunks by querying general themes
    citations, _ = retrieve_evidence(
        "main contribution research problem methodology findings dataset key results limitations future work", 
        [document_id], 
        top_k=20
    )
    
    evidence_for_llm = [c.model_dump() for c in citations]
    
    script = generate_podcast_script(document_name, evidence_for_llm)
    
    return {
        "document_name": document_name,
        "script": script,
        "processing_time_ms": round((time.time() - start) * 1000, 2),
    }
