#!/usr/bin/env python3
"""
Test script for the EU AI Act Compliance Analysis Tool.
This script tests the full pipeline from document processing to report generation.
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Add the parent directory to the Python path
parent_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.document_processing.document_ingestion import DocumentIngestor
from src.analysis.compliance_analyzer import ComplianceAnalyzer
from src.report_generation.report_generator import ReportGenerator
from src.utils.logger import setup_logger

# Setup logger
logger = setup_logger("test_compliance_analyzer")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test the EU AI Act Compliance Analysis Tool")
    parser.add_argument("--doc_dir", default="data/user_docs", 
                        help="Directory containing user AI system documentation")
    parser.add_argument("--output_dir", default="output/reports",
                        help="Directory where reports will be saved")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    parser.add_argument("--skip-retrieval", action="store_true",
                        help="Skip semantic retrieval with Pinecone (for testing)")
    
    return parser.parse_args()

def ensure_output_directory(directory):
    """Ensure the output directory exists."""
    os.makedirs(directory, exist_ok=True)
    logger.info(f"Output directory ensured: {directory}")

def main():
    """Run the full compliance analysis pipeline."""
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Set log level
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Ensure output directory exists
    ensure_output_directory(args.output_dir)
    
    # Get current timestamp for the report filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    logger.info("Starting EU AI Act Compliance Analysis test")
    logger.info(f"Processing documents from: {args.doc_dir}")
    
    try:
        # Step 1: Process user documents
        logger.info("Step 1: Processing user documents")
        document_ingestor = DocumentIngestor(
            input_dir=Path(args.doc_dir),
            output_dir=Path("data/processed_user_docs"),
            chunk_size=800,
            chunk_overlap=100
        )
        user_docs = document_ingestor.ingest_documents(force_reprocess=True)
        logger.info(f"Processed {len(user_docs)} documents")
        
        # Step 2: Analyze compliance
        logger.info("Step 2: Analyzing compliance with EU AI Act")
        
        # For testing purposes, we can create a mock analysis result
        # This bypasses the need for Pinecone connections
        if args.skip_retrieval:
            logger.info("Using mock compliance analysis (Pinecone retrieval skipped)")
            
            # Detect document contents to determine system type
            system_type = "minimal-risk"  # default type
            all_text = ""
            
            # Flatten all documents into a single text
            for doc_id, chunks in user_docs.items():
                for chunk in chunks:
                    all_text += chunk["text"] + "\n\n"
            
            all_text_lower = all_text.lower()
            
            # Simple keyword-based detection for testing
            # First check for prohibited system indicators
            prohibited_indicators = [
                ("social credit", 10),
                ("social scoring", 10),  
                ("citizen rank", 8),
                ("citizenrank", 8),
                ("evaluate citizens behavior", 7),
                ("rate citizens based on", 7),
                ("numerical score social behavior", 7),
                ("score public services", 6),
                ("score travel permission", 7)
            ]
            
            prohibited_score = 0
            for phrase, weight in prohibited_indicators:
                if phrase in all_text_lower:
                    prohibited_score += weight
                    logger.info(f"Found prohibited indicator: {phrase} (weight: {weight})")
            
            if prohibited_score >= 10:
                system_type = "prohibited"
                logger.info(f"Detected prohibited system based on indicators (score: {prohibited_score})")
            
            # If not prohibited, check for limited-risk indicators (must check before high-risk)
            elif (("chatbot" in all_text_lower and "customer service" in all_text_lower) or
                  ("servicebot" in all_text_lower) or
                  ("customer support ai" in all_text_lower) or
                  ("limited-risk" in all_text_lower and "customer" in all_text_lower) or
                  ("ai assistant" in all_text_lower and "customer" in all_text_lower)):
                system_type = "limited-risk"
                logger.info("Detected limited-risk system (customer service chatbot)")
            
            # Check for product recommendation engine specifically (higher priority than high-risk)
            elif (("product recommendation" in all_text_lower or "recommend products" in all_text_lower) and
                  ("shopping" in all_text_lower or "e-commerce" in all_text_lower or "ecommerce" in all_text_lower)):
                system_type = "minimal-risk"
                logger.info("Detected product recommendation system (minimal-risk)")
            
            # Check for high-risk system indicators next
            elif (("medical" in all_text_lower and "diagnosis" in all_text_lower) or
                  ("healthcare" in all_text_lower and "decision" in all_text_lower) or
                  ("mediscan" in all_text_lower) or
                  ("diagnostic support system" in all_text_lower) or
                  ("medical images" in all_text_lower and "analysis" in all_text_lower) or
                  ("critical" in all_text_lower and "infrastructure" in all_text_lower) or
                  ("employment" in all_text_lower and "decision" in all_text_lower) or
                  ("law enforcement" in all_text_lower) or
                  ("education" in all_text_lower and "assessment" in all_text_lower) or
                  ("biometric" in all_text_lower and "identification" in all_text_lower) or
                  ("high-risk" in all_text_lower)):
                system_type = "high-risk"
                logger.info("Detected high-risk system based on keyword indicators")
            
            logger.info(f"System type determined for testing: {system_type}")
            
            # Create mock compliance results
            compliance_results = {
                "system_name": "Test AI System",
                "system_type": system_type,
                "overall_score": 0.75 if system_type != "prohibited" else 0.0,
                "category_scores": {
                    "risk_assessment": 0.8,
                    "data_governance": 0.7,
                    "technical_robustness": 0.75,
                    "transparency": 0.8,
                    "human_oversight": 0.7,
                    "accountability": 0.7
                },
                "compliance_gaps": [
                    {
                        "category": "data_governance",
                        "description": "Insufficient data quality measures described",
                        "severity": "medium"
                    },
                    {
                        "category": "human_oversight",
                        "description": "Limited details on human oversight procedures",
                        "severity": "medium"
                    }
                ],
                "recommendations": [
                    {
                        "category": "data_governance",
                        "recommendation": "Implement more robust data quality control measures",
                        "priority": "medium"
                    },
                    {
                        "category": "human_oversight",
                        "recommendation": "Define clearer procedures for human oversight",
                        "priority": "medium"
                    }
                ],
                "detailed_analysis": {}
            }
            
            # If it's a prohibited system, set special results
            if system_type == "prohibited":
                compliance_results["overall_score"] = 0.0
                compliance_results["category_scores"] = {k: 0.0 for k in compliance_results["category_scores"]}
                compliance_results["compliance_gaps"] = [{
                    "category": "prohibited_use",
                    "description": "This system appears to be a social scoring system, which is prohibited under Article 5 of the EU AI Act",
                    "severity": "high"
                }]
                compliance_results["recommendations"] = [{
                    "category": "prohibited_use",
                    "recommendation": "This AI system falls under prohibited uses in the EU AI Act. It should not be deployed in the EU.",
                    "priority": "high"
                }]
                compliance_results["prohibition_analysis"] = {
                    "prohibited_category": "social_scoring",
                    "article": "Article 5(1)(c)",
                    "explanation": "The system appears to be designed for social scoring of individuals, which is explicitly prohibited under the EU AI Act."
                }
        else:
            # Use the actual compliance analyzer with retrieval
            # Note: This will fail if Pinecone is not properly configured
            compliance_analyzer = ComplianceAnalyzer(output_dir=Path(args.output_dir))
            
            # Flatten all documents into a single list of chunks
            all_chunks = []
            for doc_id, chunks in user_docs.items():
                all_chunks.extend(chunks)
                
            compliance_results = compliance_analyzer.analyze_compliance(all_chunks, "Test AI System")
        
        logger.info(f"Compliance analysis completed. System type: {compliance_results.get('system_type', 'Unknown')}")
        logger.debug(f"Compliance results: {compliance_results}")
        
        # Step 3: Generate report
        logger.info("Step 3: Generating compliance report")
        report_generator = ReportGenerator(output_dir=Path(args.output_dir))
        report_files = report_generator.generate_report(compliance_results)
        logger.info(f"Report generated successfully: {report_files['docx']}")
        logger.info(f"Text report generated successfully: {report_files['txt']}")
        
        print("\n" + "="*50)
        print(f"Compliance Analysis Complete!")
        print(f"System Type: {compliance_results.get('system_type', 'Unknown')}")
        print(f"Overall Compliance Score: {compliance_results.get('overall_score', 0)*100:.1f}%")
        print(f"Report saved to: {report_files['docx']}")
        print(f"Text report saved to: {report_files['txt']}")
        print("="*50 + "\n")
        
        return 0
    
    except Exception as e:
        logger.error(f"Error during compliance analysis: {e}", exc_info=True)
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 