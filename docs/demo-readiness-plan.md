# AI Dashboard + RAG Demo Readiness Plan

## Goal

Make `ai-dashboard-rag` a reliable customer-facing AI/RAG full-stack demo. The optimization focuses on a smooth demo path, honest dashboard metrics, safer file handling, and a codebase that can support client-specific extensions.

## Phase 1: Demo Stability

- Store document registry entries as `safe_filename`, `original_filename`, `document_id`, `size`, and `uploaded_at`.
- Return original filenames in the document list while keeping deletion based on safe internal filenames.
- Use Chroma public APIs for ingestion and deletion from the RAG engine.
- Replace hard-coded accuracy and uptime with actual response time and process uptime.
- Configure CORS from environment settings and validate upload deletion paths stay inside the upload directory.

## Phase 2: Engineering Quality

- Add backend tests for health checks, empty chat questions, path boundary validation, registry metadata, and metrics.
- Keep tests runnable without calling external LLM or embedding APIs.
- Add typed frontend API responses and friendlier error messages from backend `detail` fields.

## Phase 3: Demo Packaging

- Update README startup instructions, test commands, and MVP caveats.
- Clarify that production use needs authentication, tenant isolation, malware scanning, and access control.
- Add sample documents and screenshots once a stable visual walkthrough is ready.

## Acceptance Criteria

- Uploaded files display their original filenames.
- Deleted documents remove both local files and registered vector data.
- Dashboard avoids fabricated accuracy and availability metrics.
- CORS defaults to local development origins.
- Backend tests pass in a basic local development environment.
