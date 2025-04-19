"""
Prompt templates for EU AI Act risk classification.
"""

import logging
import sys
from typing import Dict, Optional

from src.analysis.process_prompts import update_classification_prompts

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("classification_prompts")

# Cache for loaded prompts
_PROMPTS_CACHE: Optional[Dict[str, str]] = None

def get_prompts() -> Dict[str, str]:
    """
    Get classification prompts, loading from prompts.pdf if not already cached.
    
    Returns:
        Dictionary of prompt name to prompt text
    """
    global _PROMPTS_CACHE
    
    if _PROMPTS_CACHE is None:
        logger.info("Loading prompts from prompts.pdf")
        try:
            _PROMPTS_CACHE = update_classification_prompts()
            if not _PROMPTS_CACHE:
                logger.warning("Failed to load prompts from PDF, falling back to default prompts")
                _PROMPTS_CACHE = _get_default_prompts()
        except Exception as e:
            logger.error(f"Error loading prompts from PDF: {str(e)}")
            logger.info("Falling back to default prompts")
            _PROMPTS_CACHE = _get_default_prompts()
    
    return _PROMPTS_CACHE

def get_prompt(prompt_name: str) -> str:
    """
    Get a specific prompt by name.
    
    Args:
        prompt_name: Name of the prompt
        
    Returns:
        Prompt text
    """
    prompts = get_prompts()
    if prompt_name in prompts:
        return prompts[prompt_name]
    else:
        logger.warning(f"Prompt '{prompt_name}' not found, using fallback")
        # Return a default prompt if not found
        return _get_default_prompts().get(prompt_name, "")

def _get_default_prompts() -> Dict[str, str]:
    """
    Get default prompts (used as fallback if PDF parsing fails).
    
    Returns:
        Dictionary of prompt name to prompt text
    """
    return {
        "system_classification": SYSTEM_TYPE_CLASSIFICATION_PROMPT,
        "prohibited_social_scoring": SOCIAL_SCORING_ASSESSMENT_PROMPT,
        "prohibited_manipulation": MANIPULATION_ASSESSMENT_PROMPT,
        "high_risk_assessment": HIGH_RISK_ASSESSMENT_PROMPT,
        "data_governance": "",  # No default
        "human_oversight": "",  # No default
    }

# Default fallback prompts (only used if PDF parsing fails)

# System type classification prompt 
SYSTEM_TYPE_CLASSIFICATION_PROMPT = """
You are an expert EU AI Act compliance analyst. Classify the AI system described in the documentation according to the EU AI Act risk categories.

Step 1: Extract Basic System Characteristics
From the AI system documentation, extract:
● Intended purpose of the system
● Target users (internal, external, public)
● Deployment context (e.g. public space, private sector, workplace)
● AI capabilities (e.g. classification, prediction, generation, recommendation)
● Use of biometric, emotion recognition, or decision-making on individuals
● General-purpose nature (i.e. trained for broad tasks, not purpose-specific)

Step 2: Classify the System Using EU AI Act Definitions
Use the extracted information to classify the system into one of the following categories:

A. Prohibited System (Article 5)
Check if the system appears to:
● Use subliminal techniques or manipulative behavior
● Exploit vulnerable groups (children, mentally impaired)
● Enable untargeted remote biometric ID in public spaces
● Implement social scoring by governments
● Use real-time biometric categorization without exemptions
If yes → Classify as "Prohibited"

B. High-Risk System (Articles 6–7 + Annex III)
Check if the system falls into a category listed in Annex III, such as:
● Biometric identification
● Critical infrastructure (transport, water, energy)
● Education and vocational training
● Employment, HR, and worker management
● Access to essential services (banking, housing, insurance)
● Law enforcement and border control
● Administration of justice or democratic processes
● Safety components of regulated products (e.g. medical devices, cars)
If yes → Classify as "High-Risk"

C. General-Purpose AI (GPAI) System (Articles 52–56)
Check if the system:
● Is trained on broad data sets
● Can perform a wide range of tasks (e.g. text, image, speech)
● Is adapted or fine-tuned for downstream use cases
● Does not have a narrowly defined, pre-specified purpose
If yes → Classify as "GPAI" or "general-purpose"

D. Limited-Risk System (Article 52)
Check if the system:
● Is a chatbot, emotion detection system, deepfake generator, or similar interface
● Requires transparency obligations to inform users they are interacting with AI
If yes → Classify as "Limited-Risk"

E. Minimal-Risk System
If none of the above apply, and the system is:
● A productivity tool (e.g. spam filter, calculator, AI in games)
● Not making decisions that impact individuals' rights or safety
● Not subject to any transparency, risk, or sectoral obligations
→ Classify as "Minimal-Risk"

Documentation:
{documentation}

Provide your answer as one of: 'prohibited', 'high-risk', 'general-purpose', 'limited-risk', or 'minimal-risk'.
Include your reasoning for the classification, citing specific evidence from the documentation.
"""

