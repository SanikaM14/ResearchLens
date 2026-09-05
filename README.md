# ResearchLens

ResearchLens is an evidence-grounded research intelligence platform designed to eliminate hallucinations in automated literature analysis. Developed by Sanika Mordekar, the system provides rigorous verification of academic claims by anchoring all extracted insights directly to their source materials.

The platform addresses the critical reliability gap in standard large language models when processing academic literature. Instead of generating unverified summaries, ResearchLens mandates that every analytical output, cross-paper comparison, and verified claim is accompanied by precise paragraph-level citations.

## Core Capabilities

* **Rigorous Claim Verification:** Evaluates user-submitted hypotheses against uploaded documents, categorizing them as supported or contradicting based strictly on textual evidence.
* **Traceable Analytical Breakdowns:** Deconstructs complex research papers into structured components including methodology, limitations, and empirical findings, mapped directly to their source pages.
* **Source-Isolated Cross-Comparison:** Contrasts multiple academic papers simultaneously while maintaining strict boundaries between sources to prevent context contamination.
* **Audio Synthesis:** Compiles synthesized findings into conversational audio briefs for accessible review.

## Technical Architecture

The system operates on a decoupled client-server architecture:
* **Backend:** A FastAPI application orchestrating document processing, optical character recognition for scanned inputs, and semantic chunking. It utilizes ChromaDB for vector storage and coordinates inference through highly constrained LLM prompts to enforce citation rules.
* **Frontend:** A React application providing a streamlined interface for document management, claim verification, and data export functionalities.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
