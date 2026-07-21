-- Idempotent migration: allow materials created from GAMMA requests to exist
-- before SAP assigns their code. The SAP code is filled in later (reconciliation);
-- until then it stays NULL ("pending") and the material still participates in
-- duplicate detection via short_text similarity.
ALTER TABLE silver.materials ALTER COLUMN code DROP NOT NULL;

-- Track the request each material originated from, so export is idempotent
-- (re-exporting the same request updates instead of duplicating) and the SAP
-- code can be reconciled back onto the right row later.
ALTER TABLE silver.materials
    ADD COLUMN IF NOT EXISTS source_request_id BIGINT REFERENCES silver.requests(id);

-- One material per source request. Partial so legacy/imported materials (no
-- source request) are unaffected and can share the NULL value.
CREATE UNIQUE INDEX IF NOT EXISTS uq_materials_source_request
    ON silver.materials (source_request_id)
    WHERE source_request_id IS NOT NULL;
