import argparse
import csv
import os
import re
import sys
from typing import Dict, Optional, Tuple


CSV_REQUIRED_COLUMNS = {"primary_xml", "filing_date"}
DOC_ID_REGEX = re.compile(r"([0-9]{14,})primary_doc\.xml$", re.IGNORECASE)


def load_docid_to_date(csv_path: str) -> Dict[str, str]:
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    mapping: Dict[str, str] = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = set(reader.fieldnames or [])
        missing = CSV_REQUIRED_COLUMNS - cols
        if missing:
            raise ValueError(f"CSV missing required columns: {', '.join(sorted(missing))}")
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


def compute_local_xml_path(ats_xml_dir: str, doc_id: str) -> str:
    return os.path.join(ats_xml_dir, f"{doc_id}_primary_doc.xml")


def insert_or_update_filing_date(xml_text: str, filing_date: str) -> Tuple[str, bool]:
    """
    Insert <filing_date>yyyy-mm-dd</filing_date> immediately after <accessionNumber>... line.
    If the tag exists already, update its value in place.
    Preserve the indentation used on the <accessionNumber> line.
    """
    # If already present, update in place
    existing_tag = re.search(r"(<\s*filing_date\s*>)(.*?)(<\s*/\s*filing_date\s*>)", xml_text, flags=re.IGNORECASE | re.DOTALL)
    if existing_tag:
        start, end = existing_tag.span(2)
        new_text = xml_text[:start] + filing_date + xml_text[end:]
        return new_text, True

    lines = xml_text.splitlines(keepends=True)
    for idx, line in enumerate(lines):
        if "<accessionNumber" in line:
            # Derive indentation from this line's leading whitespace
            leading_ws = ""
            for ch in line:
                if ch in (" ", "\t"):
                    leading_ws += ch
                else:
                    break
            # Compose new line with the same indentation level
            newline = f"{leading_ws}<filing_date>{filing_date}</filing_date>\n"
            insert_at = idx + 1
            lines.insert(insert_at, newline)
            return "".join(lines), True
    return xml_text, False


def process_all(ats_xml_dir: str, csv_path: str, dry_run: bool = False) -> None:
    docid_to_date = load_docid_to_date(csv_path)
    if not docid_to_date:
        print("[warn] No doc ids with filing_date found in CSV; nothing to do.", file=sys.stderr)
        return

    total = 0
    updated = 0
    skipped_missing = 0
    skipped_no_anchor = 0

    for doc_id, filing_date in docid_to_date.items():
        total += 1
        xml_path = compute_local_xml_path(ats_xml_dir, doc_id)
        if not os.path.exists(xml_path):
            skipped_missing += 1
            continue
        with open(xml_path, "r", encoding="utf-8") as f:
            original = f.read()
        new_text, changed = insert_or_update_filing_date(original, filing_date)
        if not changed:
            skipped_no_anchor += 1
            continue
        if not dry_run:
            with open(xml_path, "w", encoding="utf-8") as f:
                f.write(new_text)
        updated += 1

    print(f"[done] Considered: {total}, Updated: {updated}, Missing files: {skipped_missing}, No anchor found: {skipped_no_anchor}")


def main():
    parser = argparse.ArgumentParser(description="Insert <filing_date> after <accessionNumber> in local ATS XML files.")
    parser.add_argument("--ats-xml-dir", required=True, help="Directory containing *_primary_doc.xml files")
    parser.add_argument("--csv", required=True, help="CSV with primary_xml and filing_date columns")
    parser.add_argument("--dry-run", action="store_true", help="Do not write changes, only report")
    args = parser.parse_args()

    process_all(args.ats_xml_dir, args.csv, dry_run=args.dry_run)


if __name__ == "__main__":
    main()





