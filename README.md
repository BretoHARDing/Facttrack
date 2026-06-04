# FACTTRACK

FACTTRACK is a forensic investigation platform that ingests and preserves evidence, structures it into searchable and linked records, detects contradictions and timelines across documents and media, and provides grounded AI-assisted case intelligence while maintaining strong chain-of-custody and access controls.

## Core mission

- Secure evidence vault with immutable, content-addressed storage
- Hash-first forensic ingestion and parsing pipeline
- Case-isolated legal investigation workspace
- Tamper-evident audit and integrity subsystem
- Entity relationship and contradiction analysis
- Timeline reconstruction across evidence sources
- Offline-capable field investigation workflows
- Grounded AI-assisted investigative Q&A (phased)

## Architecture intent

FACTTRACK supports two implementation tracks that target the same product outcome:

1. **Microservice-oriented track** (long-term enterprise decomposition)
2. **Monolithic FastAPI prototype track** (faster runnable delivery)

Both must preserve the same guarantees around integrity, case isolation, and evidentiary defensibility.

## Foundation requirements (Phase 1)

- JWT access + refresh token authentication, MFA (TOTP; optional WebAuthn/FIDO2)
- Case workspaces with strict access isolation
- Hash-first evidence ingestion (SHA-256 on raw bytes before parsing)
- Immutable content-addressed evidence storage
- Parser pipeline for PDF (with OCR fallback), email, spreadsheet, and text evidence
- Searchable derived artifacts while preserving raw originals and derivative hashes
- Append-only tamper-evident audit log with cryptographic hash chaining
- PostgreSQL as primary store with row-level security (RLS)
- Redis for caching, queueing, and session-adjacent infrastructure

## Intelligence expansion (Phase 2)

- Contradiction detection pipeline (NLI + optional ASP verification)
- Audio/video ingestion (transcription, diarization, keyframes, OCR, embeddings)
- Timeline extraction and reconstruction engine
- Offline-first PWA model (IndexedDB + OPFS + CRDT sync)

## Advanced retrieval and graph intelligence (Phase 3)

- Grounded RAG over evidence corpus with citation and post-generation verification
- Multimodal retrieval across text, audio, video, and metadata
- Knowledge graph maturation to RDF/OWL model on Amazon Neptune with provenance links
- Policy hardening with ABAC and media authenticity verification (C2PA)

## Integrity and chain-of-custody expectations

Every upload, view, download, export, annotation, login, and contradiction-review action should be auditable.  
Evidence integrity must be demonstrable from ingestion through retrieval, including support for higher-assurance sealing workflows (for example, Merkle batch sealing) where implemented.
