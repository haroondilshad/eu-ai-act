"""
Configuration settings for the EU AI Act Compliance Analysis Tool.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# EU AI Act - Updated to use the exact PDF filename as in the workspace
EU_AI_ACT_PDF = BASE_DIR / "EU-Ai-Act.pdf"  # Updated to match the actual filename
EU_AI_ACT_PROCESSED_DIR = DATA_DIR / "eu_ai_act_processed"
EU_AI_ACT_PROCESSED_DIR.mkdir(exist_ok=True)

# Prompts PDF for extraction prompts
PROMPTS_PDF = BASE_DIR / "prompts.pdf"  # Added configuration for prompts PDF

# User documentation
USER_DOCS_DIR = DATA_DIR / "user_docs"
USER_DOCS_DIR.mkdir(exist_ok=True)
PROCESSED_USER_DOCS_DIR = DATA_DIR / "processed_user_docs"
PROCESSED_USER_DOCS_DIR.mkdir(exist_ok=True)

# Pinecone settings - prioritize environment variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-east-1-aws")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "eu-ai-act-index")

# MongoDB settings
MONGODB_CONNECTION_STRING = os.getenv("MONGODB_CONNECTION_STRING", "mongodb://localhost:27017/")
MONGODB_DATABASE_NAME = os.getenv("MONGODB_DATABASE_NAME", "eu_ai_act_compliance")

# OpenAI settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-large"
COMPLETION_MODEL = "gpt-4o"

# Chunking settings
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

# Report settings
REPORT_TEMPLATE_PATH = BASE_DIR / "templates" / "report_template.docx"

# Create templates directory
(BASE_DIR / "templates").mkdir(exist_ok=True) 