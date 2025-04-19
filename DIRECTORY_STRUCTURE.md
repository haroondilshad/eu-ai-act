# EU AI Act Compliance Analysis Tool - Directory Structure

This document describes the directory structure and file organization of the EU AI Act Compliance Analysis Tool.

## Overview

The tool organizes test results in a clear, timestamp-based structure with subdirectories for each risk type. This approach provides several benefits:

1. Easy identification of results by date and time
2. Clear separation of different risk categories
3. Availability of both DOCX and TXT formats for all reports
4. Preservation of source documents in their original and text formats

## Directory Structure

```
output/
├── reports/                       # Individual reports
│   └── *.docx, *.txt              # Report files
│
└── test_results/                  # Organized test results
    └── test_run_YYYY-MM-DD_HH-MM-SS/  # Timestamped test run
        ├── prohibited/            # Prohibited systems
        │   ├── *_report.docx      # Report in DOCX format
        │   ├── *_report.txt       # Report in TXT format
        │   ├── raw_*.txt          # Original document in text format
        │   └── original.*         # Original document in native format
        │
        ├── high-risk/             # High-risk systems
        │   └── ...                # Similar structure as above
        │
        ├── limited-risk/          # Limited-risk systems
        │   └── ...                # Similar structure as above
        │
        ├── minimal-risk/          # Minimal-risk systems
        │   └── ...                # Similar structure as above
        │
        └── unknown/               # Systems with undetermined risk
            └── ...                # Similar structure as above
```

## File Types

### Report Files

Each analysis generates two versions of the report:

1. **DOCX Report** (`.docx`): Full-featured report with formatting, colors, and images.
2. **TXT Report** (`.txt`): Plain text version of the report for compatibility, search, and archiving.

### Document Files

Each analyzed document is preserved in multiple formats:

1. **Original Document**: The source file in its native format (PDF, DOCX, TXT, etc.)
2. **Text Version** (`raw_*.txt`): Extracted text content from the original document

## Benefits of New Structure

- **Timestamped Organization**: Each test run is clearly marked with a human-readable timestamp.
- **Risk-Based Classification**: Results are automatically organized by risk category for easy reference.
- **Format Flexibility**: Having both DOCX and TXT versions enables different use cases:
  - DOCX for full visual presentation
  - TXT for easy searching, text processing, and archiving
- **Source Preservation**: Original documents are preserved alongside analysis results.

## Using the Structure

To run the compliance analysis with this new directory structure:

```bash
./run_implementation.sh
```

The script will process the documents, organize the results in the structure described above, and provide a summary of the findings for each risk category.

Additional options:
- `--force-embeddings`: Force regeneration of embeddings
- `--skip-retrieval`: Skip semantic retrieval (useful when Pinecone is not configured) 