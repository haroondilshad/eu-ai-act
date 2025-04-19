"""
Semantic retrieval module for EU AI Act compliance analysis.
"""

import logging
import sys
from typing import Dict, List, Optional, Union

from src.embeddings.embedding_generator import EmbeddingGenerator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("semantic_retriever")

class SemanticRetriever:
    """
    Retriever for semantic search against the EU AI Act embeddings.
    """
    
    def __init__(self, embedding_generator: Optional[EmbeddingGenerator] = None):
        """
        Initialize the semantic retriever.
        
        Args:
            embedding_generator: Embedding generator instance (creates a new one if None)
        """
        self.embedding_generator = embedding_generator or EmbeddingGenerator()
    
    def retrieve(self, query: str, top_k: int = 5, namespace: str = "eu_ai_act") -> List[Dict]:
        """
        Retrieve relevant passages from the EU AI Act based on a query.
        
        Args:
            query: Query string
            top_k: Number of results to return
            namespace: Pinecone namespace to search in
            
        Returns:
            List of retrieval results with text and metadata
        """
        logger.info(f"Retrieving passages for query: '{query}'")
        results = self.embedding_generator.search_embeddings(query, top_k=top_k, namespace=namespace)
        logger.info(f"Retrieved {len(results)} results")
        return results
    
    def retrieve_for_compliance(self, user_doc_text: str, top_k: int = 5) -> List[Dict]:
        """
        Retrieve relevant passages from the EU AI Act for compliance analysis.
        
        Args:
            user_doc_text: User documentation text
            top_k: Number of results to return
            
        Returns:
            List of retrieval results with text and metadata
        """
        logger.info("Retrieving EU AI Act passages for compliance analysis")
        return self.retrieve(user_doc_text, top_k=top_k)
    
    def retrieve_specific_article(self, article_number: Union[int, str]) -> List[Dict]:
        """
        Retrieve a specific article from the EU AI Act.
        
        Args:
            article_number: Article number (e.g., 5, "5", "5(1)")
            
        Returns:
            List of retrieval results containing the specified article
        """
        article_str = str(article_number)
        logger.info(f"Retrieving Article {article_str} from EU AI Act")
        
        # First try to search for the article number in metadata
        query = f"Article {article_str}"
        results = self.retrieve(query, top_k=10)
        
        # Filter results to only include the specified article
        filtered_results = []
        for result in results:
            metadata = result.get("metadata", {})
            if metadata.get("article_number") == article_str:
                filtered_results.append(result)
        
        logger.info(f"Found {len(filtered_results)} chunks for Article {article_str}")
        return filtered_results
    
    def retrieve_by_topic(self, topic: str, top_k: int = 5) -> List[Dict]:
        """
        Retrieve passages from the EU AI Act related to a specific topic.
        
        Args:
            topic: Topic to search for (e.g., "transparency", "high-risk", "prohibited")
            top_k: Number of results to return
            
        Returns:
            List of retrieval results related to the topic
        """
        logger.info(f"Retrieving passages related to topic: '{topic}'")
        
        # Formulate a more specific query about the topic in the context of the EU AI Act
        query = f"EU AI Act requirements for {topic}"
        results = self.retrieve(query, top_k=top_k)
        
        logger.info(f"Retrieved {len(results)} results for topic '{topic}'")
        return results 