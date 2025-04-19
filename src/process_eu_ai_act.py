"""
Process EU AI Act PDF and store embeddings in Pinecone.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from src.config import (
    EU_AI_ACT_PDF,
    EU_AI_ACT_PROCESSED_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP
)
from src.document_processing.pdf_processor import PDFProcessor
from src.embeddings.embedding_generator import EmbeddingGenerator
from src.utils.helpers import save_json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("process_eu_ai_act")

def process_eu_ai_act(pdf_path: Path,
                     output_dir: Path,
                     chunk_size: int = CHUNK_SIZE,
                     chunk_overlap: int = CHUNK_OVERLAP,
                     store_embeddings: bool = True,
                     namespace: str = "eu_ai_act",
                     force_reprocess: bool = False,
                     force_embeddings: bool = False) -> None:
    """
    Process the EU AI Act PDF and store embeddings in Pinecone.
    
    Args:
        pdf_path: Path to the EU AI Act PDF
        output_dir: Directory to store processed chunks
        chunk_size: Size of text chunks
        chunk_overlap: Overlap between text chunks
        store_embeddings: Whether to store embeddings in Pinecone
        namespace: Pinecone namespace to store embeddings in
        force_reprocess: Whether to force reprocessing if processed files already exist
        force_embeddings: Whether to force regeneration of embeddings even if they already exist
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "eu_ai_act_chunks.json"
    vector_ids_file = output_dir / "eu_ai_act_vector_ids.json"
    
    # Check if already processed
    if output_file.exists() and not force_reprocess:
        logger.info(f"Found existing processed file: {output_file}")
        logger.info("Use --force to reprocess")
        
        # Load processed chunks
        with open(output_file, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        logger.info(f"Loaded {len(chunks)} existing chunks")
    else:
        # Process the PDF
        logger.info(f"Processing EU AI Act PDF: {pdf_path}")
        pdf_processor = PDFProcessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks = pdf_processor.process_pdf(pdf_path)
        
        # Save processed chunks
        save_json(chunks, output_file)
        logger.info(f"Saved {len(chunks)} processed chunks to {output_file}")
    
    # Store embeddings in Pinecone
    if store_embeddings:
        # Check if vector IDs already exist and we're not forcing embedding regeneration
        if vector_ids_file.exists() and not force_reprocess and not force_embeddings:
            logger.info(f"Found existing vector IDs file: {vector_ids_file}")
            logger.info("Embeddings have already been stored in Pinecone")
            logger.info("Use --force-embeddings to regenerate embeddings")
            
            # Load vector IDs for reference
            with open(vector_ids_file, "r", encoding="utf-8") as f:
                vector_ids = json.load(f)
            logger.info(f"Loaded {len(vector_ids)} existing vector IDs")
            return
        
        logger.info("Generating and storing embeddings in Pinecone")
        embedding_generator = EmbeddingGenerator()
        
        # If force_reprocess or force_embeddings, delete existing namespace
        if force_reprocess or force_embeddings:
            logger.info(f"Deleting existing namespace: {namespace}")
            embedding_generator.delete_namespace(namespace)
        
        # Store embeddings
        vector_ids = embedding_generator.store_embeddings(chunks, namespace=namespace)
        logger.info(f"Stored {len(vector_ids)} embeddings in Pinecone")
        
        # Save vector IDs for reference
        save_json(vector_ids, vector_ids_file)
        logger.info(f"Saved vector IDs to {vector_ids_file}")

def main():
    parser = argparse.ArgumentParser(description="Process EU AI Act PDF and store embeddings")
    parser.add_argument("--pdf", type=str, default=str(EU_AI_ACT_PDF), help="Path to EU AI Act PDF")
    parser.add_argument("--output-dir", type=str, default=str(EU_AI_ACT_PROCESSED_DIR), help="Output directory for processed files")
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE, help="Chunk size for text splitting")
    parser.add_argument("--chunk-overlap", type=int, default=CHUNK_OVERLAP, help="Chunk overlap for text splitting")
    parser.add_argument("--no-store-embeddings", action="store_true", help="Do not store embeddings in Pinecone")
    parser.add_argument("--namespace", type=str, default="eu_ai_act", help="Pinecone namespace for embeddings")
    parser.add_argument("--force", action="store_true", help="Force reprocessing even if files exist")
    parser.add_argument("--force-embeddings", action="store_true", help="Force regeneration of embeddings even if they already exist")
    
    args = parser.parse_args()
    
    process_eu_ai_act(
        pdf_path=Path(args.pdf),
        output_dir=Path(args.output_dir),
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        store_embeddings=not args.no_store_embeddings,
        namespace=args.namespace,
        force_reprocess=args.force,
        force_embeddings=args.force_embeddings
    )

if __name__ == "__main__":
    main() 