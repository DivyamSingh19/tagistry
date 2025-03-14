import os
import json
import time
import argparse
import logging
from src.scraper.driver_manager import DriverManager
from src.scraper.pinterest_scraper import PinterestScraper
from src.scraper.auth_manager import PinterestAuthManager
from src.processor.hash_generator import HashGenerator
from src.utils.file_handler import FileHandler
from src.utils.logger import setup_logger

def parse_arguments():
    parser = argparse.ArgumentParser(description="Pinterest Content Protection Scraper")
    parser.add_argument("--query", type=str, help="Search query for Pinterest")
    parser.add_argument("--board", type=str, help="Pinterest board URL to scrape")
    parser.add_argument("--pin", type=str, help="Pinterest pin URL to scrape")
    parser.add_argument("--scroll", type=int, default=3, help="Number of scrolls to perform")
    parser.add_argument("--limit", type=int, default=50, help="Maximum number of pins to scrape")
    parser.add_argument("--login", action="store_true", help="Log in to Pinterest")
    parser.add_argument("--credentials", type=str, help="Path to credentials file")
    parser.add_argument("--headless", action="store_true", default=False, help="Run in headless mode")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO")
    return parser.parse_args()

def main():
     
    args = parse_arguments()
    
     
    log_level = getattr(logging, args.log_level)
    logger = setup_logger(log_level=log_level)
    logger.info("Starting Pinterest content protection scraper")
    
     
    file_handler = FileHandler(logger)
    
   
    driver_manager = DriverManager(browser_type="chrome", headless=args.headless, logger=logger)
    driver = driver_manager.initialize_driver()
    
    try:
         
        pinterest_scraper = PinterestScraper(driver, logger)
        hash_generator = HashGenerator(logger)
        
       
        if args.login:
            auth_manager = PinterestAuthManager(driver, logger, credentials_file=args.credentials)
            if not auth_manager.login():
                logger.warning("Failed to log in, continuing without authentication")
        
        scraped_data = []
        hash_records = []
        
         
        if args.query:
           
            logger.info(f"Searching Pinterest for: {args.query}")
            pins = pinterest_scraper.search_pinterest(args.query, scroll_count=args.scroll, pin_limit=args.limit)
            
           
            timestamp = int(time.time())
            raw_filename = f"data/raw/pinterest_search_{timestamp}.json"
            file_handler.save_json(pins, raw_filename)
            
             
            for pin in pins:
                hash_record = hash_generator.create_pin_hash_record(pin)
                if hash_record:
                    hash_records.append(hash_record)
            
           
            hash_filename = f"data/hashes/pinterest_search_hashes_{timestamp}.json"
            file_handler.save_json(hash_records, hash_filename)
            
            logger.info(f"Scraped and hashed {len(pins)} pins from search: {args.query}")
            scraped_data = pins
            
        elif args.board:
          
            logger.info(f"Scraping board: {args.board}")
            board_data = pinterest_scraper.scrape_board(args.board, scroll_count=args.scroll, pin_limit=args.limit)
            
            
            timestamp = int(time.time())
            raw_filename = f"data/raw/pinterest_board_{timestamp}.json"
            file_handler.save_json(board_data, raw_filename)
            
            
            for pin in board_data["pins"]:
                hash_record = hash_generator.create_pin_hash_record(pin)
                if hash_record:
                    hash_records.append(hash_record)
            
           
            hash_filename = f"data/hashes/pinterest_board_hashes_{timestamp}.json"
            file_handler.save_json(hash_records, hash_filename)
            
            logger.info(f"Scraped and hashed {len(board_data['pins'])} pins from board: {board_data['board_title']}")
            scraped_data = board_data
            
        elif args.pin:
           
            logger.info(f"Scraping pin: {args.pin}")
            pin_data = pinterest_scraper.scrape_pin_details(args.pin)
            
            if pin_data:
               
                timestamp = int(time.time())
                raw_filename = f"data/raw/pinterest_pin_{timestamp}.json"
                file_handler.save_json(pin_data, raw_filename)
                
               
                hash_record = hash_generator.create_pin_hash_record(pin_data)
                if hash_record:
                    hash_records.append(hash_record)
                    
                   
                    hash_filename = f"data/hashes/pinterest_pin_hash_{timestamp}.json"
                    file_handler.save_json(hash_record, hash_filename)
                
                logger.info(f"Scraped and hashed pin: {pin_data['pin_id']}")
                scraped_data = pin_data
                
            else:
                logger.error(f"Failed to scrape pin: {args.pin}")
        
        else:
            logger.error("No action specified. Use --query, --board, or --pin arguments.")
        
        
        results = {
            "timestamp": int(time.time()),
            "type": "search" if args.query else "board" if args.board else "pin" if args.pin else "unknown",
            "query": args.query if args.query else None,
            "board_url": args.board if args.board else None,
            "pin_url": args.pin if args.pin else None,
            "item_count": len(hash_records),
            "hash_records": [hr["combined_hash"] for hr in hash_records]
        }
        
        file_handler.save_json(results, f"data/processed/pinterest_results_{int(time.time())}.json")
        logger.info(f"Process complete. Generated {len(hash_records)} hash records.")
        
    finally:
        
        driver_manager.close_driver()

if __name__ == "__main__":
    main()