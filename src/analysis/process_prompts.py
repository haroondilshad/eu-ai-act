"""
Process prompts PDF to extract structured prompts for EU AI Act compliance analysis.
"""

import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pypdf

from src.config import PROMPTS_PDF

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("process_prompts")

class PromptExtractor:
    """Extract and structure prompts from the prompts PDF."""
    
    def __init__(self, pdf_path: Path = PROMPTS_PDF):
        """
        Initialize the prompt extractor.
        
        Args:
            pdf_path: Path to the prompts PDF
        """
        self.pdf_path = pdf_path
        
    def extract_text_from_pdf(self) -> str:
        """
        Extract text from the prompts PDF.
        
        Returns:
            Extracted text as a string
        """
        if not self.pdf_path.exists():
            logger.error(f"Prompts PDF not found: {self.pdf_path}")
            raise FileNotFoundError(f"Prompts PDF not found: {self.pdf_path}")
        
        logger.info(f"Extracting text from prompts PDF: {self.pdf_path}")
        pdf_reader = pypdf.PdfReader(self.pdf_path)
        text = ""
        
        for i, page in enumerate(pdf_reader.pages):
            logger.debug(f"Processing page {i+1} of {len(pdf_reader.pages)}")
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"
        
        logger.info(f"Extracted {len(text)} characters from prompts PDF")
        return text
    
    def extract_classification_prompts(self) -> Dict[str, str]:
        """
        Extract classification prompts from the PDF.
        
        Returns:
            Dictionary of prompt name to prompt text
        """
        text = self.extract_text_from_pdf()
        
        # Define patterns to identify prompts
        patterns = {
            "system_classification": r"Step 1 Qualification.*?Agent Prompt: Classify the AI System Based on Risk Category(.*?)(?:Step \d|$)",
            "prohibited_social_scoring": r"Sub-Prompt: Article 5\(1\)\(c\) – Social Scoring(.*?)(?:Sub-Prompt:|$)",
            "prohibited_manipulation": r"Sub-Prompt: Article 5\(1\)\(a\) – Manipulative or Subliminal Techniques(.*?)(?:Sub-Prompt:|$)",
            "high_risk_assessment": r"Sub-Prompt: Article 6\(1\) – Regulated Product Integration \(Annex I\)(.*?)(?:Sub-Prompt:|$)",
            "data_governance": r"Sub-Prompt: Article 10\(2\)\(a\) – Data Design Choices(.*?)(?:Sub-Prompt:|$)",
            "human_oversight": r"Sub-Prompt: Article 14\(1\) – Design for Effective Human Oversight(.*?)(?:Sub-Prompt:|$)",
        }
        
        # Extract prompts using regex patterns
        prompts = {}
        for name, pattern in patterns.items():
            match = re.search(pattern, text, re.DOTALL)
            if match:
                prompt_text = match.group(1).strip()
                prompts[name] = prompt_text
                logger.info(f"Extracted {name} prompt ({len(prompt_text)} characters)")
            else:
                logger.warning(f"Could not extract {name} prompt")
        
        # Format prompts for LLM use
        formatted_prompts = {}
        for name, prompt_text in prompts.items():
            # Clean up formatting
            formatted_text = self._format_prompt(prompt_text)
            formatted_prompts[name] = formatted_text
        
        logger.info(f"Extracted {len(formatted_prompts)} structured prompts from PDF")
        return formatted_prompts
    
    def _format_prompt(self, text: str) -> str:
        """
        Format a prompt for LLM use.
        
        Args:
            text: Raw prompt text
            
        Returns:
            Formatted prompt text
        """
        # Remove multiple whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix bullet points
        text = re.sub(r'●', '\n●', text)
        
        # Ensure proper spacing after sections
        text = re.sub(r'([.:?!])\s*([A-Z])', r'\1\n\2', text)
        
        return text.strip()

def update_classification_prompts():
    """
    Update classification prompts from the PDF and return them for use.
    
    Returns:
        Dictionary of updated prompts
    """
    logger.info("Updating classification prompts from prompts.pdf")
    extractor = PromptExtractor()
    try:
        prompts = extractor.extract_classification_prompts()
        logger.info("Successfully updated classification prompts")
        return prompts
    except Exception as e:
        logger.error(f"Failed to update classification prompts: {str(e)}")
        return {}

if __name__ == "__main__":
    """Run as a script to test prompt extraction."""
    prompts = update_classification_prompts()
    for name, prompt in prompts.items():
        print(f"\n--- {name} ---")
        print(prompt[:200] + "..." if len(prompt) > 200 else prompt)
        print(f"Length: {len(prompt)} characters") 