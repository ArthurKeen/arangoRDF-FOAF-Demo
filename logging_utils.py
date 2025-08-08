#!/usr/bin/env python3
"""
Shared logging utilities for the FOAF demonstration project.
Provides consistent logging configuration across all modules.

Author: Arthur Keen
Date: January 2025
"""

import logging
import sys
from typing import Optional


def setup_logging(
    name: str,
    level: str = "INFO",
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Set up standardized logging configuration
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string (optional)
        
    Returns:
        Configured logger instance
    """
    if format_string is None:
        format_string = '%(asctime)s - %(levelname)s - %(message)s'
    
    # Set up basic config (only affects root logger if not already configured)
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        stream=sys.stdout
    )
    
    # Return named logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    return logger


def setup_module_logging(module_name: str) -> logging.Logger:
    """
    Standard logging setup for FOAF demo modules
    
    Args:
        module_name: Name of the module (typically __name__)
        
    Returns:
        Configured logger for the module
    """
    return setup_logging(
        name=module_name,
        level="INFO",
        format_string='%(asctime)s - %(levelname)s - %(message)s'
    )


def setup_verbose_logging(module_name: str) -> logging.Logger:
    """
    Verbose logging setup for debugging
    
    Args:
        module_name: Name of the module (typically __name__)
        
    Returns:
        Configured logger with DEBUG level
    """
    return setup_logging(
        name=module_name,
        level="DEBUG",
        format_string='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
