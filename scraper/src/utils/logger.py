import os
import sys
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import datetime


def setup_logger(
    name="content_protection_scraper", 
    log_level=logging.INFO,
    console_output=True, 
    file_output=True,
    log_dir="logs",
    rotate_size=10 * 1024 * 1024,  # 10 MB
    backup_count=5,
    log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
):
    """
    Set up and configure a logger with console and/or file handlers.
    
    Args:
        name (str): Logger name
        log_level (int): Logging level (e.g., logging.DEBUG, logging.INFO)
        console_output (bool): Enable console output if True
        file_output (bool): Enable file output if True
        log_dir (str): Directory to store log files
        rotate_size (int): Size in bytes at which to rotate log files
        backup_count (int): Number of backup log files to keep
        log_format (str): Format string for log messages
        
    Returns:
        logging.Logger: Configured logger object
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Clear any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
        
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    # File handler
    if file_output:
        # Create log directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(log_dir, f"{name}_{timestamp}.log")
        
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=rotate_size,
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger


def get_timed_rotating_logger(
    name="content_protection_scraper",
    log_level=logging.INFO,
    console_output=True,
    file_output=True,
    log_dir="logs",
    when="midnight",  # daily rotation at midnight
    interval=1,
    backup_count=30,  # keep logs for a month
    log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
):
    """
    Set up a logger with time-based log rotation.
    
    Args:
        name (str): Logger name
        log_level (int): Logging level (e.g., logging.DEBUG, logging.INFO)
        console_output (bool): Enable console output if True
        file_output (bool): Enable file output if True
        log_dir (str): Directory to store log files
        when (str): Time unit for rotation ('S', 'M', 'H', 'D', 'midnight')
        interval (int): Number of time units between rotations
        backup_count (int): Number of backup log files to keep
        log_format (str): Format string for log messages
        
    Returns:
        logging.Logger: Configured logger object
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Clear any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
        
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    # File handler with time-based rotation
    if file_output:
        # Create log directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        log_file = os.path.join(log_dir, f"{name}.log")
        
        file_handler = TimedRotatingFileHandler(
            log_file,
            when=when,
            interval=interval,
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger


class LoggerDecorator:
    """
    Decorator class for logging function calls, parameters, and execution time.
    """
    
    def __init__(self, logger=None, level=logging.INFO):
        """
        Initialize the decorator.
        
        Args:
            logger (logging.Logger): Logger to use, or None to create a new one
            level (int): Log level for the messages
        """
        self.logger = logger or setup_logger()
        self.level = level
        
    def __call__(self, func):
        """
        Wrap the function with logging capabilities.
        """
        def wrapper(*args, **kwargs):
            # Log function call
            self.logger.log(self.level, f"Calling {func.__name__}")
            
            # Call the function and time it
            start_time = datetime.datetime.now()
            try:
                result = func(*args, **kwargs)
                # Log successful execution
                execution_time = (datetime.datetime.now() - start_time).total_seconds()
                self.logger.log(
                    self.level, 
                    f"{func.__name__} completed in {execution_time:.4f}s"
                )
                return result
            except Exception as e:
                # Log exception
                execution_time = (datetime.datetime.now() - start_time).total_seconds()
                self.logger.exception(
                    f"{func.__name__} failed after {execution_time:.4f}s with error: {str(e)}"
                )
                raise
                
        # Preserve the original function's metadata
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.__module__ = func.__module__
        
        return wrapper