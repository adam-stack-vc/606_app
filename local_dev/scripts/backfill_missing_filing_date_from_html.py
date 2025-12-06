import argparse
import csv
import os
import re
import sys
import time
from typing import Dict, Optional

import psycopg2
import requests

SEC_UA = "Mozilla/5.0 (compatible; 606-app/1.0; +contact@example.com)"
DATE_REGEX = re.compile(r"\b(20\d{2})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b")
DOC_ID_REGEX = re.compile(r"([0-9]{14,})primary_doc\.xml$", re.IGNORECASE)
DOC_DIR_REGEX = re.compile(r"/([0-9]{14,})/", re.IGNORECASE)


def http_get(url: str, retries: int = 3, timeout: int = 20) -> Optional[str]:
    headers = {"User-Agent": SEC_UA}
    last_exc: Optional[Exception] = None
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            if r.status_code == 200 and r.text:
                return r.text
            last_exc = Exception(f"HTTP {r.status_code}")
        except Exception as e:
            last_exc = e
        time.sleep(1.5 * (attempt + 1))
    sys.stderr.write(f"[warn] Failed to fetch {url}: {last_exc}\n")
    return None


def extract_filing_date_from_html(html: str) -> Optional[str]:
    if not html:
        return None
    normalized = re.sub(r"\s+", " ", html)
    # Try to narrow to FILING DIV region
    block = normalized
    mblock = re.search(r"<!--\s*START\s+FILING\s+DIV\s*-->(.*?)(?:<!--|$)", normalized, re.IGNORECASE)
    if mblock:
        block = mblock.group(1)
    # Label 'Filing Date' then next info
    label = re.search(r'class\s*=\s*["\']infoHead["\'][^>]*>\s*Filing\s*Date\s*<', block, re.IGNORECASE)
    if label:
        tail = block[label.end():]
        info = re.search(r'class\s*=\s*["\']info["\'][^>]*>(.*?)<', tail, re.IGNORECASE)
        if info:
            candidate = info.group(1).strip()
            md = DATE_REGEX.search(candidate)
            if md:
                return md.group(0)
        nearby = DATE_REGEX.search(tail[:500])
        if nearby:
            return nearby.group(0)
    generic = re.search(r"Filing\s*Date(.{0,500})", block, re.IGNORECASE)
    if generic:
        md = DATE_REGEX.search(generic.group(1))
        if md:
            return md.group(0)
    anyd = DATE_REGEX.search(block)
    if anyd:
        return anyd.group(0)
    return None


def load_docid_to_primary_html(csv_path: str) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            primary_xml = (row.get("primary_xml") or "").strip()
            primary_html = (row.get("primary_html") or "").strip()
            if not primary_xml or not primary_html:
                continue
            m = DOC_ID_REGEX.search(primary_xml)
            if m:
                doc_id = m.group(1)
            else:
                m2 = DOC_DIR_REGEX.search(primary_xml)
                if not m2:
                    continue
                doc_id = m2.group(1)
            mapping[doc_id] = primary_html
    return mapping


def main():
    ap = argparse.ArgumentParser(description="Backfill missing filing_date by fetching Filing Date from primary_html pages.")
    ap.add_argument("--csv", required=True, help="ats_n_links CSV (can use .bak) with primary_html and primary_xml")
    ap.add_argument("--host", default=os.getenv("DB_HOST", "localhost"))
    ap.add_argument("--port", type=int, default=int(os.getenv("DB_PORT", "5432")))
    ap.add_argument("--user", default=os.getenv("DB_USER", "postgres"))
    ap.add_argument("--password", default=os.getenv("DB_PASSWORD"))
    ap.add_argument("--dbname", default=os.getenv("DB_NAME", "stack_equities"))
    args = ap.parse_args()

    doc_to_html = load_docid_to_primary_html(args.csv)
    if not doc_to_html:
        print("[warn] No doc->html mapping from CSV", file=sys.stderr)
        return

    conn = psycopg2.connect(
        host=args.host, port=args.port, user=args.user, password=args.password, dbname=args.dbname
    )
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT doc_id FROM public.ats_n_filings WHERE filing_date IS NULL;")
            rows = [r[0] for r in cur.fetchall()]
            updated = 0
            for doc_id in rows:
                html_url = doc_to_html.get(doc_id)
                if not html_url:
                    continue
                html = http_get(html_url)
                fdate = extract_filing_date_from_html(html) if html else None
                if not fdate:
                    continue
                cur.execute("UPDATE public.ats_n_filings SET filing_date = %s::date WHERE doc_id = %s;", (fdate, doc_id))
                updated += 1
        conn.commit()
        print(f"[done] Backfilled {updated} rows via HTML")
    finally:
        conn.close()


if __name__ == "__main__":
    main()