# Detailed assessment prompt for high-risk systems
HIGH_RISK_ASSESSMENT_PROMPT = """
You are an expert EU AI Act compliance analyst. The AI system has been classified as high-risk under the EU AI Act.
Perform a detailed assessment of the system's compliance with the key requirements for high-risk AI systems.

System Documentation:
{documentation}

For each of the following requirements, assess the system's compliance level (compliant, partially compliant, or non-compliant):

1. Risk Management System (Article 9)
   - Assess if there is an ongoing risk management process throughout the system lifecycle
   - Check for identification and analysis of known and foreseeable risks
   - Verify adoption of risk mitigation measures

2. Data Governance (Article 10)
   - Evaluate data quality measures
   - Check for bias identification and mitigation
   - Verify data security and privacy protection

3. Technical Documentation (Article 11)
   - Assess if documentation is comprehensive and allows for compliance assessment
   - Check if design specifications, development methodologies are documented
   - Verify if performance metrics and limitations are documented

4. Record-Keeping (Article 12)
   - Check for automated logging capabilities
   - Assess monitoring of operation and unusual events

5. Transparency (Article 13)
   - Verify if system provides clear information to users
   - Check if limitations, performance, and purpose are disclosed
   - Assess if human oversight capabilities are documented

6. Human Oversight (Article 14)
   - Evaluate measures to enable human oversight
   - Check for ability to intervene or override system decisions
   - Assess if monitoring tools are available

7. Accuracy, Robustness, Cybersecurity (Article 15)
   - Assess performance metrics and accuracy levels
   - Check for resilience against errors or inconsistencies
   - Verify cybersecurity measures

Provide a detailed analysis for each requirement, citing specific evidence from the documentation.
For any non-compliant or partially compliant areas, provide specific recommendations to achieve compliance.
"""

# Detailed assessment prompt for general-purpose AI systems
GPAI_ASSESSMENT_PROMPT = """
You are an expert EU AI Act compliance analyst. The AI system has been classified as a general-purpose AI system under the EU AI Act.
Perform a detailed assessment of the system's compliance with the key requirements for general-purpose AI systems.

System Documentation:
{documentation}

For each of the following requirements, assess the system's compliance level (compliant, partially compliant, or non-compliant):

1. Model Documentation (Articles 53-54)
   - Check for comprehensive summary of training
   - Assess if training data characteristics are described
   - Verify if model architecture and capabilities are documented

2. Transparency Obligations (Article 52)
   - Verify disclosure that content is AI-generated
   - Check for clear labeling of AI interactions
   - Assess if limitations are properly disclosed

3. Copyright Compliance (Article 28b)
   - Check for documentation of training data sources
   - Assess compliance with copyright regulations
   - Verify measures for proper attribution

4. Risk Assessment (Article 9)
   - Evaluate risk identification procedures
   - Check for potential misuse mitigation
   - Verify harm reduction measures

Provide a detailed analysis for each requirement, citing specific evidence from the documentation.
For any non-compliant or partially compliant areas, provide specific recommendations to achieve compliance.
"""

# Social scoring assessment prompt
SOCIAL_SCORING_ASSESSMENT_PROMPT = """
You are an expert EU AI Act compliance analyst. Evaluate whether the AI system implements social scoring as prohibited under Article 5(1)(c) of the EU AI Act.

System Documentation:
{documentation}

Check the following criteria:
1. Does the system evaluate or classify natural persons over time?
2. Is the evaluation based on social behavior or personality characteristics?
3. Could the evaluation lead to unfavorable or disproportionate treatment?
4. Is the system used by public authorities or on their behalf?

Provide a detailed analysis with specific evidence from the documentation, and conclude whether the system meets the definition of prohibited social scoring under Article 5(1)(c).
"""

# Manipulation assessment prompt
MANIPULATION_ASSESSMENT_PROMPT = """
You are an expert EU AI Act compliance analyst. Evaluate whether the AI system implements manipulative or subliminal techniques as prohibited under Article 5(1)(a) of the EU AI Act.

System Documentation:
{documentation}

Check the following criteria:
1. Does the system deploy subliminal components beyond a person's consciousness?
2. Does the system materially distort human behavior in a manner that causes harm?
3. Does the system exploit vulnerabilities due to age, disability, or social/economic situation?

Provide a detailed analysis with specific evidence from the documentation, and conclude whether the system meets the definition of prohibited manipulative or subliminal techniques under Article 5(1)(a).
""" 