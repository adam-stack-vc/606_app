#!/usr/bin/env python3
"""
Script to download XML files from URLs in a CSV file
"""

import csv
import requests
import zipfile
import os
import glob
from urllib.parse import urlparse, urljoin, urlunparse
import time
from pathlib import Path
import re
from bs4 import BeautifulSoup

# -----------------------------
# SEC-friendly request helpers
# -----------------------------

def _request_kwargs(url: str):
    """
    Build requests kwargs (headers, timeouts) suitable for SEC and general hosts.
    Uses hard-coded contact details per requirements.
    """
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    headers = {
        # Descriptive UA with organization and contact
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/17.0 Safari/605.1.15 "
            "(Stack Asset Mgmt; contact: research@stack.vc)"
        ),
        "Accept": "application/xml, text/xml, text/html;q=0.9, */*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }
    if "sec.gov" in host:
        headers.setdefault("Referer", "https://www.sec.gov/")
    return {"headers": headers, "timeout": 60}

def _normalize_url(url: str) -> str:
    """
    Some SEC 'primary_doc.xml' URLs are missing a slash before the filename:
      .../000123456789primary_doc.xml  →  .../000123456789/primary_doc.xml
    Normalize such cases to reduce 404s.
    """
    try:
        parsed = urlparse(url)
        host = (parsed.netloc or "").lower()
        path = parsed.path or ""
        if "sec.gov" in host and path.endswith("primary_doc.xml") and not path.endswith("/primary_doc.xml"):
            idx = path.rfind("primary_doc.xml")
            path = path[:idx] + "/" + path[idx:]
            return urlunparse(parsed._replace(path=path))
    except Exception:
        pass
    return url

def get_files_from_directory(url):
    """Get list of files from a directory URL"""
    try:
        print(f"  📁 Detected directory, scanning for files...")
        response = requests.get(url, **_request_kwargs(url))
        response.raise_for_status()
        
        file_urls = []
        
        # Parse the HTML content to find links
        lines = response.text.split('\n')
        for line in lines:
            # Look for href patterns in the HTML
            matches = re.findall(r'href="([^"]+)"', line)
            for href in matches:
                if href and not href.startswith('?') and not href.startswith('#') and href != '..':
                    # Make it a full URL
                    full_url = urljoin(url, href)
                    
                    # Only include files (not parent directories)
                    if not href.endswith('/'):
                        file_urls.append(full_url)
        
        print(f"    Found {len(file_urls)} files in directory")
        return file_urls
        
    except Exception as e:
        print(f"    ❌ Error scanning directory {url}: {e}")
        return []

def download_file(url, destination_folder):
    """Download a file from URL to destination folder"""
    try:
        # Normalize known SEC URL quirk
        url = _normalize_url(url)
        # Get filename from URL
        filename = os.path.basename(urlparse(url).path)
        if not filename or filename.endswith('/'):
            # If it's a directory or no filename, create a timestamped name
            filename = f"download_{int(time.time())}.zip"
        
        filepath = os.path.join(destination_folder, filename)
        
        print(f"  Downloading: {filename}")
        
        # Download with progress
        response = requests.get(url, stream=True, **_request_kwargs(url))
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('content-type', '').lower()
        print(f"    Content-Type: {content_type}")
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"    Progress: {percent:.1f}%", end='\r')
        
        print(f"    ✓ Downloaded: {filename}")
        return filepath, content_type
        
    except Exception as e:
        print(f"    ❌ Error downloading {url}: {e}")
        return None, None

def process_downloaded_file(file_path, destination_folder, content_type):
    """Process downloaded file - extract XML from zip or copy if it's already XML"""
    try:
        filename = os.path.basename(file_path)
        xml_files_extracted = []
        
        # Check if it's already an XML file
        if filename.lower().endswith('.xml'):
            print(f"    ✓ File is already XML: {filename}")
            xml_files_extracted.append(file_path)
            return xml_files_extracted
        
        # Check if it's a zip file
        if filename.lower().endswith('.zip') or 'zip' in content_type:
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    # List all files in zip
                    file_list = zip_ref.namelist()
                    
                    # Find XML files
                    xml_files = [f for f in file_list if f.lower().endswith('.xml')]
                    
                    if not xml_files:
                        print(f"    ⚠️  No XML files found in {filename}")
                        os.remove(file_path)  # Delete the zip
                        return []
                    
                    print(f"    Found {len(xml_files)} XML files:")
                    
                    # Extract only XML files
                    for xml_file in xml_files:
                        # Get just the filename (remove path)
                        xml_filename = os.path.basename(xml_file)
                        xml_dest_path = os.path.join(destination_folder, xml_filename)
                        
                        # Extract the file
                        with zip_ref.open(xml_file) as source, open(xml_dest_path, 'wb') as target:
                            target.write(source.read())
                        
                        xml_files_extracted.append(xml_dest_path)
                        print(f"      ✓ Extracted: {xml_filename}")
                
                # Delete the zip file
                os.remove(file_path)
                print(f"    🗑️  Deleted: {filename}")
                
            except zipfile.BadZipFile:
                print(f"    ⚠️  File is not a valid zip: {filename}")
                # Check if it might be an XML file with wrong extension
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read(100)  # Read first 100 chars
                        if content.strip().startswith('<?xml'):
                            # It's an XML file with wrong extension
                            new_name = filename.replace('.zip', '.xml')
                            new_path = os.path.join(destination_folder, new_name)
                            os.rename(file_path, new_path)
                            xml_files_extracted.append(new_path)
                            print(f"      ✓ Renamed to XML: {new_name}")
                        else:
                            print(f"    ❌ Unknown file type: {filename}")
                            os.remove(file_path)
                except:
                    print(f"    ❌ Unknown file type: {filename}")
                    os.remove(file_path)
        else:
            print(f"    ⚠️  Unknown file type: {filename} (Content-Type: {content_type})")
            os.remove(file_path)
        
        return xml_files_extracted
        
    except Exception as e:
        print(f"    ❌ Error processing {file_path}: {e}")
        return []

