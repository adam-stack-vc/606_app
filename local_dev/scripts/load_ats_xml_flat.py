import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET

import psycopg2

NS = {
    "ns": "http://www.sec.gov/edgar/atsn",
    "com": "http://www.sec.gov/edgar/common",
}
DOCFILE_REGEX = re.compile(r"^(\d+)_primary_doc\.xml$", re.IGNORECASE)


def text_at(root: ET.Element, xpath: str):
    el = root.find(xpath, NS)
    return el.text.strip() if el is not None and el.text else None


def parse_flat_fields(xml_text: str):
    root = ET.fromstring(xml_text)

    submission_type = text_at(root, ".//ns:headerData/ns:submissionType")
    accession_number = text_at(root, ".//ns:headerData/ns:accessionNumber")
    cik = text_at(root, ".//ns:headerData/ns:filerInfo/ns:filer/ns:filerCredentials/com:cik")
    file_number = text_at(root, ".//ns:headerData/ns:filerInfo/ns:filer/ns:fileNumber")

    # filing_date may be namespaced; try both ways
    filing_date = text_at(root, ".//ns:filing_date")
    if not filing_date:
        for el in root.iter():
            if isinstance(el.tag, str) and el.tag.lower().endswith("}filing_date") and el.text:
                filing_date = el.text.strip()
                break
    if not filing_date:
        # last resort regex
        m = re.search(r"<filing_date>\s*([0-9]{4}-[0-9]{2}-[0-9]{2})\s*</filing_date>", xml_text)
        if m:
            filing_date = m.group(1)

    # formData cover ATS name
    stock_ats_name = text_at(root, ".//ns:formData/ns:cover/ns:txNMSStockATSName")

    return submission_type, accession_number, filing_date, cik, file_number, stock_ats_name


def upsert_flat_row(conn, doc_id: str, source_path: str, fields):
    submission_type, accession_number, filing_date, cik, file_number, stock_ats_name = fields
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO public.ats_n_flat
                (submission_type, accession_number, filing_date, cik, file_number, stock_ats_name, doc_id, source_path)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (doc_id) DO UPDATE SET
                submission_type  = EXCLUDED.submission_type,
                accession_number = EXCLUDED.accession_number,
                filing_date      = EXCLUDED.filing_date,
                cik              = EXCLUDED.cik,
                file_number      = EXCLUDED.file_number,
                stock_ats_name   = EXCLUDED.stock_ats_name,
                source_path      = EXCLUDED.source_path
            ;
            """,
            (
                submission_type,
                accession_number,
                filing_date,
                cik,
                file_number,
                stock_ats_name,
                doc_id,
                source_path,
            ),
        )


def main():
    ap = argparse.ArgumentParser(description="Load flattened ATS-N fields into postgres: public.ats_n_flat")
    ap.add_argument("--xml-dir", required=True)
    ap.add_argument("--host", default=os.getenv("PGHOST", "localhost"))
    ap.add_argument("--port", type=int, default=int(os.getenv("PGPORT", "5432")))
    ap.add_argument("--user", default=os.getenv("PGUSER", "postgres"))
    ap.add_argument("--password", default=os.getenv("PGPASSWORD"))
    ap.add_argument("--dbname", default=os.getenv("PGDATABASE", "postgres"))
    args = ap.parse_args()

    conn = psycopg2.connect(
        host=args.host, port=args.port, user=args.user, password=args.password, dbname=args.dbname
    )
    try:
        files = sorted(f for f in os.listdir(args.xml_dir) if f.lower().endswith("_primary_doc.xml"))
        total = 0
        for fname in files:
            m = DOCFILE_REGEX.match(fname)
            if not m:
                continue
            doc_id = m.group(1)
            path = os.path.join(args.xml_dir, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    xml_text = f.read()
                fields = parse_flat_fields(xml_text)
                upsert_flat_row(conn, doc_id, path, fields)
                total += 1
                if total % 10 == 0:
                    conn.commit()
                    sys.stderr.write(f"[info] Loaded {total}\n")
            except Exception as e:
                conn.rollback()
                sys.stderr.write(f"[warn] {fname}: {e}\n")
        conn.commit()
        sys.stderr.write(f"[done] Loaded {total} rows into public.ats_n_flat\n")
    finally:
        conn.close()


if __name__ == "__main__":
    main()





