import logging


# Default log level
_CURRENT_LOG_LEVEL = logging.INFO

def set_log_level(level_name: str):
    """
    Sets the global log level based on a string name (e.g., 'DEBUG', 'INFO').
    Case-insensitive.
    """
    global _CURRENT_LOG_LEVEL
    
    level_name = level_name.upper()
    level = getattr(logging, level_name, logging.INFO)
    
    _CURRENT_LOG_LEVEL = level
    
    # Optionally update existing loggers if needed, or just the root logger?
    # For now, we mainly control future get_logger calls, or we can force update root.
    logging.getLogger().setLevel(level)

def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger with the current global level and standard formatting.
    Safe to call multiple times (clears existing handlers to prevent duplicates).
    """
    logger = logging.getLogger(name)
    logger.setLevel(_CURRENT_LOG_LEVEL)
    
    # Check if a handler is already set to avoid duplication
    if logger.hasHandlers():
        logger.handlers.clear()
        
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