def process_csv_urls(csv_file, destination_folder="test_batch"):
    """Process URLs from CSV file and download XML files"""
    
    # Create destination folder if it doesn't exist
    os.makedirs(destination_folder, exist_ok=True)
    
    print(f"Processing URLs from: {csv_file}")
    print(f"Destination folder: {destination_folder}")
    print("=" * 60)
    
    # Statistics
    total_urls = 0
    successful_downloads = 0
    failed_downloads = 0
    total_xml_files = 0
    
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            
            # Find the URL column (try common names)
            url_column = None
            if reader.fieldnames:
                for col in reader.fieldnames:
                    if 'url' in col.lower() or 'link' in col.lower() or 'file' in col.lower():
                        url_column = col
                        break
            
            if not url_column:
                print("❌ Could not find URL column in CSV. Available columns:")
                if reader.fieldnames:
                    for col in reader.fieldnames:
                        print(f"  - {col}")
                return
            
            print(f"Using URL column: {url_column}")
            print()
            
            # Process each row
            for i, row in enumerate(reader, 1):
                url = row.get(url_column, '').strip()
                
                if not url:
                    print(f"[{i}] ⚠️  Empty URL, skipping")
                    continue
                
                print(f"[{i}] Processing: {url}")
                
                # Check if this is a directory (ends with /)
                if url.endswith('/'):
                    # Get all files from directory
                    file_urls = get_files_from_directory(url)
                    
                    if not file_urls:
                        print(f"    ⚠️  No files found in directory")
                        failed_downloads += 1
                        total_urls += 1
                        continue
                    
                    # Download each file from the directory
                    for j, file_url in enumerate(file_urls, 1):
                        print(f"    [{j}/{len(file_urls)}] Downloading: {os.path.basename(urlparse(file_url).path)}")
                        
                        download_result = download_file(file_url, destination_folder)
                        
                        if download_result[0]:  # file_path
                            file_path, content_type = download_result
                            # Process the downloaded file
                            xml_files = process_downloaded_file(file_path, destination_folder, content_type)
                            
                            if xml_files:
                                total_xml_files += len(xml_files)
                        
                        # Small delay between files
                        time.sleep(0.5)
                    
                    successful_downloads += 1
                else:
                    # Single file download
                    download_result = download_file(url, destination_folder)
                    
                    if download_result[0]:  # file_path
                        file_path, content_type = download_result
                        # Process the downloaded file
                        xml_files = process_downloaded_file(file_path, destination_folder, content_type)
                        
                        if xml_files:
                            successful_downloads += 1
                            total_xml_files += len(xml_files)
                        else:
                            failed_downloads += 1
                    else:
                        failed_downloads += 1
                
                total_urls += 1
                
                # Small delay to be nice to servers
                time.sleep(1)
    
    except FileNotFoundError:
        print(f"❌ CSV file not found: {csv_file}")
        return
    except Exception as e:
        print(f"❌ Error processing CSV: {e}")
        return
    
    # Final summary
    print("\n" + "=" * 60)
    print("DOWNLOAD SUMMARY")
    print("=" * 60)
    print(f"Total URLs processed: {total_urls}")
    print(f"Successful downloads: {successful_downloads}")
    print(f"Failed downloads: {failed_downloads}")
    print(f"Total XML files extracted: {total_xml_files}")
    
    # List all XML files in destination
    xml_files_in_dest = glob.glob(os.path.join(destination_folder, "*.xml"))
    print(f"XML files in {destination_folder}: {len(xml_files_in_dest)}")
    
    if xml_files_in_dest:
        print("\nXML files ready for processing:")
        for xml_file in xml_files_in_dest:
            print(f"  - {os.path.basename(xml_file)}")

def main():
    """Main function"""
    print("XML File Downloader")
    print("=" * 60)
    
    # Look for CSV files in current directory
    csv_files = glob.glob("*.csv")
    
    if not csv_files:
        print("❌ No CSV files found in current directory")
        print("Please place your CSV file with URLs in this directory")
        return
    
    if len(csv_files) == 1:
        csv_file = csv_files[0]
        print(f"Found CSV file: {csv_file}")
    else:
        print("Multiple CSV files found:")
        for i, file in enumerate(csv_files, 1):
            print(f"  {i}. {file}")
        
        try:
            choice = int(input("\nSelect CSV file (number): ")) - 1
            if 0 <= choice < len(csv_files):
                csv_file = csv_files[choice]
            else:
                print("Invalid selection")
                return
        except ValueError:
            print("Invalid input")
            return
    
    # Ask for destination folder
    destination = input("Destination folder (default: test_batch): ").strip()
    if not destination:
        destination = "test_batch"
    
    # Confirm before starting
    print(f"\nAbout to download files to: {destination}")
    response = input("Proceed? (y/N): ")
    if response.lower() != 'y':
        print("Download cancelled.")
        return
    
    # Start downloading
    process_csv_urls(csv_file, destination)

if __name__ == "__main__":
    main() 