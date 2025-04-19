"""
Helper utilities for the EU AI Act Compliance Analysis Tool.
"""

import json
import logging
import os
import sys
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("eu_ai_act_compliance")

def save_json(data: Union[Dict, List], filepath: Union[str, Path], pretty: bool = True) -> None:
    """
    Save data to a JSON file.
    
    Args:
        data: The data to save
        filepath: Path to the output file
        pretty: Whether to format the JSON with indentation
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    indent = 2 if pretty else None
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
    
    logger.info(f"Saved JSON data to {filepath}")

def load_json(filepath: Union[str, Path]) -> Union[Dict, List]:
    """
    Load data from a JSON file.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        The loaded data
    """
    filepath = Path(filepath)
    if not filepath.exists():
        logger.error(f"File not found: {filepath}")
        raise FileNotFoundError(f"File not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"Loaded JSON data from {filepath}")
    return data

def extract_metadata_from_text(text: str) -> Dict[str, Any]:
    """
    Extract metadata from text, such as article numbers, section titles, etc.
    
    Args:
        text: The text to extract metadata from
        
    Returns:
        Dictionary containing metadata
    """
    metadata = {
        "article_number": None,
        "section_title": None,
        "is_recital": False,
        "is_annex": False,
    }
    
    # Extract article number (e.g., "Article 5", "Article 10")
    import re
    article_match = re.search(r"Article\s+(\d+(?:\s*\(\d+\))?)", text)
    if article_match:
        metadata["article_number"] = article_match.group(1).strip()
    
    # Check if it's a recital (preamble)
    if "HAVE ADOPTED THIS REGULATION" in text or "Whereas:" in text or "recital" in text.lower():
        metadata["is_recital"] = True
    
    # Check if it's an annex
    if "ANNEX" in text:
        metadata["is_annex"] = True
        annex_match = re.search(r"ANNEX\s+([IVX]+)", text)
        if annex_match:
            metadata["annex_number"] = annex_match.group(1)
    
    # Extract section title
    lines = text.split('\n')
    for line in lines[:5]:  # Check first few lines for section titles
        if line.isupper() and len(line) > 10 and len(line) < 100:
            metadata["section_title"] = line.strip()
            break
    
    return metadata

def ensure_directory(directory):
    """Ensure a directory exists, creating it if necessary."""
    os.makedirs(directory, exist_ok=True)
    return directory

def copy_to_text_format(source_path, destination_path):
    """
    Copy a file to a text format, extracting text if needed.
    
    Args:
        source_path: Path to the source file
        destination_path: Path to save the text version
        
    Returns:
        Boolean indicating success
    """
    try:
        source_path = Path(source_path)
        destination_path = Path(destination_path)
        
        # Make sure destination directory exists
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Extract text based on file type
        file_ext = source_path.suffix.lower()
        
        if file_ext == ".pdf":
            # For PDF files, extract the text
            try:
                import pypdf
                pdf_reader = pypdf.PdfReader(source_path)
                text = ""
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
                
                with open(destination_path, "w", encoding="utf-8") as f:
                    f.write(text)
                return True
            except Exception as e:
                logging.error(f"Error extracting text from PDF {source_path}: {str(e)}")
                return False
        elif file_ext in [".docx", ".doc"]:
            # For Word documents, extract the text
            try:
                from docx import Document
                doc = Document(source_path)
                text = "\n\n".join([paragraph.text for paragraph in doc.paragraphs if paragraph.text])
                
                with open(destination_path, "w", encoding="utf-8") as f:
                    f.write(text)
                return True
            except Exception as e:
                logging.error(f"Error extracting text from Word document {source_path}: {str(e)}")
                return False
        elif file_ext in [".html", ".htm"]:
            # For HTML files, strip the tags
            try:
                import re
                with open(source_path, "r", encoding="utf-8") as f:
                    html_text = f.read()
                
                # Strip HTML tags
                text = re.sub(r"<[^>]*>", "", html_text)
                
                with open(destination_path, "w", encoding="utf-8") as f:
                    f.write(text)
                return True
            except Exception as e:
                logging.error(f"Error extracting text from HTML {source_path}: {str(e)}")
                return False
        else:
            # For text files, just copy
            try:
                shutil.copy2(source_path, destination_path)
                return True
            except Exception as e:
                logging.error(f"Error copying file {source_path}: {str(e)}")
                return False
    except Exception as e:
        logging.error(f"Error in copy_to_text_format: {str(e)}")
        return False 