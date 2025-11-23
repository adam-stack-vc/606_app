# HTML Content Extractor - Usage Guide

## Command Line Arguments

The HTML Content Extractor now has comprehensive command line support with the following options:

### Basic Usage

```bash
# Process CSV file
python html_content_extractor.py --csv pfof_articles2.csv --output extracted_content

# Process single URL
python html_content_extractor.py --url "https://example.com" --output single_extract.txt
```

### All Available Options

```bash
python html_content_extractor.py --help
```

**Input Options (choose one):**
- `--csv FILE`: Process URLs from CSV file
- `--url URL`: Process single URL

**Output Options:**
- `--output PATH`: Output directory (for CSV) or file path (for single URL)
- `--url-column COLUMN`: Name of URL column in CSV (default: "url")

**Processing Options:**
- `--timeout SECONDS`: Page load timeout (default: 30)
- `--no-headless`: Run browser in visible mode (default: headless)
- `--delay SECONDS`: Delay between requests (default: 1.0)
- `--sample N`: Process only first N URLs from CSV

## Usage Examples

### 1. Process Your PFOF Articles CSV

```bash
# Process all articles
python html_content_extractor.py --csv pfof_articles2.csv --output pfof_extracted

# Process with custom settings
python html_content_extractor.py --csv pfof_articles2.csv --output pfof_extracted --timeout 60 --delay 2.0

# Process sample for testing
python html_content_extractor.py --csv pfof_articles2.csv --output pfof_sample --sample 5
```

### 2. Process Single URL

```bash
# Extract single article
python html_content_extractor.py --url "https://investopedia.com/broker/robinhood-review" --output robinhood_review.txt

# With visible browser for debugging
python html_content_extractor.py --url "https://example.com" --output debug.txt --no-headless
```

### 3. Custom CSV Format

```bash
# If your CSV has different column names
python html_content_extractor.py --csv data.csv --output results --url-column "website_url"
```

## Pipeline Integration

### Option 1: Standalone HTML Extraction

Use the HTML extractor as a separate step before running the main pipeline:

```bash
# Step 1: Extract HTML content
python html_content_extractor.py --csv pfof_articles2.csv --output html_extracted

# Step 2: Convert to JSON format for pipeline
python html_extractor_integration.py pfof_articles2.csv pipeline_input/

# Step 3: Run main pipeline
python pipeline_runner.py --csv pipeline_input/ --output-dir final_results --skip-fetch
```

### Option 2: Direct Integration

Use the integration module within your existing pipeline:

```python
from html_extractor_integration import run_html_extraction_pipeline

# Extract content and convert to JSON
results = run_html_extraction_pipeline(
    csv_file_path="pfof_articles2.csv",
    output_dir="pipeline_input",
    timeout=30,
    headless=True,
    delay=1.0
)

if results['success']:
    print("HTML extraction completed successfully")
    print(f"JSON files ready at: {results['output_dirs']['json_files']}")
```

## Output Structure

### For CSV Processing

```
pfof_extracted/
├── row_001_investopedia_com_extracted.txt
├── row_002_ft_com_extracted.txt
├── row_003_globaltrading_net_extracted.txt
└── ...
```

### For Single URL

```
robinhood_review.txt  # Single file with extracted content
```

### Text File Format

Each extracted file contains:

```
================================================================================
EXTRACTED CONTENT
================================================================================

CSV METADATA:
----------------------------------------
URL: https://investopedia.com/broker/robinhood-review
Title: Robinhood Review
Date: 9/9/25
Sentiment: Neutral

EXTRACTED TITLE: Robinhood Review 2025: Pros, Cons, and How It Compares

EXTRACTED METADATA:
----------------------------------------
Description: Comprehensive review of Robinhood trading platform...
Keywords: robinhood, trading, commission-free, investing
Canonical Link: https://investopedia.com/broker/robinhood-review
Domain: investopedia.com
Publish Date: 2025-09-09
Authors: John Smith
Tags: trading, investing, robinhood, review

BODY:
----------------------------------------
[Full article content here...]
```

## Performance Tips

### For Large CSV Files

```bash
# Use longer timeouts and delays for stability
python html_content_extractor.py --csv large_file.csv --output results --timeout 60 --delay 2.0
```

### For Testing

```bash
# Process small sample first
python html_content_extractor.py --csv pfof_articles2.csv --output test --sample 3
```

### For Debugging

```bash
# Run with visible browser to debug issues
python html_content_extractor.py --csv test.csv --output debug --no-headless --sample 1
```

## Error Handling

The script provides detailed error reporting:

- **Network timeouts**: Increase `--timeout` value
- **Missing URLs**: Check CSV column name with `--url-column`
- **Browser issues**: Try `--no-headless` for debugging
- **Rate limiting**: Increase `--delay` between requests

## Integration with Existing Pipeline

The HTML extractor can be integrated into your existing `pipeline_runner.py` workflow:

1. **Pre-processing**: Extract HTML content before main pipeline
2. **Format conversion**: Convert to JSON format compatible with pipeline
3. **Seamless integration**: Use extracted content as input for analysis pipeline

This allows you to:
- Process web content that wasn't accessible to the original fetch methods
- Use Selenium for JavaScript-heavy sites
- Apply readability cleaning for better content extraction
- Maintain CSV metadata throughout the pipeline

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
   ```bash
   # Increase timeout
   python html_content_extractor.py --csv file.csv --output results --timeout 60
   ```

4. **Memory issues**:
   ```bash
   # Process in smaller batches
   python html_content_extractor.py --csv file.csv --output results --sample 10
   ```

The HTML Content Extractor is now fully integrated with command line arguments and can work both standalone and as part of your existing pipeline workflow!
