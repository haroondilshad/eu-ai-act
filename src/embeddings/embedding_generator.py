"""
Embedding generation module for EU AI Act Compliance Analysis.
"""

import logging
import sys
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Union

from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings

from src.config import (
    PINECONE_API_KEY,
    PINECONE_ENVIRONMENT,
    PINECONE_INDEX_NAME,
    EMBEDDING_MODEL
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("embedding_generator")

class EmbeddingGenerator:
    """
    Generate and store embeddings for text chunks.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 environment: Optional[str] = None,
                 index_name: Optional[str] = None,
                 embedding_model: Optional[str] = None):
        """
        Initialize the embedding generator.
        
        Args:
            api_key: Pinecone API key (defaults to config)
            environment: Pinecone environment (defaults to config)
            index_name: Pinecone index name (defaults to config)
            embedding_model: OpenAI embedding model name (defaults to config)
        """
        self.api_key = api_key or PINECONE_API_KEY
        self.environment = environment or PINECONE_ENVIRONMENT
        self.index_name = index_name or PINECONE_INDEX_NAME
        self.embedding_model = embedding_model or EMBEDDING_MODEL
        
        if not self.api_key:
            logger.error("Pinecone API key not provided or found in environment variables")
            raise ValueError("Pinecone API key is required")
        
        # Initialize OpenAI embeddings
        self.embeddings = OpenAIEmbeddings(model=self.embedding_model)
        
        # Initialize Pinecone
        self.init_pinecone()
    
    def init_pinecone(self) -> None:
        """
        Initialize the Pinecone client and ensure the index exists.
        """
        logger.info(f"Initializing Pinecone (environment: {self.environment})")
        
        # Create Pinecone client
        self.pc = Pinecone(api_key=self.api_key)
        
        # Check if the index already exists
        existing_indexes = self.pc.list_indexes().names()
        if self.index_name not in existing_indexes:
            logger.info(f"Creating new Pinecone index: {self.index_name}")
            # Create the index with the appropriate dimension for the embedding model
            # text-embedding-3-large has 3072 dimensions, text-embedding-3-small has 1536
            dimension = 3072 if "large" in self.embedding_model else 1536
            
            # Create the index - using AWS us-east-1 for free tier
            self.pc.create_index(
                name=self.index_name,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
        else:
            logger.info(f"Using existing Pinecone index: {self.index_name}")
        
        # Connect to the index
        self.index = self.pc.Index(self.index_name)
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding for a text chunk.
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        logger.debug(f"Generating embedding for text: {text[:50]}...")
        embedding = self.embeddings.embed_query(text)
        logger.debug(f"Generated embedding with {len(embedding)} dimensions")
        return embedding
    
    def store_embeddings(self, chunks: List[Dict], namespace: str = "eu_ai_act") -> List[str]:
        """
        Generate and store embeddings for a list of text chunks.
        
        Args:
            chunks: List of dictionaries containing text chunks and metadata
            namespace: Pinecone namespace to store embeddings in
            
        Returns:
            List of IDs for stored vectors
        """
        logger.info(f"Storing embeddings for {len(chunks)} chunks in namespace '{namespace}'")
        vector_ids = []
        
        for chunk in chunks:
            text = chunk["text"]
            # Filter out None values from metadata
            metadata = {k: v for k, v in chunk["metadata"].items() if v is not None}
            
            # Generate an ID for the vector
            vector_id = str(uuid.uuid4())
            vector_ids.append(vector_id)
            
            # Generate embedding
            embedding = self.generate_embedding(text)
            
            # Store embedding in Pinecone
            self.index.upsert(
                vectors=[(vector_id, embedding, {"text": text, **metadata})],
                namespace=namespace
            )
        
        logger.info(f"Stored {len(vector_ids)} embeddings in Pinecone index '{self.index_name}'")
        return vector_ids
    
    def delete_embeddings(self, vector_ids: List[str], namespace: str = "eu_ai_act") -> None:
        """
        Delete embeddings from Pinecone.
        
        Args:
            vector_ids: List of vector IDs to delete
            namespace: Pinecone namespace
        """
        logger.info(f"Deleting {len(vector_ids)} embeddings from namespace '{namespace}'")
        self.index.delete(ids=vector_ids, namespace=namespace)
        logger.info("Embeddings deleted")
    
    def delete_namespace(self, namespace: str) -> None:
        """
        Delete an entire namespace from Pinecone.
        
        Args:
            namespace: Pinecone namespace to delete
        """
        logger.info(f"Deleting namespace '{namespace}'")
        self.index.delete(delete_all=True, namespace=namespace)
        logger.info(f"Deleted namespace '{namespace}'")
    
    def search_embeddings(self, query: str, top_k: int = 5, namespace: str = "eu_ai_act") -> List[Dict]:
        """
        Search for embeddings similar to a query.
        
        Args:
            query: Search query
            top_k: Number of results to return
            namespace: Pinecone namespace to search in
            
        Returns:
            List of search results with text and metadata
        """
        logger.info(f"Searching for '{query}' in namespace '{namespace}'")
        
        # Generate embedding for the query
        query_embedding = self.generate_embedding(query)
        
        # Search Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            namespace=namespace
        )
        
        # Format results
        formatted_results = []
        for match in results.matches:
            formatted_results.append({
                "id": match.id,
                "score": match.score,
                "text": match.metadata.get("text", ""),
                "metadata": {k: v for k, v in match.metadata.items() if k != "text"}
            })
        
        logger.info(f"Found {len(formatted_results)} results")
        return formatted_results 