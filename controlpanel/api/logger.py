import logging

def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger with DEBUG level and standard formatting.
    Safe to call multiple times (clears existing handlers to prevent duplicates).
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Check if a handler is already set to avoid duplication
    if logger.hasHandlers():
        logger.handlers.clear()
        
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger
