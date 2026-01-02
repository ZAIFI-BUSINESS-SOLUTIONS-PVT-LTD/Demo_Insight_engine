"""
Phase 0: Response Ingestion & Normalization

Responsibilities:
- Accept raw client-uploaded response files (Excel).
- Identify response type via configuration (ONLINE or OFFLINE).
- Convert various client formats into ONE canonical ResponseSheet.csv.
- Validate schema strictly (Fail loudly if ambiguity or mismatch).
- Output exactly ONE ResponseSheet.csv per test for Phase 1 consumption.

This phase isolates the messy reality of client inputs from the strict Phase 1 pipeline.
"""
