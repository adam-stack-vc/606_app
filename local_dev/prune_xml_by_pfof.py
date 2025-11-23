#!/usr/bin/env python3
"""
Scan XML files in a folder and delete files where the sum of elements
matching <netPmtPaidRev...Usd> is less than a threshold (default: 10000.00).
"""

import os
import re
import sys
import glob
import argparse
import xml.etree.ElementTree as ET
from typing import Tuple

# Support both 'Recv' (Receive/Received) and 'Rev' variants observed in tags
TAG_REGEX = re.compile(r"^netPmtPaidRe(?:cv|v).*Usd$", re.IGNORECASE)


def local_tag(tag: str) -> str:
    """Strip XML namespace, if present: {ns}Tag -> Tag."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def sum_target_fields(xml_path: str) -> Tuple[float, int]:
    """Return (sum_usd, count) for matching <netPmtPaidRev...Usd> elements."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except Exception as e:
        print(f"❌ Failed to parse {os.path.basename(xml_path)}: {e}")
        return 0.0, 0

    total = 0.0
    count = 0
    for elem in root.iter():
        name = local_tag(elem.tag)
        if TAG_REGEX.match(name):
            text = (elem.text or "").strip()
            if text:
                try:
                    # Allow integer or float text
                    val = float(text)
                    total += val
                    count += 1
                except ValueError:
                    # Non-numeric, ignore
                    pass
    return total, count


def main():
    parser = argparse.ArgumentParser(
        description="Delete XML files where sum of <netPmtPaidRev...Usd> is below a threshold."
    )
    parser.add_argument(
        "--dir",
        default="Q3_2025",
        help="Directory to scan (default: Q3_2025)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=1000.0,
        help="Deletion threshold for sum (default: 1000.0)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not delete; only print what would be deleted",
    )
    args = parser.parse_args()

    folder = os.path.abspath(args.dir)
    if not os.path.isdir(folder):
        print(f"❌ Directory not found: {folder}")
        sys.exit(1)

    xml_files = glob.glob(os.path.join(folder, "*.xml"))
    if not xml_files:
        print(f"⚠️  No XML files found in {folder}")
        sys.exit(0)

    print(f"Scanning {len(xml_files)} XML files in: {folder}")
    print(f"Threshold: {args.threshold:.2f} (sum of <netPmtPaidRev...Usd>)")

    to_delete = []
    for path in xml_files:
        total, count = sum_target_fields(path)
        fname = os.path.basename(path)
        print(f"- {fname}: sum={total:.2f} (matches={count})")
        if total < args.threshold:
            to_delete.append((path, total, count))

    print("\nSummary:")
    print(f"  Below threshold: {len(to_delete)} file(s)")
    if to_delete:
        for path, total, count in to_delete[:10]:
            print(f"    • {os.path.basename(path)} -> sum={total:.2f} matches={count}")
        if len(to_delete) > 10:
            print(f"    … and {len(to_delete) - 10} more")

    if args.dry_run:
        print("\nDry run: no files deleted.")
        return

    # Delete
    deleted = 0
    for path, total, _ in to_delete:
        try:
            os.remove(path)
            print(f"🗑️  Deleted {os.path.basename(path)} (sum={total:.2f})")
            deleted += 1
        except Exception as e:
            print(f"❌ Failed to delete {os.path.basename(path)}: {e}")

    print(f"\nDone. Deleted {deleted} file(s).")


if __name__ == "__main__":
    main()


