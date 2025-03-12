# src/config.py
import os

# Project paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
HASHES_DIR = os.path.join(DATA_DIR, "hashes")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

# Scraper configuration
HEADLESS_MODE = True
DEFAULT_BROWSER = "chrome"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Targets configuration - add your URLs to scan here
TARGET_URLS = [
    "https://example.com/page1",
    "https://example.com/page2",
    # Add more URLs here
]