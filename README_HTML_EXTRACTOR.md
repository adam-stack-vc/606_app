# HTML Content Extractor with CSV Processing

A comprehensive Python script that uses Selenium, Readability, and Goose3 to extract content from web pages, with support for batch processing from CSV files.

## Features

- **Selenium WebDriver**: Downloads HTML from any URL with proper error handling
- **Readability Integration**: Cleans HTML to extract main content
- **Goose3 Content Extraction**: Extracts title, metadata, and body text
- **CSV Batch Processing**: Process multiple URLs from CSV files
- **Metadata Integration**: Includes CSV metadata (URL, title, date, sentiment) in output
- **Text File Output**: Saves structured content to `.txt` files
- **Temporary File Management**: Automatically cleans up downloaded files
- **Error Handling**: Comprehensive error handling throughout the process
- **Progress Tracking**: Detailed progress reporting and success/failure summaries

## Installation

1. Install required packages:
```bash
pip install -r requirements_html_extractor.txt
```

2. Install ChromeDriver:
   - Download from: https://chromedriver.chromium.org/
   - Add to your system PATH
   - Or use a package manager like `brew install chromedriver` (macOS)

## Usage

### 1. Process CSV File (Recommended)

Process all URLs from `pfof_articles2.csv`:

```bash
python process_pfof_csv.py
```

This will:
- Read URLs from the CSV file
- Extract content from each URL
- Include CSV metadata (URL, title, date, sentiment) in output
- Save results to `pfof_extracted_content/` directory

### 2. Process Single URL

```python
from html_content_extractor import HTMLContentExtractor

extractor = HTMLContentExtractor(headless=True, timeout=30)
success = extractor.extract_from_url("https://example.com", "output.txt")
extractor.cleanup()
```

### 3. Process CSV File Directly

```bash
python html_content_extractor.py pfof_articles2.csv
```

### 4. Process Custom CSV

```python
from html_content_extractor import HTMLContentExtractor

extractor = HTMLContentExtractor(headless=True, timeout=30)
results = extractor.process_csv_file("your_file.csv", "output_directory")
extractor.print_processing_summary(results)
extractor.cleanup()
```

## Output Format

Each extracted content file contains:

```
================================================================================
EXTRACTED CONTENT
================================================================================

CSV METADATA:
----------------------------------------
URL: https://example.com/article
Title: Article Title from CSV
Date: 9/9/25
Sentiment: Neutral

EXTRACTED TITLE: Actual Article Title from Webpage

EXTRACTED METADATA:
----------------------------------------
Description: Article description
Keywords: keyword1, keyword2
Canonical Link: https://example.com/canonical
Domain: example.com
Publish Date: 2025-09-09
Authors: Author Name
Tags: tag1, tag2

BODY:
----------------------------------------
Full article content here...
```

## File Structure

```
/Users/adamsussman/Documents/606_app/
├── html_content_extractor.py          # Main extractor class
├── process_pfof_csv.py               # CSV processing script
├── example_usage.py                   # Usage examples
├── requirements_html_extractor.txt    # Dependencies
├── pfof_articles2.csv               # Input CSV file
└── pfof_extracted_content/           # Output directory
    ├── row_001_investopedia_com_extracted.txt
    ├── row_002_ft_com_extracted.txt
    └── ...
```

## Configuration Options

### HTMLContentExtractor Parameters

- `headless=True`: Run browser in headless mode (no GUI)
- `timeout=30`: Page loading timeout in seconds

### CSV Processing Options

- `csv_file_path`: Path to CSV file
- `output_dir`: Directory for extracted content
- `url_column`: Name of column containing URLs (default: "url")

## Error Handling

The script includes comprehensive error handling:

- **Network Issues**: Timeout and connection errors
- **Invalid URLs**: Malformed or unreachable URLs
- **Missing CSV Columns**: Handles missing URL column
- **File System Errors**: Permission and disk space issues
- **WebDriver Issues**: Chrome/ChromeDriver problems

## Performance Tips

1. **Headless Mode**: Always use `headless=True` for better performance
2. **Timeout Settings**: Adjust timeout based on your network speed
3. **Batch Processing**: Process multiple URLs in sequence with delays
4. **Resource Cleanup**: Always call `cleanup()` to free resources

## Troubleshooting

### Common Issues

1. **ChromeDriver not found**:
   ```bash
   # Install ChromeDriver
   brew install chromedriver  # macOS
   # Or download from https://chromedriver.chromium.org/
   ```

2. **Import errors**:
   ```bash
   pip install -r requirements_html_extractor.txt
   ```

3. **Timeout errors**:
   - Increase timeout value
   - Check network connectivity
   - Some sites may block automated access

4. **Memory issues**:
   - Process smaller batches
   - Ensure adequate system memory

### Debug Mode

Run with visible browser for debugging:
```python
extractor = HTMLContentExtractor(headless=False, timeout=60)
```

## Example Output

After processing `pfof_articles2.csv`, you'll get:

- **237 text files** (one per URL in CSV)
- **Structured content** with CSV metadata included
- **Progress summary** showing success/failure rates
- **Error logs** for failed extractions

## Advanced Usage

### Custom CSV Format

The script works with any CSV file containing a URL column. Just specify the column name:

```python
results = extractor.process_csv_file(
    "custom_file.csv", 
    "custom_output", 
    url_column="website_url"
)
```

### Batch Processing with Custom Metadata

```python
# Process with custom metadata
csv_metadata = {
    'url': 'https://example.com',
    'title': 'Custom Title',
    'date': '2025-01-01',
    'sentiment': 'Positive'
}

success = extractor.extract_from_url(
    url, 
    "output.txt", 
    csv_metadata
)
```

This enhanced script provides a complete solution for extracting content from web pages with full CSV integration and metadata preservation.
