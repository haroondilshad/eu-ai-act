"""
Run PDF extraction for both EU AI Act and Prompts PDFs.
"""

import argparse
import logging
import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.process_eu_ai_act import process_eu_ai_act
from src.analysis.process_prompts import update_classification_prompts
from src.config import EU_AI_ACT_PDF, EU_AI_ACT_PROCESSED_DIR

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("run_pdf_extraction")

def main():
    parser = argparse.ArgumentParser(description="Process PDF files for EU AI Act compliance analysis")
    parser.add_argument("--force", action="store_true", help="Force reprocessing even if files exist")
    parser.add_argument("--force-embeddings", action="store_true", help="Force regeneration of embeddings even if they already exist")
    parser.add_argument("--skip-eu-act", action="store_true", help="Skip processing EU AI Act PDF")
    parser.add_argument("--skip-prompts", action="store_true", help="Skip processing prompts PDF")
    parser.add_argument("--skip-embeddings", action="store_true", help="Skip storing embeddings in Pinecone")
    
    args = parser.parse_args()
    
    # Step 1: Process EU AI Act PDF
    if not args.skip_eu_act:
        logger.info("Processing EU AI Act PDF...")
        process_eu_ai_act(
            pdf_path=EU_AI_ACT_PDF,
            output_dir=EU_AI_ACT_PROCESSED_DIR,
            force_reprocess=args.force,
            force_embeddings=args.force_embeddings,
            store_embeddings=not args.skip_embeddings
        )
        logger.info("EU AI Act PDF processing complete!")
    else:
        logger.info("Skipping EU AI Act PDF processing")
    
    # Step 2: Process Prompts PDF
    if not args.skip_prompts:
        logger.info("Processing prompts PDF...")
        prompts = update_classification_prompts()
        logger.info(f"Extracted {len(prompts)} prompts from PDF")
        
        # Print prompt names
        for name in prompts.keys():
            logger.info(f"  - {name}")
    else:
        logger.info("Skipping prompts PDF processing")
    
    logger.info("PDF extraction complete! The system is now using the PDF files directly as required.")

if __name__ == "__main__":
    main() 