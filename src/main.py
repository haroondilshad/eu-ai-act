"""
Main script for running the EU AI Act compliance analysis pipeline.
"""

import argparse
import logging
import sys
from pathlib import Path

from src.config import (
    EU_AI_ACT_PDF,
    EU_AI_ACT_PROCESSED_DIR,
    USER_DOCS_DIR,
    PROCESSED_USER_DOCS_DIR,
    OUTPUT_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP
)
from src.document_processing.pdf_processor import PDFProcessor
from src.document_processing.document_ingestion import DocumentIngestor
from src.embeddings.embedding_generator import EmbeddingGenerator
from src.analysis.compliance_analyzer import ComplianceAnalyzer
from src.report_generation.report_generator import ReportGenerator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("eu_ai_act_main")

def process_eu_ai_act(force_reprocess: bool = False) -> None:
    """
    Process the EU AI Act PDF and store embeddings.
    
    Args:
        force_reprocess: Whether to force reprocessing
    """
    logger.info("Phase 1: Processing EU AI Act")
    
    # Process PDF
    pdf_processor = PDFProcessor(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    
    output_file = EU_AI_ACT_PROCESSED_DIR / "eu_ai_act_chunks.json"
    
    # Check if already processed
    if output_file.exists() and not force_reprocess:
        logger.info(f"Found existing processed file: {output_file}")
        logger.info("Use --force to reprocess")
        return
    
    # Process the PDF
    chunks = pdf_processor.process_pdf(EU_AI_ACT_PDF)
    
    # Generate and store embeddings
    embedding_generator = EmbeddingGenerator()
    
    # If force_reprocess, delete existing namespace
    if force_reprocess:
        logger.info("Deleting existing namespace")
        embedding_generator.delete_namespace("eu_ai_act")
    
    # Store embeddings
    vector_ids = embedding_generator.store_embeddings(chunks, namespace="eu_ai_act")
    logger.info(f"Stored {len(vector_ids)} embeddings in Pinecone")

def process_user_documentation(force_reprocess: bool = False) -> dict:
    """
    Process user documentation and prepare for analysis.
    
    Args:
        force_reprocess: Whether to force reprocessing
        
    Returns:
        Dictionary of processed documents
    """
    logger.info("Phase 2: Processing user documentation")
    
    document_ingestor = DocumentIngestor(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        input_dir=USER_DOCS_DIR,
        output_dir=PROCESSED_USER_DOCS_DIR
    )
    
    processed_docs = document_ingestor.ingest_documents(force_reprocess=force_reprocess)
    logger.info(f"Processed {len(processed_docs)} user documents")
    
    return processed_docs

def analyze_compliance(processed_docs: dict, system_name: str) -> dict:
    """
    Analyze compliance of user documentation with EU AI Act.
    
    Args:
        processed_docs: Dictionary of processed documents
        system_name: Name of the AI system
        
    Returns:
        Analysis results
    """
    logger.info("Phase 3: Analyzing compliance")
    
    # Flatten all documents into a single list of chunks
    all_chunks = []
    for doc_id, chunks in processed_docs.items():
        all_chunks.extend(chunks)
    
    # Create analyzer
    analyzer = ComplianceAnalyzer()
    
    # Analyze compliance
    results = analyzer.analyze_compliance(all_chunks, system_name)
    logger.info(f"Completed compliance analysis for {system_name}")
    
    return results

def generate_report(analysis_results: dict) -> Path:
    """
    Generate compliance report from analysis results.
    
    Args:
        analysis_results: Analysis results
        
    Returns:
        Path to the generated report
    """
    logger.info("Phase 4: Generating report")
    
    report_generator = ReportGenerator()
    report_path = report_generator.generate_report(analysis_results)
    
    logger.info(f"Generated compliance report: {report_path}")
    return report_path

def main():
    parser = argparse.ArgumentParser(description="EU AI Act Compliance Analysis Tool")
    parser.add_argument("--system-name", type=str, default="AI System", help="Name of the AI system")
    parser.add_argument("--force", action="store_true", help="Force reprocessing of documents")
    parser.add_argument("--skip-eu-ai-act", action="store_true", help="Skip EU AI Act processing (use existing embeddings)")
    
    args = parser.parse_args()
    
    # Create required directories
    EU_AI_ACT_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    USER_DOCS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_USER_DOCS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Process EU AI Act if not skipped
    if not args.skip_eu_ai_act:
        process_eu_ai_act(force_reprocess=args.force)
    
    # Check if user documentation exists
    user_docs_files = list(USER_DOCS_DIR.glob("**/*"))
    user_docs_files = [f for f in user_docs_files if f.is_file()]
    
    if not user_docs_files:
        logger.error(f"No user documentation found in {USER_DOCS_DIR}")
        logger.error(f"Please add documentation files to {USER_DOCS_DIR} and run again")
        return
    
    # Process user documentation
    processed_docs = process_user_documentation(force_reprocess=args.force)
    
    if not processed_docs:
        logger.error("No processed user documentation available")
        return
    
    # Analyze compliance
    analysis_results = analyze_compliance(processed_docs, args.system_name)
    
    # Generate report
    report_path = generate_report(analysis_results)
    
    # Print summary
    system_type = analysis_results.get("system_type", "undetermined")
    overall_score = analysis_results.get("overall_score", 0.0)
    score_percentage = f"{overall_score * 100:.1f}%"
    
    print("\n" + "=" * 80)
    print(f"EU AI Act Compliance Analysis for: {args.system_name}")
    print(f"System Type: {system_type.capitalize()}")
    print(f"Overall Compliance Score: {score_percentage}")
    print(f"Report generated at: {report_path}")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main() 