-- Flattened ATS-N schema (postgres DB): minimal fields requested
-- Order: submission_type first; include only CIK and file_number from filerInfo;
-- exclude flags; from formData include StockATSName (normalized name).

CREATE TABLE IF NOT EXISTS public.ats_n_flat (
    submission_type TEXT,          -- headerData/submissionType
    accession_number TEXT,         -- headerData/accessionNumber
    filing_date DATE,              -- filing_date we inserted in header
    cik TEXT,                      -- headerData/filerInfo/filer/filerCredentials/com:cik
    file_number TEXT,              -- headerData/filerInfo/filer/fileNumber
    stock_ats_name TEXT,           -- formData/cover/txNMSStockATSName (prefixes removed)

    -- keys/lineage
    doc_id TEXT PRIMARY KEY,       -- derived from filename
    source_path TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ats_n_flat_filing_date ON public.ats_n_flat (filing_date);
CREATE INDEX IF NOT EXISTS idx_ats_n_flat_cik ON public.ats_n_flat (cik);
CREATE INDEX IF NOT EXISTS idx_ats_n_flat_name ON public.ats_n_flat (stock_ats_name);

COMMENT ON TABLE public.ats_n_flat IS 'Flattened ATS-N header fields';
COMMENT ON COLUMN public.ats_n_flat.stock_ats_name IS 'Derived from txNMSStockATSName (prefix removed)';


