-- ATS-N Filings header/cover schema for local Postgres (stack_equities)
-- Creates a table to store key metadata parsed from ATS-N XML files
-- Safe to run multiple times.

-- Optional: uncomment to drop and recreate
-- DROP TABLE IF EXISTS public.ats_n_filings;

CREATE TABLE IF NOT EXISTS public.ats_n_filings (
    -- Primary identifier derived from the XML filename: {doc_id}_primary_doc.xml
    doc_id TEXT PRIMARY KEY,

    -- Header data
    accession_number TEXT UNIQUE,
    submission_type TEXT,
    filing_date DATE,
    live_test_flag BOOLEAN,

    -- Filer info
    cik TEXT,
    file_number TEXT,

    -- Cover metadata (from formData/cover and Part I)
    ats_name TEXT,                -- txNMSStockATSName
    bd_operator_name TEXT,        -- txPart1Item2ATSName (legal entity name)
    mpid TEXT,                    -- txtPart1Item5cNmsStockMPID

    -- Timestamps
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_ats_n_filings_filing_date ON public.ats_n_filings (filing_date);
CREATE INDEX IF NOT EXISTS idx_ats_n_filings_mpid ON public.ats_n_filings (mpid);
CREATE INDEX IF NOT EXISTS idx_ats_n_filings_ats_name ON public.ats_n_filings (ats_name);

COMMENT ON TABLE public.ats_n_filings IS 'Key header/cover metadata for ATS-N filings, parsed from XML';
COMMENT ON COLUMN public.ats_n_filings.doc_id IS 'Document id from filename prefix (e.g., 000009115425000030)';
COMMENT ON COLUMN public.ats_n_filings.accession_number IS 'EDGAR accession number (e.g., 0000091154-25-000027)';
COMMENT ON COLUMN public.ats_n_filings.submission_type IS 'Submission type (e.g., ATS-N/UA)';
COMMENT ON COLUMN public.ats_n_filings.filing_date IS 'Filing date (yyyy-mm-dd) inserted into XML header';
COMMENT ON COLUMN public.ats_n_filings.live_test_flag IS 'LIVE or TEST flag';
COMMENT ON COLUMN public.ats_n_filings.cik IS 'CIK of filer';
COMMENT ON COLUMN public.ats_n_filings.file_number IS 'SEC file number (e.g., 013-00189)';
COMMENT ON COLUMN public.ats_n_filings.ats_name IS 'ATS display name from cover';
COMMENT ON COLUMN public.ats_n_filings.bd_operator_name IS 'Broker-Dealer operator legal name';
COMMENT ON COLUMN public.ats_n_filings.mpid IS 'MPID reported on cover';


