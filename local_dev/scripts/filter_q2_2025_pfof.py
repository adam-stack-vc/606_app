import os
import csv
import xml.etree.ElementTree as ET
from typing import Optional, Tuple


INPUT_DIR = "/Users/adamsussman/Documents/606_app/local_dev/Q2_2025/Q2_2025"
OUTPUT_CSV = "/Users/adamsussman/Documents/606_app/local_dev/Q2_2025/Q2_2025_pfof_over_1000.csv"


def parse_float(text: Optional[str]) -> Optional[float]:
    if text is None:
        return None
    s = text.strip()
    if s == "":
        return None
    # Remove any non-numeric chars except dot and minus
    cleaned = "".join(ch for ch in s if ch.isdigit() or ch in ".-")
    if cleaned in ("", ".", "-"):
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def extract_bd_qtr_year(root: ET.Element) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    bd = root.findtext("./bd")
    qtr = root.findtext("./qtr")
    year = root.findtext("./year")
    return (bd.strip() if bd else None,
            qtr.strip() if qtr else None,
            year.strip() if year else None)


def compute_sum_usd(root: ET.Element) -> Tuple[Optional[float], bool]:
    """
    Sum of columns Z, AD, AH mapped to XML as:
      - netPmtPaidRecvMarketOrdersUsd
      - netPmtPaidRecvMarketableLimitOrdersUsd
      - netPmtPaidRecvNonMarketableLimitOrdersUsd
    Aggregated across all rVenues in all sections.

    Returns:
      (total_sum_or_none, had_any_value)
    """
    tags = [
        "netPmtPaidRecvMarketOrdersUsd",
        "netPmtPaidRecvMarketableLimitOrdersUsd",
        "netPmtPaidRecvNonMarketableLimitOrdersUsd",
    ]
    total = 0.0
    had_any = False
    for rvenue in root.findall(".//rVenues/rVenue"):
        for tag in tags:
            val = parse_float(rvenue.findtext(f"./{tag}"))
            if val is not None:
                had_any = True
                total += val
    if not had_any:
        return (None, False)
    return (total, True)


def process_file(path: str) -> Optional[Tuple[str, str, str, float, str]]:
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except ET.ParseError:
        return None
    bd, qtr, year = extract_bd_qtr_year(root)
    total_sum, had_any = compute_sum_usd(root)
    if not had_any or total_sum is None:
        return None
    if total_sum < 1000.0:
        return None
    return (bd or "", qtr or "", year or "", float(total_sum), os.path.basename(path))


def main():
    rows = []
    for name in sorted(os.listdir(INPUT_DIR)):
        if not name.lower().endswith(".xml"):
            continue
        full_path = os.path.join(INPUT_DIR, name)
        result = process_file(full_path)
        if result:
            rows.append(result)

    # Write CSV output
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["bd", "qtr", "year", "sum_usd_Z+AD+AH", "filename"])
        for row in rows:
            writer.writerow(row)

    print(f"Wrote {len(rows)} rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()






