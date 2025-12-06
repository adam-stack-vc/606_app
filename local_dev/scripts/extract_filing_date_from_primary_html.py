import argparse
import csv
import os
import re
import sys
import time
from typing import Optional

import requests


SEC_UA = "Mozilla/5.0 (compatible; 606-app/1.0; +contact@yourdomain.example)"
DATE_REGEX = re.compile(r"\b(20\d{2})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b")


def http_get_with_retries(url: str, max_retries: int = 3, timeout: int = 20) -> Optional[str]:
    headers = {"User-Agent": SEC_UA, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
    last_exc: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 200 and resp.text:
                return resp.text
            last_exc = Exception(f"HTTP {resp.status_code}")
        except Exception as exc:
            last_exc = exc
        time.sleep(1.5 * (attempt + 1))
    sys.stderr.write(f"[warn] Failed to fetch {url}: {last_exc}\n")
    return None


def extract_filing_date_from_html(html: str) -> Optional[str]:
    """
    Strategy:
    1) Narrow to <!-- START FILING DIV --> block if present
    2) Find an element with class="infoHead" that contains 'Filing Date'
    3) Then find the next occurrence of class="info" and return the first yyyy-mm-dd found
    4) Fallback: search within ~500 chars after 'Filing Date' label
    """
    if not html:
        return None

    # Normalize spacing to simplify regex matching
    normalized = re.sub(r"\s+", " ", html)

    # Try to isolate the filing section for precision
    filing_section_match = re.search(r"<!--\s*START\s+FILING\s+DIV\s*-->(.*?)(?:<!--|$)", normalized, re.IGNORECASE)
    search_space = filing_section_match.group(1) if filing_section_match else normalized

    # Locate "Filing Date" label
    label_match = re.search(r'class\s*=\s*["\']infoHead["\'][^>]*>\s*Filing\s*Date\s*<', search_space, re.IGNORECASE)
    if label_match:
        tail = search_space[label_match.end():]
        # Find next info block
        info_match = re.search(r'class\s*=\s*["\']info["\'][^>]*>(.*?)<', tail, re.IGNORECASE)
        if info_match:
            candidate = info_match.group(1).strip()
            date_match = DATE_REGEX.search(candidate)
            if date_match:
                return date_match.group(0)
        # Fallback: scan next 500 chars for a date
        date_nearby = DATE_REGEX.search(tail[:500])
        if date_nearby:
            return date_nearby.group(0)

    # Broader fallback: any "Filing Date" mention followed by a date soon after
    generic = re.search(r"Filing\s*Date(.{0,500})", search_space, re.IGNORECASE)
    if generic:
        date_any = DATE_REGEX.search(generic.group(1))
        if date_any:
            return date_any.group(0)

    # Last resort: any date in the filing section
    any_date = DATE_REGEX.search(search_space)
    if any_date:
        return any_date.group(0)

    return None


def process_csv(input_csv: str, output_csv: Optional[str] = None, in_place: bool = True) -> None:
    if not os.path.isfile(input_csv):
        raise FileNotFoundError(f"CSV not found: {input_csv}")

    output_csv = input_csv if in_place else (output_csv or f"{os.path.splitext(input_csv)[0]}_with_filing_date.csv")
    backup_path = None
    if in_place:
        backup_path = f"{input_csv}.bak"
        if not os.path.exists(backup_path):
            os.replace(input_csv, backup_path)
        else:
            # Ensure we don't overwrite an existing backup; create a timestamped one
            ts_backup = f"{input_csv}.{int(time.time())}.bak"
            os.replace(input_csv, ts_backup)
            backup_path = ts_backup

    # Read from backup if in-place, else from input
    read_path = backup_path if in_place else input_csv

    with open(read_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        if "primary_html" not in fieldnames:
            raise ValueError("CSV must contain a 'primary_html' column.")
        if "filing_date" not in fieldnames:
            fieldnames.append("filing_date")
        rows = list(reader)

    total = len(rows)
    done = 0

    for row in rows:
        url = (row.get("primary_html") or "").strip()
        if not url:
            row["filing_date"] = ""
            done += 1
            continue

        # Skip if already populated
        if row.get("filing_date"):
            done += 1
            continue

        html = http_get_with_retries(url)
        date_val = extract_filing_date_from_html(html) if html else None
        row["filing_date"] = date_val or ""

        done += 1
        if done % 10 == 0:
            sys.stderr.write(f"[info] Processed {done}/{total}\n")

        # Be polite to SEC servers
        time.sleep(0.25)

    with open(output_csv, "w", newline="", encoding="utf-8") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    if in_place:
        sys.stderr.write(f"[done] Updated CSV in place: {output_csv}\n")
        sys.stderr.write(f"[backup] Original saved to: {backup_path}\n")
    else:
        sys.stderr.write(f"[done] Wrote: {output_csv}\n")


def main():
    parser = argparse.ArgumentParser(description="Extract Filing Date from primary_html pages and append to CSV.")
    parser.add_argument("--input", required=True, help="Path to input CSV (must contain primary_html)")
    parser.add_argument("--output", help="Output CSV path (ignored if --in-place)")
    parser.add_argument("--no-in-place", action="store_true", help="Write to a new file instead of in-place update")
    args = parser.parse_args()

    in_place = not args.no_in_place
    process_csv(args.input, args.output, in_place=in_place)


if __name__ == "__main__":
    main()





