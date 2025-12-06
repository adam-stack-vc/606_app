import argparse
import csv
import os
import re
import sys
from typing import Dict

import psycopg2

DOC_ID_REGEX = re.compile(r"([0-9]{14,})primary_doc\.xml$", re.IGNORECASE)


def load_docid_to_date(csv_path: str) -> Dict[str, str]:
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(csv_path)
    mapping: Dict[str, str] = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            primary_xml = (row.get("primary_xml") or "").strip()
            filing_date = (row.get("filing_date") or "").strip()
            if not primary_xml or not filing_date:
                continue
            m = DOC_ID_REGEX.search(primary_xml)
            if not m:
                continue
            doc_id = m.group(1)
            mapping[doc_id] = filing_date
    return mapping


def main():
    ap = argparse.ArgumentParser(description="Backfill ats_n_filings.filing_date from ats_n_links.csv for missing rows.")
    ap.add_argument("--csv", required=True, help="Path to ats_n_links.csv with filing_date column")
    ap.add_argument("--host", default=os.getenv("DB_HOST", "localhost"))
    ap.add_argument("--port", type=int, default=int(os.getenv("DB_PORT", "5432")))
    ap.add_argument("--user", default=os.getenv("DB_USER", "postgres"))
    ap.add_argument("--password", default=os.getenv("DB_PASSWORD"))
    ap.add_argument("--dbname", default=os.getenv("DB_NAME", "stack_equities"))
    args = ap.parse_args()

    mapping = load_docid_to_date(args.csv)
    if not mapping:
        print("[warn] No mapping loaded from CSV", file=sys.stderr)
        return

    conn = psycopg2.connect(
        host=args.host, port=args.port, user=args.user, password=args.password, dbname=args.dbname
    )
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT doc_id FROM public.ats_n_filings WHERE filing_date IS NULL;")
            rows = cur.fetchall()
            updated = 0
            for (doc_id,) in rows:
                date_str = mapping.get(doc_id)
                if not date_str:
                    continue
                cur.execute(
                    "UPDATE public.ats_n_filings SET filing_date = %s::date WHERE doc_id = %s;",
                    (date_str, doc_id),
                )
                updated += 1
        conn.commit()
        print(f"[done] Backfilled {updated} rows from CSV")
    finally:
        conn.close()


if __name__ == "__main__":
    main()





