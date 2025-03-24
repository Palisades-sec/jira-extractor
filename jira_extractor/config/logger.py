import logging

def setup_logger():
    """
    Configure and setup logging for the application
    
    Returns:
        logging.Logger: Configured logger instance
    """
    try:
        # Setup logging configuration
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()]
        )
        logger = logging.getLogger("jira_extractor")
        return logger
    except Exception as e:
        print(f"Failed to setup logger: {str(e)}")
        # Fallback to basic logging
        return logging.getLogger("jira_extractor")

# Create a global logger instance
logger = setup_logger() 