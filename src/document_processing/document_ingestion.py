"""
Document ingestion module for processing user documentation for EU AI Act compliance analysis.
"""

import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pypdf
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import (
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    USER_DOCS_DIR,
    PROCESSED_USER_DOCS_DIR
)
from src.utils.helpers import save_json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("document_ingestion")

class DocumentIngestor:
    """
    Process user documentation for AI Act compliance analysis.
    """
    
    def __init__(self, 
                 chunk_size: int = CHUNK_SIZE, 
                 chunk_overlap: int = CHUNK_OVERLAP,
                 input_dir: Path = USER_DOCS_DIR,
                 output_dir: Path = PROCESSED_USER_DOCS_DIR):
        """
        Initialize the document ingestor.
        
        Args:
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between text chunks
            input_dir: Directory containing user documentation
            output_dir: Directory for processed files
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.input_dir = input_dir
        self.output_dir = output_dir
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def ingest_documents(self, force_reprocess: bool = False) -> Dict[str, List[Dict]]:
        """
        Ingest all documents in the input directory.
        
        Args:
            force_reprocess: Whether to force reprocessing of already processed files
            
        Returns:
            Dictionary mapping document IDs to lists of processed chunks
        """
        if not self.input_dir.exists() or not self.input_dir.is_dir():
            logger.error(f"Input directory not found: {self.input_dir}")
            raise FileNotFoundError(f"Input directory not found: {self.input_dir}")
        
        # Get list of files in input directory
        files = list(self.input_dir.glob("**/*"))
        files = [f for f in files if f.is_file()]
        
        if not files:
            logger.warning(f"No files found in input directory: {self.input_dir}")
            return {}
        
        logger.info(f"Found {len(files)} files in input directory")
        
        # Process each file
        processed_docs = {}
        for file_path in files:
            doc_id = str(file_path.relative_to(self.input_dir))
            output_file = self.output_dir / f"{doc_id.replace('/', '_')}.json"
            text_output_file = self.output_dir / f"{doc_id.replace('/', '_')}.txt"
            
            # Skip if already processed and not forcing reprocess
            if output_file.exists() and text_output_file.exists() and not force_reprocess:
                logger.info(f"Skipping already processed file: {doc_id}")
                with open(output_file, "r", encoding="utf-8") as f:
                    processed_docs[doc_id] = json.load(f)
                continue
            
            logger.info(f"Processing document: {doc_id}")
            text, chunks = self.process_file(file_path)
            
            if chunks:
                # Save processed chunks
                save_json(chunks, output_file)
                logger.info(f"Saved {len(chunks)} processed chunks for {doc_id}")
                
                # Save full text version of the file
                with open(text_output_file, "w", encoding="utf-8") as f:
                    f.write(text)
                logger.info(f"Saved text version of {doc_id}")
                
                processed_docs[doc_id] = chunks
        
        logger.info(f"Processed {len(processed_docs)} documents")
        return processed_docs
    
    def process_file(self, file_path: Path) -> Tuple[str, List[Dict]]:
        """
        Process a single file and extract text chunks.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple containing:
                - Full text of the document
                - List of processed chunks with metadata
        """
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return "", []
        
        # Extract text based on file type
        file_ext = file_path.suffix.lower()
        
        if file_ext == ".pdf":
            text = self._extract_text_from_pdf(file_path)
        elif file_ext in [".txt", ".md"]:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        elif file_ext in [".html", ".htm"]:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
                # Strip HTML tags
                text = re.sub(r"<[^>]*>", "", text)
        else:
            logger.warning(f"Unsupported file type: {file_ext} for {file_path}")
            return "", []
        
        if not text:
            logger.warning(f"No text extracted from {file_path}")
            return "", []
        
        # Split text into chunks
        chunks = self.text_splitter.split_text(text)
        logger.info(f"Split {file_path} into {len(chunks)} chunks")
        
        # Process chunks with metadata
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            # Extract metadata
            metadata = self._extract_metadata_from_user_doc(chunk)
            metadata["chunk_id"] = i
            metadata["source"] = str(file_path)
            metadata["doc_id"] = str(file_path.relative_to(self.input_dir))
            
            processed_chunks.append({
                "text": chunk,
                "metadata": metadata
            })
        
        return text, processed_chunks
    
    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as a string
        """
        try:
            pdf_reader = pypdf.PdfReader(pdf_path)
            text = ""
            
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
            
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {str(e)}")
            return ""
    
    def _extract_metadata_from_user_doc(self, text: str) -> Dict:
        """
        Extract metadata from user documentation text.
        
        Args:
            text: Text chunk
            
        Returns:
            Dictionary containing metadata
        """
        metadata = {
            "system_purpose": None,
            "data_practices": None,
            "technical_specs": None,
            "risk_assessment": None,
            "has_data_section": False,
            "has_risk_section": False,
        }
        
        # Detect sections about data
        if re.search(r"data\s+collect|personal\s+data|user\s+data|data\s+process", text.lower()):
            metadata["has_data_section"] = True
        
        # Detect sections about risk
        if re.search(r"risk|hazard|safety|security|vulnerabilit|threat", text.lower()):
            metadata["has_risk_section"] = True
        
        # Detect AI system type
        if re.search(r"high[\-\s]+risk|safety\s+component", text.lower()):
            metadata["system_type"] = "high-risk"
        elif re.search(r"general\s+purpose|foundation|large\s+language", text.lower()):
            metadata["system_type"] = "general-purpose"
        elif re.search(r"emotion\s+recognition|biometric", text.lower()):
            metadata["system_type"] = "limited-risk"
        else:
            metadata["system_type"] = "undetermined"
        
        return metadata 