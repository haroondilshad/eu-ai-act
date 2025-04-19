"""
PDF document processing module for EU AI Act Compliance Analysis.
"""

import re
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pypdf
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("pdf_processor")

class PDFProcessor:
    """
    Process PDF documents for text extraction and chunking.
    """
    
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100):
        """
        Initialize the PDF processor.
        
        Args:
            chunk_size: Size of text chunks for embedding (in characters)
            chunk_overlap: Overlap between chunks (in characters)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as a string
        """
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        logger.info(f"Extracting text from PDF: {pdf_path}")
        pdf_reader = pypdf.PdfReader(pdf_path)
        text = ""
        
        for i, page in enumerate(pdf_reader.pages):
            logger.debug(f"Processing page {i+1} of {len(pdf_reader.pages)}")
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"
        
        logger.info(f"Extracted {len(text)} characters from PDF")
        return text
    
    def split_into_chunks(self, text: str) -> List[str]:
        """
        Split text into chunks for embedding.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        logger.info(f"Splitting text into chunks (size={self.chunk_size}, overlap={self.chunk_overlap})")
        chunks = self.text_splitter.split_text(text)
        logger.info(f"Created {len(chunks)} text chunks")
        return chunks
    
    def extract_metadata_from_chunk(self, chunk: str) -> Dict:
        """
        Extract metadata from a text chunk.
        
        Args:
            chunk: Text chunk
            
        Returns:
            Dictionary containing metadata
        """
        metadata = {
            "article_number": None,
            "section_title": None,
            "is_recital": False,
            "is_annex": False,
        }
        
        # Extract article number
        article_match = re.search(r"Article\s+(\d+(?:\s*\(\d+\))?)", chunk)
        if article_match:
            metadata["article_number"] = article_match.group(1).strip()
        
        # Check if it's a recital (preamble)
        if "HAVE ADOPTED THIS REGULATION" in chunk or "Whereas:" in chunk or "recital" in chunk.lower():
            metadata["is_recital"] = True
        
        # Check if it's an annex
        if "ANNEX" in chunk:
            metadata["is_annex"] = True
            annex_match = re.search(r"ANNEX\s+([IVX]+)", chunk)
            if annex_match:
                metadata["annex_number"] = annex_match.group(1)
        
        # Extract section title
        lines = chunk.split('\n')
        for line in lines[:5]:  # Check first few lines for section titles
            if line.isupper() and len(line) > 10 and len(line) < 100:
                metadata["section_title"] = line.strip()
                break
        
        return metadata
    
    def process_pdf(self, pdf_path: Path) -> List[Dict]:
        """
        Process a PDF file, extract text, split into chunks, and extract metadata.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of dictionaries containing chunks with metadata
        """
        logger.info(f"Processing PDF: {pdf_path}")
        
        # Extract text from PDF
        text = self.extract_text_from_pdf(pdf_path)
        
        # Split text into chunks
        chunks = self.split_into_chunks(text)
        
        # Process chunks and extract metadata
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            metadata = self.extract_metadata_from_chunk(chunk)
            metadata["chunk_id"] = i
            metadata["source"] = str(pdf_path)
            
            processed_chunks.append({
                "text": chunk,
                "metadata": metadata
            })
        
        logger.info(f"Processed {len(processed_chunks)} chunks from PDF")
        return processed_chunks 