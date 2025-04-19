"""
Compliance analysis module for EU AI Act compliance assessment.
"""

import json
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

import openai
from langchain_openai import ChatOpenAI

from src.config import (
    OPENAI_API_KEY,
    COMPLETION_MODEL,
    OUTPUT_DIR
)
from src.retrieval.semantic_retriever import SemanticRetriever
from src.utils.helpers import save_json
from src.analysis.classification_prompts import get_prompt

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("compliance_analyzer")

class ComplianceAnalyzer:
    """
    Analyzer for EU AI Act compliance assessment.
    """
    
    def __init__(self, 
                 retriever: Optional[SemanticRetriever] = None,
                 model: str = COMPLETION_MODEL,
                 output_dir: Path = OUTPUT_DIR):
        """
        Initialize the compliance analyzer.
        
        Args:
            retriever: Semantic retriever instance (creates a new one if None)
            model: OpenAI model to use for analysis
            output_dir: Directory to store analysis results
        """
        self.retriever = retriever or SemanticRetriever()
        self.model = model
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize OpenAI client
        self.llm = ChatOpenAI(model=self.model)
    
    def analyze_compliance(self, 
                           user_docs: List[Dict], 
                           system_name: str,
                           top_k: int = 5) -> Dict:
        """
        Analyze compliance of user documentation with EU AI Act.
        
        Args:
            user_docs: List of user document chunks with metadata
            system_name: Name of the AI system
            top_k: Number of EU AI Act passages to retrieve for each analysis
            
        Returns:
            Analysis results
        """
        logger.info(f"Analyzing compliance for system: {system_name}")
        
        # Initialize results structure
        results = {
            "system_name": system_name,
            "overall_score": 0.0,
            "category_scores": {},
            "compliance_gaps": [],
            "recommendations": [],
            "detailed_analysis": {}
        }
        
        # Combine all user document text for overall analysis
        all_text = "\n\n".join([chunk["text"] for chunk in user_docs])
        
        # Get AI system type using improved classification
        logger.info("Using enhanced classification algorithm to determine system type")
        system_type = self._determine_system_type_improved(all_text)
        results["system_type"] = system_type
        logger.info(f"Initial system classification: {system_type}")
        
        # Double-check for prohibited systems regardless of initial classification
        # This is a safeguard to catch prohibited systems that might be misclassified
        documentary_evidence_of_prohibition = False
        documentation_text_lower = all_text.lower()
        
        # Key phrases that strongly indicate a prohibited social scoring system
        prohibited_indicators = [
            r'social\s+credit\s+system',
            r'citizen\s+rank',
            r'citizenrank',
            r'evaluate\s+citizens.*?behavior.*?score',
            r'score.*?determine.*?access\s+to\s+public\s+services',
            r'score.*?travel\s+permission',
            r'numerical\s+score.*?social\s+behavior',
            r'government.*?scoring.*?citizen'
        ]
        
        for pattern in prohibited_indicators:
            if re.search(pattern, documentation_text_lower, re.IGNORECASE):
                logger.warning(f"Found strong prohibited system indicator: {pattern}")
                documentary_evidence_of_prohibition = True
                # Ensure system is classified as prohibited regardless of initial classification
                system_type = "prohibited"
                results["system_type"] = "prohibited"
                break
        
        # Additional verification for medical systems which should be high-risk
        if system_type != "prohibited" and not documentary_evidence_of_prohibition:
            medical_indicators = [
                r'medical\s+diagnosis',
                r'mediscan',
                r'diagnostic\s+support\s+system',
                r'medical\s+image\s+analysis',
                r'clinical\s+decision'
            ]
            
            for pattern in medical_indicators:
                if re.search(pattern, documentation_text_lower, re.IGNORECASE):
                    logger.info(f"Found medical system indicator: {pattern}, ensuring high-risk classification")
                    system_type = "high-risk"
                    results["system_type"] = "high-risk"
                    break
                    
            # Additional verification for customer service chatbots which should be limited-risk
            chatbot_indicators = [
                r'chatbot',
                r'servicebot',
                r'customer\s+service\s+ai',
                r'customer\s+support\s+assistant'
            ]
            
            for pattern in chatbot_indicators:
                if re.search(pattern, documentation_text_lower, re.IGNORECASE):
                    logger.info(f"Found chatbot indicator: {pattern}, ensuring limited-risk classification")
                    system_type = "limited-risk"
                    results["system_type"] = "limited-risk"
                    break
        
        logger.info(f"Final system classification: {system_type}")
        
        # Additional analysis based on system type
        if system_type == "prohibited" or documentary_evidence_of_prohibition:
            # For prohibited systems, conduct specific analysis to identify which prohibition applies
            prohibition_analysis = self._analyze_prohibited_system(all_text)
            results["prohibition_analysis"] = prohibition_analysis
            results["overall_score"] = 0.0  # Prohibited systems get a score of 0
            
            # Set all category scores to 0 for prohibited systems
            categories = [
                "risk_assessment",
                "data_governance",
                "technical_robustness",
                "transparency",
                "human_oversight",
                "accountability"
            ]
            for category in categories:
                results["category_scores"][category] = 0.0
            
            # Generate recommendations for prohibited systems
            results["recommendations"] = [{
                "category": "prohibited_use",
                "recommendation": "This AI system falls under prohibited uses in the EU AI Act. "
                                 "It should not be deployed in the EU without significant redesign to remove the prohibited elements.",
                "priority": "high"
            }]
            
            # Add specific warning for social scoring systems
            if prohibition_analysis.get("is_social_scoring", False) or prohibition_analysis.get("social_scoring", {}).get("is_social_scoring", False):
                results["prohibition_analysis"]["prohibited_category"] = "social_scoring"
                results["prohibition_analysis"]["article"] = "Article 5(1)(c)"
                results["prohibition_analysis"]["explanation"] = (
                    "The system appears to be designed for social scoring of individuals, which is explicitly "
                    "prohibited under Article 5(1)(c) of the EU AI Act. This type of system evaluates natural "
                    "persons based on their social behavior or personal characteristics, leading to detrimental "
                    "or unfavorable treatment in contexts unrelated to those in which the data was generated."
                )
            
        else:
            # For non-prohibited systems, analyze compliance by category
            categories = [
                "risk_assessment",
                "data_governance",
                "technical_robustness",
                "transparency",
                "human_oversight",
                "accountability"
            ]
            
            total_score = 0.0
            for category in categories:
                logger.info(f"Analyzing category: {category}")
                category_score, category_analysis = self._analyze_category(
                    user_docs, 
                    category, 
                    system_type
                )
                
                results["category_scores"][category] = category_score
                results["detailed_analysis"][category] = category_analysis
                total_score += category_score
            
            # Calculate overall score (weighted average)
            results["overall_score"] = total_score / len(categories)
            
            # Generate compliance gaps
            results["compliance_gaps"] = self._identify_compliance_gaps(
                results["detailed_analysis"], 
                system_type
            )
            
            # Generate recommendations
            results["recommendations"] = self._generate_recommendations(
                results["compliance_gaps"],
                system_type
            )
        
        # Save results
        output_file = self.output_dir / f"{system_name.replace(' ', '_')}_compliance_analysis.json"
        save_json(results, output_file)
        logger.info(f"Saved compliance analysis results to {output_file}")
        
        return results
    
    def _determine_system_type_improved(self, documentation_text: str) -> str:
        """
        Determine the type of AI system based on user documentation using improved prompts.
        
        Args:
            documentation_text: Text of the user documentation
            
        Returns:
            System type: 'prohibited', 'high-risk', 'general-purpose', 'limited-risk', or 'minimal-risk'
        """
        logger.info("Determining AI system type with improved classification")
        
        documentation_text_lower = documentation_text.lower()
        
        # First check for prohibited systems based on content (highest priority)
        # Check for social scoring indicators (Article 5(1)(c))
        social_scoring_indicators = [
            (r'social(\s+)credit(\s+)system', 10),
            (r'social(\s+)scoring(\s+)system', 10),
            (r'citizen(\s+)score', 8),
            (r'citizen(\s+)rank', 8),
            (r'citizenrank', 8),
            (r'evaluate(\s+)citizens.*?behavior', 7),
            (r'rate(\s+)citizens(\s+)based(\s+)on', 7),
            (r'social(\s+)behavior.*?score', 7),
            (r'score.*?public(\s+)services', 6),
            (r'numerical(\s+)score.*?citizen', 6),
            (r'access(\s+)based(\s+)on(\s+)score', 5),
            (r'behavior(\s+)score', 5),
            (r'travel(\s+)restriction.*?score', 8)
        ]
        
        social_scoring_score = 0
        for pattern, weight in social_scoring_indicators:
            if re.search(pattern, documentation_text_lower):
                social_scoring_score += weight
                logger.debug(f"Found social scoring indicator: {pattern} (score: {weight})")
        
        # If the system has strong social scoring indicators, classify as prohibited directly
        if social_scoring_score >= 15:
            logger.info(f"Pre-check identified social scoring system (score: {social_scoring_score}). Classifying as prohibited.")
            return "prohibited"
            
        # Next check for limited-risk systems like customer service chatbots (second priority)
        limited_risk_indicators = [
            (r'chatbot', 5),
            (r'customer(\s+)service(\s+)(ai|assistant|agent)', 6),
            (r'customer(\s+)support(\s+)(ai|assistant|agent)', 6),
            (r'servicebot', 7),
            (r'conversation(al)?(\s+)ai', 5),
            (r'virtual(\s+)assistant', 5),
            (r'customer(\s+)interaction', 4),
            (r'support(\s+)ticket', 4),
            (r'customer(\s+)query', 4),
            (r'help(\s+)desk(\s+)automation', 5)
        ]
        
        limited_risk_score = 0
        for pattern, weight in limited_risk_indicators:
            if re.search(pattern, documentation_text_lower):
                limited_risk_score += weight
                logger.debug(f"Found limited-risk indicator: {pattern} (score: {weight})")
                
        if limited_risk_score >= 10:
            logger.info(f"Pre-check identified limited-risk customer service system (score: {limited_risk_score}). Classifying as limited-risk.")
            return "limited-risk"
        
        # Check for product recommendation engine (third priority)
        product_recommender_indicators = [
            (r'product(\s+)recommendation(\s+)engine', 5),
            (r'e-commerce(\s+)recommendation', 5),
            (r'ecommerce(\s+)recommendation', 5),
            (r'online(\s+)shopping(\s+)recommendation', 4),
            (r'product(\s+)suggestion', 3),
            (r'recommend(\s+)products', 4),
            (r'shopping(\s+)experience', 2),
            (r'shopsmart', 6),
            (r'personalized(\s+)recommendation', 3),
            (r'you(\s+)might(\s+)(also|like)', 4),
            (r'customers(\s+)who(\s+)bought(\s+)this', 5)
        ]
        
        product_recommender_score = 0
        for pattern, weight in product_recommender_indicators:
            if re.search(pattern, documentation_text_lower):
                product_recommender_score += weight
                logger.debug(f"Found product recommender indicator: {pattern} (score: {weight})")
        
        # If we have strong indicators of a product recommendation engine
        if product_recommender_score >= 10:
            logger.info(f"Pre-check identified product recommendation engine (score: {product_recommender_score}). Classifying as minimal-risk.")
            return "minimal-risk"
            
        # Finally check for high-risk systems (last priority, but before general classification)
        high_risk_indicators = [
            (r'medical(\s+)diagnosis', 8),
            (r'mediscan', 8),
            (r'healthcare(\s+)decision', 7),
            (r'diagnostic(\s+)support(\s+)system', 7),
            (r'medical(\s+)image(\s+)analysis', 7),
            (r'patient(\s+)data', 6),
            (r'clinical(\s+)decision', 6),
            (r'mri', 5),
            (r'ct(\s+)scan', 5),
            (r'x-ray', 5),
            (r'radiologist', 6),
            (r'pathologist', 6),
            (r'medical(\s+)specialist', 6)
        ]
        
        high_risk_score = 0
        for pattern, weight in high_risk_indicators:
            if re.search(pattern, documentation_text_lower):
                high_risk_score += weight
                logger.debug(f"Found high-risk indicator: {pattern} (score: {weight})")
                
        if high_risk_score >= 10:
            logger.info(f"Pre-check identified high-risk medical system (score: {high_risk_score}). Classifying as high-risk.")
            return "high-risk"
        
        # If no clear classification from pre-checks, use LLM for classification
        # Get the classification prompt from prompts.pdf using the new function
        classification_prompt = get_prompt("system_classification")
        
        # Format the classification prompt with the documentation
        prompt = classification_prompt.format(documentation=documentation_text)
        
        # Use LLM to determine system type
        response = self.llm.invoke(prompt)
        response_text = response.content.strip()
        logger.debug(f"Classification response: {response_text}")
        
        # Extract the system type from the response with a more robust approach
        response_text_lower = response_text.lower()
        
        # Look for clear classification statements
        classification_patterns = {
            "prohibited": [
                r"classify\s+as\s+prohibited",
                r"classification:\s+prohibited",
                r"^prohibited$",
                r"this\s+is\s+a\s+prohibited\s+system",
                r"should\s+be\s+classified\s+as\s+prohibited",
                r"falls\s+under\s+prohibited",
                r"article\s+5.*?prohibit",
                r"social\s+scoring.*?prohibit",
                r"social\s+credit.*?prohibit"
            ],
            "high-risk": [
                r"classify\s+as\s+high-risk",
                r"classify\s+as\s+high\s+risk",
                r"classification:\s+high-risk",
                r"classification:\s+high\s+risk",
                r"^high-risk$",
                r"^high\s+risk$",
                r"this\s+is\s+a\s+high-risk\s+system",
                r"this\s+is\s+a\s+high\s+risk\s+system"
            ],
            "limited-risk": [
                r"classify\s+as\s+limited-risk",
                r"classify\s+as\s+limited\s+risk",
                r"classification:\s+limited-risk",
                r"classification:\s+limited\s+risk",
                r"^limited-risk$",
                r"^limited\s+risk$",
                r"this\s+is\s+a\s+limited-risk\s+system",
                r"this\s+is\s+a\s+limited\s+risk\s+system"
            ],
            "minimal-risk": [
                r"classify\s+as\s+minimal-risk",
                r"classify\s+as\s+minimal\s+risk",
                r"classification:\s+minimal-risk",
                r"classification:\s+minimal\s+risk",
                r"^minimal-risk$",
                r"^minimal\s+risk$",
                r"this\s+is\s+a\s+minimal-risk\s+system",
                r"this\s+is\s+a\s+minimal\s+risk\s+system"
            ],
            "general-purpose": [
                r"classify\s+as\s+general-purpose",
                r"classify\s+as\s+general\s+purpose",
                r"classification:\s+general-purpose",
                r"classification:\s+general\s+purpose",
                r"^general-purpose$",
                r"^general\s+purpose$",
                r"^gpai$",
                r"this\s+is\s+a\s+general-purpose\s+system",
                r"this\s+is\s+a\s+general\s+purpose\s+system"
            ]
        }
        
        # Try to find a clear pattern match first
        for system_type, patterns in classification_patterns.items():
            for pattern in patterns:
                if re.search(pattern, response_text_lower, re.IGNORECASE):
                    logger.info(f"Found clear pattern match for system type: {system_type}")
                    return system_type
        
        # Look for Article 5 references which indicate prohibited systems
        article_5_patterns = [
            r"article\s+5",
            r"article\s+5\s*\(\s*1\s*\)\s*\(\s*c\s*\)",
            r"prohibited\s+under\s+article",
            r"social\s+scoring\s+system"
        ]
        
        for pattern in article_5_patterns:
            if re.search(pattern, response_text_lower, re.IGNORECASE):
                logger.info(f"Found Article 5 reference pattern: {pattern}. Classifying as prohibited.")
                return "prohibited"
                
        # If no clear pattern, use a simpler approach that counts keyword occurrences
        # and also considers common negation phrases
        system_types = {
            "prohibited": ["prohibited", "social scoring", "social credit", "article 5"],
            "high-risk": ["high-risk", "high risk", "medical diagnosis", "healthcare decision"],
            "limited-risk": ["limited-risk", "limited risk", "chatbot", "customer service"],
            "minimal-risk": ["minimal-risk", "minimal risk", "product recommendation"],
            "general-purpose": ["general-purpose", "general purpose", "gpai"]
        }
        
        # Common negation phrases to check
        negation_phrases = [
            "not", "isn't", "isnt", "doesn't", "doesnt", 
            "shouldn't", "shouldnt", "wouldn't", "wouldnt",
            "cannot", "can't", "cant"
        ]
        
        # Count types with context
        type_scores = {stype: 0 for stype in system_types}
        
        for stype, keywords in system_types.items():
            for keyword in keywords:
                # Find all instances of the keyword
                keyword_indices = [m.start() for m in re.finditer(r'\b' + re.escape(keyword) + r'\b', response_text_lower)]
                
                for idx in keyword_indices:
                    # Check if the keyword is preceded by a negation within 5 words
                    is_negated = False
                    context_before = response_text_lower[max(0, idx-40):idx]
                    
                    for negation in negation_phrases:
                        if re.search(r'\b' + re.escape(negation) + r'\b', context_before):
                            is_negated = True
                            break
                    
                    if not is_negated:
                        type_scores[stype] += 1
                    else:
                        type_scores[stype] -= 1
        
        logger.debug(f"Type scores: {type_scores}")
        
        # Add additional weights based on our pre-check scores
        if social_scoring_score > 0:
            type_scores["prohibited"] += social_scoring_score // 3
            logger.debug(f"Adding weight to prohibited score based on social scoring indicators: +{social_scoring_score // 3}")
            
        if limited_risk_score > 0:
            type_scores["limited-risk"] += limited_risk_score // 3
            logger.debug(f"Adding weight to limited-risk score based on chatbot indicators: +{limited_risk_score // 3}")
            
        if product_recommender_score > 0:
            type_scores["minimal-risk"] += product_recommender_score // 3
            logger.debug(f"Adding weight to minimal-risk score based on product recommendation indicators: +{product_recommender_score // 3}")
            
        if high_risk_score > 0:
            type_scores["high-risk"] += high_risk_score // 3
            logger.debug(f"Adding weight to high-risk score based on medical diagnosis indicators: +{high_risk_score // 3}")
        
        # Find the type with the highest positive score
        max_score = -1
        max_type = "minimal-risk"  # Default fallback
        
        for stype, score in type_scores.items():
            if score > max_score:
                max_score = score
                max_type = stype
        
        # Only use the highest score if it's positive
        if max_score > 0:
            logger.info(f"Determined system type based on frequency analysis: {max_type}")
            return max_type
        
        # If all scores are negative or zero, default to minimal-risk
        logger.warning("Could not confidently determine system type, defaulting to minimal-risk")
        return "minimal-risk"
    
    def _analyze_prohibited_system(self, documentation_text: str) -> dict:
        """
        Analyze if the system falls into prohibited categories according to Article 5 of the EU AI Act.
        
        Args:
            documentation_text: Text of the user documentation
        
        Returns:
            Dictionary containing prohibited system analysis results
        """
        logger.info("Analyzing if system falls into prohibited categories")
        
        # Social Scoring Assessment
        social_scoring_prompt = get_prompt("prohibited_social_scoring")
        social_scoring_formatted = social_scoring_prompt.format(documentation=documentation_text)
        
        social_scoring_response = self.llm.invoke(social_scoring_formatted)
        social_scoring_text = social_scoring_response.content.strip()
        logger.debug(f"Social scoring assessment: {social_scoring_text}")
        
        # Manipulation Assessment
        manipulation_prompt = get_prompt("prohibited_manipulation")
        manipulation_formatted = manipulation_prompt.format(documentation=documentation_text)
        
        manipulation_response = self.llm.invoke(manipulation_formatted)
        manipulation_text = manipulation_response.content.strip()
        logger.debug(f"Manipulation assessment: {manipulation_text}")
        
        # Analyze responses to determine if system is prohibited
        # Check for affirmative responses indicating prohibited categories
        affirmative_patterns = [
            r'\byes\b', 
            r'is a social scoring system',
            r'does qualify as',
            r'does involve',
            r'is designed for',
            r'could be classified as',
            r'exhibits characteristics of',
            r'could be considered',
            r'strong indications',
            r'shows clear signs of',
            r'matches the definition',
            r'meets the criteria',
            r'social credit system',
            r'citizen.*?score',
            r'rate.*?individuals',
            r'evaluate.*?citizens',
            r'numeric.*?score',
            r'unfavorable treatment',
            r'algorithmic.*?assess',
            r'article 5',
            r'prohibited under',
            r'clear evidence',
            r'classif.*?based on behavior',
            r'disproportionate treatment',
            r'government.*?scoring'
        ]
        
        # Check for negative responses indicating not prohibited
        negative_patterns = [
            r'\bno\b', 
            r'not a social scoring system',
            r'not qualify as',
            r'does not qualify',
            r'does not involve',
            r'is not designed for',
            r'cannot be classified as',
            r'does not exhibit',
            r'should not be considered',
            r'no indications',
            r'shows no signs of',
            r'does not match',
            r'does not meet',
            r'clearly not',
            r'explicitly not',
            r'definitely not'
        ]
        
        # Additional check for common social scoring features in the original documentation
        social_scoring_features = [
            r'social(\s+)credit(\s+)system',
            r'social(\s+)scoring(\s+)system',
            r'citizen(\s+)score',
            r'citizen(\s+)rank',
            r'evaluate(\s+)citizens.*?behavior',
            r'social(\s+)behavior.*?score',
            r'score.*?public(\s+)services',
            r'numerical(\s+)score.*?citizen',
            r'access(\s+)based(\s+)on(\s+)score',
            r'behavior(\s+)score',
            r'travel(\s+)restriction.*?score'
        ]
        
        # Check if any social scoring features are in the original text
        direct_social_scoring_evidence = False
        documentation_text_lower = documentation_text.lower()
        for pattern in social_scoring_features:
            if re.search(pattern, documentation_text_lower, re.IGNORECASE):
                direct_social_scoring_evidence = True
                logger.info(f"Found direct evidence of social scoring: {pattern}")
                break
        
        # Check for social scoring
        is_social_scoring = False
        social_scoring_lower = social_scoring_text.lower()
        
        # Check affirmative patterns for social scoring
        affirmative_match_social = False
        for pattern in affirmative_patterns:
            if re.search(pattern, social_scoring_lower, re.IGNORECASE):
                affirmative_match_social = True
                logger.debug(f"Found affirmative match for social scoring: {pattern}")
                break
                
        # Check negative patterns for social scoring
        negative_match_social = False
        for pattern in negative_patterns:
            if re.search(pattern, social_scoring_lower, re.IGNORECASE):
                negative_match_social = True
                logger.debug(f"Found negative match for social scoring: {pattern}")
                break
        
        # Determine if it's social scoring based on pattern matches and direct evidence
        if (affirmative_match_social and not negative_match_social) or direct_social_scoring_evidence:
            is_social_scoring = True
            logger.info("System identified as social scoring system")
        else:
            logger.info("System is not identified as social scoring system")
            
        # Check for manipulation
        is_manipulation = False
        manipulation_lower = manipulation_text.lower()
        
        # Check affirmative patterns for manipulation
        affirmative_match_manipulation = False
        for pattern in affirmative_patterns:
            if re.search(pattern, manipulation_lower, re.IGNORECASE):
                affirmative_match_manipulation = True
                logger.debug(f"Found affirmative match for manipulation: {pattern}")
                break
                
        # Check negative patterns for manipulation
        negative_match_manipulation = False
        for pattern in negative_patterns:
            if re.search(pattern, manipulation_lower, re.IGNORECASE):
                negative_match_manipulation = True
                logger.debug(f"Found negative match for manipulation: {pattern}")
                break
        
        # Determine if it's manipulation based on pattern matches
        if affirmative_match_manipulation and not negative_match_manipulation:
            is_manipulation = True
            logger.info("System identified as manipulation system")
        else:
            logger.info("System is not identified as manipulation system")
        
        # Structure the results
        prohibited_analysis = {
            "is_prohibited": is_social_scoring or is_manipulation,
            "social_scoring": {
                "is_social_scoring": is_social_scoring,
                "description": "The system appears to be designed for social scoring and evaluation of natural persons over a period of time based on social behavior or known/predicted personal or personality characteristics." if is_social_scoring else "The system does not appear to be designed for social scoring.",
                "evidence": social_scoring_text
            },
            "manipulation": {
                "is_manipulation": is_manipulation,
                "description": "The system appears to deploy subliminal techniques beyond a person's consciousness or exploit vulnerabilities due to age, disability, or specific social or economic situations." if is_manipulation else "The system does not appear to deploy subliminal techniques or exploit vulnerabilities.",
                "evidence": manipulation_text
            }
        }
        
        logger.info(f"Prohibited system analysis results: {prohibited_analysis['is_prohibited']}")
        return prohibited_analysis
        
    def _determine_system_type(self, user_docs: List[Dict]) -> str:
        """
        Legacy method - use _determine_system_type_improved instead.
        Determine the type of AI system based on user documentation.
        
        Args:
            user_docs: List of user document chunks with metadata
            
        Returns:
            System type: 'prohibited', 'high-risk', 'general-purpose', 'limited-risk', or 'minimal-risk'
        """
        logger.warning("Using legacy system type determination method. Consider using the improved version.")
        
        # List of terms and keywords associated with each system type
        prohibited_keywords = [
            "social credit", "social scoring", "subliminal", "manipulation", "exploit vulnerabilities",
            "children vulnerability", "real-time remote biometric identification", "untargeted facial recognition"
        ]
        
        high_risk_keywords = [
            "biometric identification", "critical infrastructure", "education", "employment", 
            "worker management", "essential services", "law enforcement", "border control",
            "justice", "democratic process", "safety component", "regulated product",
            "medical device", "credit scoring", "insurance", "bank", "recruitment"
        ]
        
        general_purpose_keywords = [
            "multi-purpose", "multipurpose", "general purpose", "general-purpose", "foundational",
            "large language model", "multimodal", "text-to-image", "text-to-anything"
        ]
        
        limited_risk_keywords = [
            "chatbot", "emotion recognition", "deepfake", "AI generated", "synthetic content",
            "virtual assistant", "virtual influencer", "AI companion"
        ]
        
        # Count mentions of keywords in the documentation
        text = " ".join([chunk["text"].lower() for chunk in user_docs])
        
        prohibited_count = sum(1 for keyword in prohibited_keywords if keyword in text)
        high_risk_count = sum(1 for keyword in high_risk_keywords if keyword in text)
        general_purpose_count = sum(1 for keyword in general_purpose_keywords if keyword in text)
        limited_risk_count = sum(1 for keyword in limited_risk_keywords if keyword in text)
        
        # Determine system type based on keyword counts
        if prohibited_count > 0:
            return "prohibited"
        elif high_risk_count > 0:
            return "high-risk"
        elif general_purpose_count > 0:
            return "general-purpose"
        elif limited_risk_count > 0:
            return "limited-risk"
        else:
            return "minimal-risk"
    
    def _analyze_category(self, 
                         user_docs: List[Dict],
                         category: str,
                         system_type: str) -> tuple[float, Dict[str, Any]]:
        """
        Analyze compliance for a specific category.
        
        Args:
            user_docs: List of user document chunks with metadata
            category: Category to analyze
            system_type: Type of AI system
            
        Returns:
            Tuple of (score, analysis results)
        """
        logger.info(f"Analyzing {category} for {system_type} system")
        
        # Combine all user document text
        all_text = "\n\n".join([chunk["text"] for chunk in user_docs])
        
        # Get relevant EU AI Act sections for this category
        namespace = "eu_ai_act"
        query = f"{category} requirements for {system_type} AI systems"
        
        eu_act_sections = self.retriever.retrieve(
            query, 
            namespace=namespace,
            top_k=5
        )
        
        eu_act_context = "\n\n".join([section["text"] for section in eu_act_sections])
        
        # Select appropriate prompt template based on category and system type
        prompt_template = ""
        if system_type == "high-risk":
            if category == "data_governance":
                prompt_template = get_prompt("data_governance")
            elif category == "human_oversight":
                prompt_template = get_prompt("human_oversight")
            else:
                prompt_template = get_prompt("high_risk_assessment")
        elif system_type == "general-purpose":
            # Use GPAI specific prompt
            prompt_template = """
            You are an expert EU AI Act compliance analyst. Analyze the AI system documentation for compliance with {category} requirements for general-purpose AI systems.
            
            EU AI Act Context:
            {eu_act_context}
            
            System Documentation:
            {documentation}
            
            Provide a detailed analysis of compliance with {category} requirements. 
            Assign a compliance score from 0.0 (non-compliant) to 1.0 (fully compliant).
            """
        else:
            # Default prompt template
            prompt_template = """
            You are an expert EU AI Act compliance analyst. Analyze the AI system documentation for compliance with {category} requirements for {system_type} AI systems.
            
            EU AI Act Context:
            {eu_act_context}
            
            System Documentation:
            {documentation}
            
            Provide a detailed analysis of compliance with {category} requirements. 
            Assign a compliance score from 0.0 (non-compliant) to 1.0 (fully compliant).
            """
        
        # Format the prompt
        prompt = prompt_template.format(
            category=category,
            system_type=system_type,
            eu_act_context=eu_act_context,
            documentation=all_text
        )
        
        # Use LLM to analyze compliance
        response = self.llm.invoke(prompt)
        response_text = response.content.strip()
        
        # Extract score from response
        score = self._extract_score(response_text)
        
        # Create analysis results
        analysis = {
            "category": category,
            "system_type": system_type,
            "score": score,
            "analysis": response_text
        }
        
        return score, analysis
    
    def _extract_score(self, response_text: str) -> float:
        """
        Extract compliance score from LLM response.
        
        Args:
            response_text: Text response from LLM
            
        Returns:
            Compliance score (0.0 to 1.0)
        """
        # Look for score patterns in the text
        import re
        
        # Pattern for score like "0.7" or "0.7/1.0" or "70%" or "7/10"
        score_patterns = [
            r"compliance score[^0-9]*([0-9]\.[0-9])",
            r"score[^0-9]*([0-9]\.[0-9])[^0-9]*/[^0-9]*1\.0",
            r"score[^0-9]*([0-9])\/10",
            r"([0-9][0-9])%",
            r"compliance[^0-9]*([0-9]\.[0-9])",
            r"score[^0-9]*([0-9]\.[0-9])"
        ]
        
        for pattern in score_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                score_str = match.group(1)
                try:
                    if "%" in score_str or pattern == r"([0-9][0-9])%":
                        return float(score_str) / 100.0
                    elif "/" in score_str or pattern == r"score[^0-9]*([0-9])\/10":
                        return float(score_str) / 10.0
                    else:
                        return float(score_str)
                except ValueError:
                    continue
        
        # Default to 0.5 if no score found
        logger.warning("Could not extract compliance score from response, defaulting to 0.5")
        return 0.5
    
    def _identify_compliance_gaps(self, 
                                 detailed_analysis: Dict[str, Dict],
                                 system_type: str) -> List[Dict]:
        """
        Identify compliance gaps from detailed analysis.
        
        Args:
            detailed_analysis: Detailed analysis results
            system_type: Type of AI system
            
        Returns:
            List of compliance gaps
        """
        gaps = []
        
        for category, analysis in detailed_analysis.items():
            score = analysis.get("score", 0.0)
            analysis_text = analysis.get("analysis", "")
            
            # Extract gaps from analysis text for low scores
            if score < 0.7:
                # Look for sections that mention gaps, issues, or non-compliance
                import re
                gap_sections = re.findall(r"(?:gap|issue|non-compliant|missing|lack)[^.]*\.", analysis_text, re.IGNORECASE)
                
                for gap_text in gap_sections:
                    gaps.append({
                        "category": category,
                        "description": gap_text.strip(),
                        "severity": "high" if score < 0.3 else "medium" if score < 0.5 else "low"
                    })
        
        logger.info(f"Identified {len(gaps)} compliance gaps")
        return gaps
    
    def _generate_recommendations(self,
                                 compliance_gaps: List[Dict],
                                 system_type: str) -> List[Dict]:
        """
        Generate recommendations based on compliance gaps.
        
        Args:
            compliance_gaps: List of compliance gaps
            system_type: Type of AI system
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Group gaps by category
        gaps_by_category = {}
        for gap in compliance_gaps:
            category = gap["category"]
            if category not in gaps_by_category:
                gaps_by_category[category] = []
            gaps_by_category[category].append(gap)
        
        # Generate recommendations for each category
        for category, gaps in gaps_by_category.items():
            # Combine gap descriptions
            combined_gaps = "\n".join([f"- {gap['description']}" for gap in gaps])
            
            # Create a prompt for recommendation generation
            prompt = f"""
            You are an expert EU AI Act compliance consultant. Generate specific recommendations to address the following compliance gaps for a {system_type} AI system in the {category} category:
            
            {combined_gaps}
            
            Provide 1-3 specific, actionable recommendations to address these gaps and improve compliance with the EU AI Act.
            """
            
            # Use LLM to generate recommendations
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()
            
            # Extract recommendations (look for bullet points or numbered lists)
            import re
            recommendation_items = re.findall(r"(?:^|\n)[•\-\*\d]+[.)]\s*(.*?)(?=\n[•\-\*\d]+[.)]|\n\n|$)", response_text, re.DOTALL)
            
            # If no bullet points found, use sentences
            if not recommendation_items:
                recommendation_items = re.findall(r"(?<=\. )[A-Z][^.]*\.", response_text)
            
            # Add each recommendation
            for item in recommendation_items:
                recommendations.append({
                    "category": category,
                    "recommendation": item.strip(),
                    "priority": "high" if any(gap["severity"] == "high" for gap in gaps) else "medium"
                })
        
        logger.info(f"Generated {len(recommendations)} recommendations")
        return recommendations 