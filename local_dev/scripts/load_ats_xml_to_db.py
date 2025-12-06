import argparse
import os
import re
import sys
from typing import Optional, Tuple

import psycopg2
import psycopg2.extras
import xml.etree.ElementTree as ET


DOCFILE_REGEX = re.compile(r"^(\d+)_primary_doc\.xml$", re.IGNORECASE)
NS = {
    "ns": "http://www.sec.gov/edgar/atsn",
    "com": "http://www.sec.gov/edgar/common",
    "ats": "http://www.sec.gov/edgar/atsncommon",
}


def parse_fields(xml_text: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Extract a small set of useful fields from the XML, if present.
    Returns: (accession_number, submission_type, filing_date, live_test_flag, cik, file_number, ats_name, bd_operator_name, mpid)
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return (None, None, None, None, None, None, None, None)

    def text_at(xpath: str) -> Optional[str]:
        el = root.find(xpath, NS)
        return el.text.strip() if el is not None and el.text else None

    accession_number = text_at(".//ns:headerData/ns:accessionNumber")
    submission_type = text_at(".//ns:headerData/ns:submissionType")
    live_test_flag = text_at(".//ns:headerData/ns:filerInfo/ns:liveTestFlag")
    cik = text_at(".//ns:headerData/ns:filerInfo/ns:filer/ns:filerCredentials/com:cik")
    file_number = text_at(".//ns:headerData/ns:filerInfo/ns:filer/ns:fileNumber")
    ats_name = text_at(".//ns:formData/ns:cover/ns:txNMSStockATSName")
    bd_operator_name = text_at(".//ns:formData/ns:partOne/ns:txPart1Item2ATSName")
    mpid = text_at(".//ns:formData/ns:partOne/ns:txtPart1Item5cNmsStockMPID")

    # filing_date was injected under the default namespace scope; ElementTree will see it as namespaced.
    # Try namespaced lookup first, then fallback to generic tag search, then regex as last resort.
    filing_date = text_at(".//ns:filing_date")
    if not filing_date:
        # Fallback: scan any element whose localname is filing_date
        for el in root.iter():
            # Handle tags like '{namespace}filing_date'
            if isinstance(el.tag, str) and el.tag.lower().endswith("}filing_date") and el.text:
                filing_date = el.text.strip()
                break
    if not filing_date:
        # Last resort: simple regex search
        m = re.search(r"<filing_date>\s*([0-9]{4}-[0-9]{2}-[0-9]{2})\s*</filing_date>", xml_text)
        if m:
            filing_date = m.group(1)

    return (accession_number, submission_type, filing_date, live_test_flag, cik, file_number, ats_name, bd_operator_name, mpid)


def ensure_columns(conn):
    with conn.cursor() as cur:
        cur.execute("""
            ALTER TABLE public.ats_n_filings
            ADD COLUMN IF NOT EXISTS xml_content xml;
        """)
        cur.execute("""
            ALTER TABLE public.ats_n_filings
            ADD COLUMN IF NOT EXISTS source_path text;
        """)
    conn.commit()


def upsert_row(conn, doc_id: str, xml_text: str, source_path: str):
    (accession_number, submission_type, filing_date, live_test_flag, cik, file_number, ats_name, bd_operator_name, mpid) = parse_fields(xml_text)

    # Normalize LIVE/TEST flag to boolean
    ltf_bool: Optional[bool]
    if live_test_flag is None:
        ltf_bool = None
    else:
        val = live_test_flag.strip().upper()
        if val == "LIVE":
            ltf_bool = True
        elif val == "TEST":
            ltf_bool = False
        else:
            ltf_bool = None

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO public.ats_n_filings
                (doc_id, accession_number, submission_type, filing_date, live_test_flag, cik, file_number, ats_name, bd_operator_name, mpid, xml_content, source_path)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::xml, %s)
            ON CONFLICT (doc_id) DO UPDATE SET
                accession_number = EXCLUDED.accession_number,
                submission_type  = EXCLUDED.submission_type,
                filing_date      = EXCLUDED.filing_date,
                live_test_flag   = EXCLUDED.live_test_flag,
                cik              = EXCLUDED.cik,
                file_number      = EXCLUDED.file_number,
                ats_name         = EXCLUDED.ats_name,
                bd_operator_name = EXCLUDED.bd_operator_name,
                mpid             = EXCLUDED.mpid,
                xml_content      = EXCLUDED.xml_content,
                source_path      = EXCLUDED.source_path
            ;
            """,
            (
                doc_id,
                accession_number,
                submission_type,
                filing_date,
                ltf_bool,
                cik,
                file_number,
                ats_name,
                bd_operator_name,
                mpid,
                xml_text,
                source_path,
            ),
        )


def main():
    ap = argparse.ArgumentParser(description="Load ATS-N XML files into Postgres (store full XML and parsed fields).")
    ap.add_argument("--xml-dir", required=True, help="Directory containing *_primary_doc.xml files")
    ap.add_argument("--host", default=os.getenv("DB_HOST", "localhost"))
    ap.add_argument("--port", type=int, default=int(os.getenv("DB_PORT", "5432")))
    ap.add_argument("--user", default=os.getenv("DB_USER", "postgres"))
    ap.add_argument("--password", default=os.getenv("DB_PASSWORD"))
    ap.add_argument("--dbname", default=os.getenv("DB_NAME", "stack_equities"))
    args = ap.parse_args()

    conn = psycopg2.connect(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        dbname=args.dbname,
    )
    try:
        ensure_columns(conn)

        files = sorted(f for f in os.listdir(args.xml_dir) if f.lower().endswith("_primary_doc.xml"))
        total = 0
        for fname in files:
            m = DOCFILE_REGEX.match(fname)
            if not m:
                continue
            doc_id = m.group(1)
            fpath = os.path.join(args.xml_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    xml_text = f.read()
                upsert_row(conn, doc_id, xml_text, fpath)
                total += 1
                if total % 10 == 0:
                    sys.stderr.write(f"[info] Loaded {total} files\n")
                    conn.commit()
            except Exception as e:
                sys.stderr.write(f"[warn] Failed to load {fpath}: {e}\n")
                conn.rollback()
        conn.commit()
        sys.stderr.write(f"[done] Loaded {total} XML files into public.ats_n_filings\n")
    finally:
        conn.close()


if __name__ == "__main__":
    main()


