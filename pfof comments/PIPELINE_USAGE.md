# 606 App Pipeline Usage

## Overview
The `pipeline_runner.py` orchestrates the complete 606 App pipeline:
1. **Fetch Content** - Downloads and processes web content
2. **Analysis Pipeline** - Enhances documents with entity extraction and value chain analysis  
3. **NMS Chunks** - Creates chunked documents with rich metadata

## Quick Start

### Basic Usage
```bash
python pipeline_runner.py --csv-file input.csv --output-dir ./output
```

### Advanced Usage
```bash
python pipeline_runner.py \
  --csv-file input.csv \
  --output-dir ./output \
  --chunk-size 4000 \
  --skip-fetch \
  --skip-analysis
```

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--csv-file` | ✅ | - | Input CSV file with links to process |
| `--output-dir` | ✅ | - | Output directory for all results |
| `--chunk-size` | ❌ | 6000 | Target chunk size in characters |
| `--skip-fetch` | ❌ | False | Skip fetch step (use existing JSON files) |
| `--skip-analysis` | ❌ | False | Skip analysis step |
| `--skip-chunks` | ❌ | False | Skip chunks step |

## Input CSV Format

Your input CSV should have these columns:
```csv
title,url,date,sentiment
"Robinhood PFOF Analysis","https://robinhood.com/pfof","2024-01-01","positive"
"Citadel Securities Report","https://citadel.com/report","2024-01-02","neutral"
```

## Output Structure

```
output/
├── markdown_files/           # Raw markdown files
├── json_files/              # Individual JSON files (response_schema format)
├── analysis_output/         # Enhanced JSON files with analysis
├── chunks_output/           # Final chunked output
│   ├── nms_manifest.csv     # Document manifest
│   ├── nms_chunks.jsonl    # Chunked documents (JSONL)
│   ├── nms_chunks.csv      # Chunked documents (CSV)
│   └── metadata_index.json # Metadata index
└── fetch_summary.csv       # Fetch operation summary
```

## Pipeline Steps

### Step 1: Fetch Content
- Reads CSV file with links
- Fetches content using ScrapingBee API
- Creates individual JSON files matching `response_schema.json`
- Saves markdown files and summary

### Step 2: Analysis Pipeline  
- Reads JSON files from Step 1
- Extracts entities (companies, persons) using spaCy NER
- Performs value chain analysis
- Enhances documents with analysis results

### Step 3: NMS Chunks
- Reads enhanced JSON files from Step 2
- Chunks text into specified sizes
- Creates rich metadata for each chunk
- Outputs multiple formats (JSONL, CSV, manifest)

## Output Files

### Manifest CSV
Overview of all documents with metadata:
```csv
filename,url,date,value_chains,companies_mentioned,persons_mentioned,asset_classes,topic,sentiment,text_length,total_chunks
```

### Chunks JSONL
Individual chunks with full metadata:
```json
{
  "filename": "document.json",
  "url": "https://example.com",
  "date": "2024-01-01",
  "value_chains": ["trading", "execution"],
  "companies_mentioned": ["Robinhood", "Citadel"],
  "persons_mentioned": ["John Doe"],
  "asset_classes": "equities",
  "topic": "pfof",
  "sentiment": "positive",
  "chunk_index": 0,
  "total_chunks": 3,
  "chunk_size": 1500,
  "text": "Actual chunk content..."
}
```

### Metadata Index
Complete metadata for all documents:
```json
{
  "document1.json": {
    "filename": "document1.json",
    "url": "https://example.com",
    "value_chains": ["trading"],
    "companies_mentioned": ["Robinhood"],
    "persons_mentioned": ["John Doe"],
    "text": "Full document text..."
  }
}
```

## Examples

### Run Complete Pipeline
```bash
python pipeline_runner.py --csv-file data/links.csv --output-dir results/
```

### Resume from Analysis Step
```bash
python pipeline_runner.py --csv-file data/links.csv --output-dir results/ --skip-fetch
```

### Only Create Chunks
```bash
python pipeline_runner.py --csv-file data/links.csv --output-dir results/ --skip-fetch --skip-analysis
```

### Custom Chunk Size
```bash
python pipeline_runner.py --csv-file data/links.csv --output-dir results/ --chunk-size 4000
```

## Error Handling

The pipeline includes comprehensive error handling:
- ✅ Validates input files exist
- ✅ Creates output directories automatically  
- ✅ Handles API failures gracefully
- ✅ Provides detailed progress reporting
- ✅ Saves intermediate results for resumption

## Dependencies

Make sure you have these Python packages installed:
```bash
pip install pandas requests spacy boto3
python -m spacy download en_core_web_sm
```

## Environment Variables

Set your ScrapingBee API key:
```bash
export SCRAPINGBEE_API_KEY="your_api_key_here"
```

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure all files are in the same directory
2. **API errors**: Check your ScrapingBee API key and quota
3. **Memory issues**: Reduce chunk size or process fewer documents
4. **File not found**: Verify CSV file path and permissions

### Debug Mode

Add `--verbose` flag for detailed logging:
```bash
python pipeline_runner.py --csv-file data/links.csv --output-dir results/ --verbose
```
