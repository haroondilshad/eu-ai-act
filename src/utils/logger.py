"""
Logging utilities for the EU AI Act Compliance Analysis Tool.
"""

import logging
import sys

def setup_logger(name, level=logging.INFO):
    """
    Set up a logger with the specified name and level.
    
    Args:
        name: The name of the logger
        level: The log level (default: logging.INFO)
    
    Returns:
        The configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create console handler with a higher log level
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    
    # Create formatter and add it to the handlers
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    
    # Add the handlers to the logger if they don't exist
    if not logger.handlers:
        logger.addHandler(console_handler)
    
    return logger 