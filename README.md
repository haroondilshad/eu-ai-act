# EU AI Act Compliance Analysis Tool

This tool analyzes AI system documentation for compliance with the EU AI Act using RAG techniques, vector databases, LLMs, and document processing technologies.

## Features

- **EU AI Act Processing**: Ingests the EU AI Act, processes it into chunks, and stores embeddings in a vector database for semantic search.
- **Document Ingestion**: Processes user documentation (PDF, text, HTML) to extract relevant information.
- **Compliance Analysis**: Uses LLMs and semantic search to analyze compliance across multiple categories.
- **Report Generation**: Creates comprehensive compliance reports with scores, gaps, and recommendations.

## Requirements

- Python 3.9+
- OpenAI API key (for embeddings and analysis)
- Pinecone API key (for vector storage)

## Data Storage

The implementation uses a file-based JSON storage approach instead of MongoDB:

- Processed document chunks are stored as JSON files in the `data/processed_user_docs/` directory
- EU AI Act chunks are stored in `data/eu_ai_act_processed/eu_ai_act_chunks.json`
- Full text versions of processed documents are saved as `.txt` files
- Analysis results are saved as JSON files in the output directory

This approach simplifies deployment while maintaining structured data representation for compliance analysis. MongoDB configuration is included in the codebase but is optional and not required for the system to function.

## Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd eu-ai-act-compliance
   ```

2. Set up a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   Create a `.env` file with the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   PINECONE_API_KEY=your_pinecone_api_key
   PINECONE_ENVIRONMENT=your_pinecone_environment
   ```

## Usage

### 1. Add user documentation

Place your AI system documentation in the `data/user_docs` directory. Supported formats:
- PDF files
- Text files (.txt)
- Markdown files (.md)
- HTML files (.html, .htm)

### 2. Run the analysis pipeline

```
python -m src.main --system-name "Your AI System Name"
```

Options:
- `--system-name`: Name of your AI system (default: "AI System")
- `--force`: Force reprocessing of documents
- `--skip-eu-ai-act`: Skip EU AI Act processing (use existing embeddings)

### 3. View the results

The compliance report will be generated in the `output` directory as a Word document (.docx) with:
- Executive summary
- Overall compliance score
- Detailed analysis by category
- Compliance gaps
- Recommendations

## How It Works

1. **Phase 1: EU AI Act Ingestion & Embeddings**
   - Processes the EU AI Act PDF
   - Extracts text and splits into chunks
   - Generates embeddings using OpenAI's embedding model
   - Stores embeddings in Pinecone

2. **Phase 2: User Documentation Processing**
   - Ingests user documentation files
   - Extracts text and splits into chunks
   - Identifies key elements (system purpose, data practices, etc.)

3. **Phase 3: Compliance Analysis**
   - Determines AI system type based on documentation
   - Retrieves relevant EU AI Act passages using semantic search
   - Analyzes compliance across multiple categories
   - Identifies compliance gaps

4. **Phase 4: Report Generation**
   - Generates visualizations of compliance scores
   - Creates structured report with analysis results
   - Provides actionable recommendations

## Project Structure

```
eu-ai-act-compliance/
├── data/                   # Data storage
│   ├── eu_ai_act_processed/  # Processed EU AI Act chunks
│   ├── user_docs/            # User documentation
│   └── processed_user_docs/  # Processed user documentation
├── output/                 # Generated reports and visualizations
├── src/                    # Source code
│   ├── document_processing/  # Document processing modules
│   ├── embeddings/           # Embedding generation and storage
│   ├── retrieval/            # Semantic retrieval
│   ├── analysis/             # Compliance analysis
│   ├── report_generation/    # Report generation
│   ├── utils/                # Utility functions
│   ├── config.py             # Configuration
│   └── main.py               # Main script
├── templates/              # Report templates
├── .env                    # Environment variables
└── requirements.txt        # Dependencies
```

## Customization

- **Chunking Settings**: Adjust chunk size and overlap in `src/config.py`
- **Category Weights**: Modify category weights in the compliance analyzer

## License

[MIT License](LICENSE) 