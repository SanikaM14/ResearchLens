from flask import Flask, jsonify, request
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)

# MOCK DATA
MOCK_DOCUMENT = {
    "id": "demo-doc-1",
    "original_name": "Agile_Methodology_Impact_Study_2026.pdf",
    "status": "ready",
    "total_pages": 42,
    "file_size": 1024000,
    "upload_time": "2026-09-05T12:00:00Z"
}

MOCK_CITATION = {
    "document_name": "Agile_Methodology_Impact_Study_2026.pdf",
    "page_number": 12,
    "section": "Methodology",
    "chunk_index": 4,
    "evidence_text": "Our empirical study across 50 enterprise teams revealed that implementing Agile frameworks increased deployment frequency by 47% while reducing critical defects by 22%. The transition required an average of 3 months of intensive training.",
    "relevance_score": 0.95
}

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "mode": "presentation-mock"})

@app.route("/api/documents", methods=["GET"])
def get_documents():
    return jsonify({"documents": [MOCK_DOCUMENT], "total": 1})

@app.route("/api/documents/<doc_id>", methods=["GET"])
def get_document(doc_id):
    return jsonify(MOCK_DOCUMENT)

@app.route("/api/research/query", methods=["POST"])
def mock_query():
    data = request.json or {}
    time.sleep(1)
    return jsonify({
        "answer": "Based on the provided research, Agile methodology significantly impacts team performance. The study demonstrates a 47% increase in deployment frequency and a 22% reduction in critical defects following Agile adoption.",
        "citations": [MOCK_CITATION],
        "evidence_sufficient": True,
        "query": data.get("query", ""),
        "processing_time_ms": 1024.5
    })

@app.route("/api/research/analyze", methods=["POST"])
def mock_analyze():
    time.sleep(1.5)
    return jsonify({
        "document_name": MOCK_DOCUMENT["original_name"],
        "sections": [
            {
                "title": "Research Problem",
                "content": "The paper investigates the quantitative impact of Agile methodologies on enterprise software deployment frequency and defect rates, addressing the lack of large-scale empirical data in previous literature.",
                "citations": [MOCK_CITATION]
            },
            {
                "title": "Methodology",
                "content": "A longitudinal study was conducted over 18 months, tracking 50 enterprise software teams across 3 Fortune 500 companies during their transition from Waterfall to Agile frameworks.",
                "citations": [MOCK_CITATION]
            },
            {
                "title": "Key Findings",
                "content": "Teams experienced a 47% increase in deployment frequency. Critical defects dropped by 22%. However, initial velocity dipped by 15% during the first 3 months of transition.",
                "citations": [MOCK_CITATION]
            }
        ],
        "key_metrics": [
            {"metric": "Deployment Frequency", "value": "+47%", "context": "Increase post-Agile adoption", "page": 12, "section": "Results"},
            {"metric": "Critical Defects", "value": "-22%", "context": "Reduction in severity 1 bugs", "page": 14, "section": "Results"},
            {"metric": "Sample Size", "value": "50", "context": "Enterprise teams tracked", "page": 5, "section": "Methodology"}
        ],
        "processing_time_ms": 1540.2
    })

@app.route("/api/research/compare", methods=["POST"])
def mock_compare():
    time.sleep(1)
    return jsonify({
        "answer": "Both papers agree that Agile improves deployment metrics, but they differ on the impact of defect rates. Paper A shows a 22% reduction in defects, whereas Paper B argues that defect rates remain stable but are caught earlier in the lifecycle.",
        "per_paper_evidence": {
            MOCK_DOCUMENT["original_name"]: [MOCK_CITATION]
        },
        "comparison_table": "| Metric | Paper A (Study) | Paper B (Review) |\n|---|---|---|\n| Deployment Speed | +47% | +35% |\n| Defect Rate | -22% | No change |\n| Team Satisfaction | +18% | +25% |",
        "processing_time_ms": 1100.0
    })

@app.route("/api/research/verify-claim", methods=["POST"])
def mock_verify():
    data = request.json or {}
    claim = data.get("claim", "")
    time.sleep(1)
    return jsonify({
        "verdict": "SUPPORTED",
        "explanation": f"The claim that '{claim}' is strongly supported by the text. The empirical study explicitly states that deployment frequency increased by 47% across the 50 tracked enterprise teams.",
        "supporting_evidence": [MOCK_CITATION],
        "contradicting_evidence": [],
        "processing_time_ms": 950.5
    })

@app.route("/api/research/podcast", methods=["POST"])
def mock_podcast():
    time.sleep(2)
    return jsonify({
        "document_name": MOCK_DOCUMENT["original_name"],
        "script": [
            {"speaker": "Host 1", "text": "Welcome back! Today we are looking at a fascinating 2026 study on Agile Methodology."},
            {"speaker": "Host 2", "text": "That's right. Everyone says Agile makes you faster, but this paper actually tracked 50 enterprise teams to prove it."},
            {"speaker": "Host 1", "text": "And the numbers are huge. They saw a 47% increase in deployment frequency!"},
            {"speaker": "Host 2", "text": "Wow, almost 50 percent? Did quality drop because they were moving so fast?"},
            {"speaker": "Host 1", "text": "Actually, no. Critical defects dropped by 22 percent. However, it wasn't easy. The paper notes that teams struggled for the first 3 months before seeing these benefits."},
            {"speaker": "Host 2", "text": "So it's a long-term investment. Very interesting!"}
        ],
        "processing_time_ms": 2100.0
    })
