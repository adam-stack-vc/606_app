#!/usr/bin/env python3
"""
Direct NMS chunks runner for analysis output directory
"""

import json
import pandas as pd
from pathlib import Path
from NMS_chunks import chunk_text

def run_chunks_on_analysis_output(analysis_dir: str, output_dir: str, chunk_size: int = 6000):
    """
    Run NMS chunks directly on analysis output directory
    """
    analysis_path = Path(analysis_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"🔍 Processing analysis output from: {analysis_path}")
    print(f"📁 Output directory: {output_path}")
    print(f"📏 Chunk size: {chunk_size} characters")
    
    # Load all enhanced documents
    enhanced_documents = []
    json_files = list(analysis_path.glob("*.json"))
    
    print(f"📄 Found {len(json_files)} JSON files:")
    for json_file in json_files:
        print(f"  - {json_file.name}")
    
    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            document = json.load(f)
        enhanced_documents.append(document)
    
    print(f"📚 Loaded {len(enhanced_documents)} enhanced documents")
    
    # Process each document
    all_chunks = []
    manifest_records = []
    
    for doc in enhanced_documents:
        filename = doc.get('filename', 'unknown')
        text = doc.get('text', '')
        
        if not text.strip():
            print(f"⚠️  Warning: No text content in {filename}")
            continue
        
        # Create manifest record
        manifest_record = {
            'filename': filename,
            'url': doc.get('url', ''),
            'date': doc.get('date', ''),
            'sentiment': doc.get('sentiment', ''),
            'companies_mentioned': ', '.join(doc.get('companies_mentioned', [])),
            'persons_mentioned': ', '.join(doc.get('persons_mentioned', [])),
            'value_chains': ', '.join(doc.get('value_chains', [])),
            'text_length': len(text),
            'total_chunks': 0  # Will be updated after chunking
        }
        
        # Chunk the text
        chunks = chunk_text(text, chunk_size)
        manifest_record['total_chunks'] = len(chunks)
        
        print(f"📝 {filename}: {len(chunks)} chunks")
        
        # Create chunk records
        for i, chunk in enumerate(chunks):
            chunk_record = {
                'filename': filename,
                'url': doc.get('url', ''),
                'date': doc.get('date', ''),
                'sentiment': doc.get('sentiment', ''),
                'companies_mentioned': ', '.join(doc.get('companies_mentioned', [])),
                'persons_mentioned': ', '.join(doc.get('persons_mentioned', [])),
                'value_chains': ', '.join(doc.get('value_chains', [])),
                'chunk_index': i,
                'total_chunks': len(chunks),
                'chunk_size': len(chunk),
                'text': chunk
            }
            all_chunks.append(chunk_record)
        
        manifest_records.append(manifest_record)
    
    if not all_chunks:
        print("❌ No chunks created!")
        return False
    
    # Save outputs
    manifest_path = output_path / "nms_manifest.csv"
    manifest_df = pd.DataFrame(manifest_records)
    manifest_df.to_csv(manifest_path, index=False)
    
    # Save chunks as JSONL
    chunks_path = output_path / "nms_chunks.jsonl"
    with open(chunks_path, 'w', encoding='utf-8') as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
    
    # Save chunks CSV (without text)
    chunks_csv_path = output_path / "nms_chunks.csv"
    chunks_df = pd.DataFrame([{k: v for k, v in chunk.items() if k != 'text'} for chunk in all_chunks])
    chunks_df.to_csv(chunks_csv_path, index=False)
    
    print(f"\n🎉 Chunking complete!")
    print(f"📊 Total chunks: {len(all_chunks)}")
    print(f"📄 Total documents: {len(enhanced_documents)}")
    print(f"📈 Average chunk size: {sum(len(c['text']) for c in all_chunks) / len(all_chunks):.0f} characters")
    print(f"\n📁 Output files:")
    print(f"  - Manifest: {manifest_path}")
    print(f"  - Chunks (full): {chunks_path}")
    print(f"  - Chunks CSV: {chunks_csv_path}")
    
    return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python run_chunks_direct.py <analysis_dir> <output_dir> [chunk_size]")
        print("Example: python run_chunks_direct.py results/analysis_output2 results/chunks_output")
        sys.exit(1)
    
    analysis_dir = sys.argv[1]
    output_dir = sys.argv[2]
    chunk_size = int(sys.argv[3]) if len(sys.argv) > 3 else 6000
    
    success = run_chunks_on_analysis_output(analysis_dir, output_dir, chunk_size)
    
    if success:
        print("\n✅ Chunking completed successfully!")
    else:
        print("\n❌ Chunking failed!")
        sys.exit(1)
