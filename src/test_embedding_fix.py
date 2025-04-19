#!/usr/bin/env python3
"""
Test script to verify the fix for handling None values in metadata for Pinecone.
"""

import argparse
import logging
import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.embeddings.embedding_generator import EmbeddingGenerator
from pinecone.openapi_support.exceptions import PineconeApiException

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("test_embedding_fix")

def test_metadata_fix():
    """
    Test the fix for handling None values in metadata.
    """
    logger.info("Testing metadata fix for Pinecone")
    
    # Create a sample chunk with None values in metadata
    sample_chunk = {
        "text": "This is a test chunk to verify the Pinecone metadata fix.",
        "metadata": {
            "article_number": None,
            "section_title": "Test Section",
            "is_recital": False,
            "is_annex": True,
            "annex_number": None,
            "chunk_id": 1,
            "source": "test_source"
        }
    }
    
    # Create another chunk with all valid values
    valid_chunk = {
        "text": "This is a valid test chunk with no None values.",
        "metadata": {
            "article_number": "42",
            "section_title": "Valid Section",
            "is_recital": True,
            "is_annex": False,
            "chunk_id": 2,
            "source": "test_source"
        }
    }
    
    # Initialize the embedding generator
    try:
        embedding_generator = EmbeddingGenerator()
        
        # Create a test namespace
        test_namespace = "test_metadata_fix"
        
        # Try to delete the test namespace if it exists, but ignore 404 errors
        logger.info(f"Cleaning up test namespace: {test_namespace}")
        try:
            embedding_generator.delete_namespace(test_namespace)
        except PineconeApiException as e:
            # If the error is 404 (namespace not found), that's fine - continue
            if "404" in str(e) or "Namespace not found" in str(e):
                logger.info(f"Namespace {test_namespace} doesn't exist yet, continuing...")
            else:
                # Re-raise other API exceptions
                raise
        
        # Store the test chunks
        logger.info("Storing test chunks with None values in metadata")
        vector_ids = embedding_generator.store_embeddings(
            [sample_chunk, valid_chunk], 
            namespace=test_namespace
        )
        
        logger.info(f"Successfully stored {len(vector_ids)} test chunks")
        
        # Clean up the test namespace
        logger.info("Cleaning up test namespace")
        embedding_generator.delete_namespace(test_namespace)
        
        logger.info("Test completed successfully - the metadata fix is working!")
        return True
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Test the fix for handling None values in metadata")
    
    args = parser.parse_args()
    
    success = test_metadata_fix()
    
    if success:
        logger.info("✅ The metadata fix is working correctly")
        sys.exit(0)
    else:
        logger.error("❌ The metadata fix is not working")
        sys.exit(1)

if __name__ == "__main__":
    main() 