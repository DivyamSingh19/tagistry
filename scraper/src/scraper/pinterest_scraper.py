import time
import json
import os
import requests
from urllib.parse import urlparse, urljoin
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .selectors import PinterestSelectors

class PinterestScraper:
    """Specialized scraper for Pinterest content"""
    
    def __init__(self, driver, logger, download_images=True, download_path="data/raw/images"):
        self.driver = driver
        self.logger = logger
        self.selectors = PinterestSelectors()
        self.download_images = download_images
        self.download_path = download_path
        
        # Create download directory if needed
        if download_images and not os.path.exists(download_path):
            os.makedirs(download_path, exist_ok=True)
    
    def navigate_to_url(self, url):
        """Navigate to a Pinterest URL"""
        try:
            self.logger.info(f"Navigating to {url}")
            self.driver.get(url)
            time.sleep(3)  # Allow initial page load
            return True
        except Exception as e:
            self.logger.error(f"Failed to navigate to {url}: {e}")
            return False
    
    def login(self, email, password):
        """Log into Pinterest"""
        try:
            self.logger.info("Attempting Pinterest login")
            
            # Navigate to Pinterest login page
            self.driver.get("https://www.pinterest.com/login/")
            time.sleep(2)
            
            # Enter email
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            email_field.clear()
            email_field.send_keys(email)
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(password)
            
            # Submit form
            password_field.send_keys(Keys.RETURN)
            
            # Wait for login to complete
            time.sleep(5)
            
            # Check if login was successful
            if "pinterest.com/login" in self.driver.current_url:
                self.logger.error("Login failed")
                return False
            else:
                self.logger.info("Login successful")
                return True
                
        except Exception as e:
            self.logger.error(f"Login error: {e}")
            return False
    
    def scroll_to_load_more(self, scroll_count=5, scroll_pause=2.0):
        """Scroll down the page to trigger Pinterest's infinite scrolling"""
        self.logger.info(f"Scrolling page to load more content (count: {scroll_count})")
        
        try:
            # Get scroll height
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            for i in range(scroll_count):
                # Scroll down to bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Wait to load more content
                time.sleep(scroll_pause)
                
                # Calculate new scroll height and compare with last scroll height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                if new_height == last_height:
                    self.logger.info("Reached end of page or no more content loading")
                    break
                    
                last_height = new_height
                self.logger.debug(f"Scroll {i+1}/{scroll_count} completed")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error during page scrolling: {e}")
            return False
    
    def extract_pins_from_page(self, limit=None):
        """Extract pins from the current page"""
        self.logger.info("Extracting pins from page")
        
        pins_data = []
        try:
            pin_elements = self.driver.find_elements(By.CSS_SELECTOR, self.selectors.PINS["pin_container"])
            self.logger.info(f"Found {len(pin_elements)} pins on the page")
            
            # Apply limit if specified
            if limit and limit < len(pin_elements):
                pin_elements = pin_elements[:limit]
                
            for i, pin_element in enumerate(pin_elements):
                try:
                    # Extract pin data
                    pin_id = pin_element.get_attribute("data-pin-id") or f"unknown_{i}"
                    
                    # Find image inside the pin
                    try:
                        img_element = pin_element.find_element(By.CSS_SELECTOR, self.selectors.PINS["pin_image"])
                        img_url = img_element.get_attribute("src")
                        img_alt = img_element.get_attribute("alt") or ""
                    except NoSuchElementException:
                        img_url = None
                        img_alt = ""
                    
                    # Find pin link
                    try:
                        link_element = pin_element.find_element(By.CSS_SELECTOR, "a")
                        pin_url = link_element.get_attribute("href")
                    except NoSuchElementException:
                        pin_url = None
                    
                    # Build pin data structure
                    pin_data = {
                        "pin_id": pin_id,
                        "image_url": img_url,
                        "alt_text": img_alt,
                        "pin_url": pin_url,
                        "local_path": None  # Will be populated if download is successful
                    }
                    
                    # Download the image if required
                    if self.download_images and img_url:
                        local_path = self._download_image(img_url, f"pin_{pin_id}")
                        pin_data["local_path"] = local_path
                    
                    pins_data.append(pin_data)
                    
                except Exception as e:
                    self.logger.warning(f"Error extracting data for pin {i}: {e}")
            
            return pins_data
            
        except Exception as e:
            self.logger.error(f"Error extracting pins: {e}")
            return pins_data
    
    def scrape_pin_details(self, pin_url):
        """Scrape detailed information about a specific pin"""
        self.logger.info(f"Scraping details for pin: {pin_url}")
        
        if not self.navigate_to_url(pin_url):
            return None
            
        try:
            # Wait for pin details to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors.PINS["full_resolution_img"]))
            )
            
            # Extract pin information
            pin_data = {}
            
            # Get pin ID from URL
            pin_id = urlparse(pin_url).path.split("/")[-2]
            pin_data["pin_id"] = pin_id
            
            # Get high-resolution image
            img_element = self.driver.find_element(By.CSS_SELECTOR, self.selectors.PINS["full_resolution_img"])
            pin_data["image_url"] = img_element.get_attribute("src")
            pin_data["alt_text"] = img_element.get_attribute("alt") or ""
            
            # Get pin description
            try:
                desc_element = self.driver.find_element(By.CSS_SELECTOR, self.selectors.PINS["pin_description"])
                pin_data["description"] = desc_element.text
            except NoSuchElementException:
                pin_data["description"] = ""
            
            # Get pin title
            try:
                title_element = self.driver.find_element(By.CSS_SELECTOR, self.selectors.PINS["pin_title"])
                pin_data["title"] = title_element.text
            except NoSuchElementException:
                pin_data["title"] = ""
            
            # Get pin creator
            try:
                creator_element = self.driver.find_element(By.CSS_SELECTOR, self.selectors.PINS["pin_creator"])
                pin_data["creator"] = creator_element.text
                pin_data["creator_url"] = creator_element.get_attribute("href")
            except NoSuchElementException:
                pin_data["creator"] = ""
                pin_data["creator_url"] = ""
            
            # Download the image if required
            if self.download_images and pin_data["image_url"]:
                local_path = self._download_image(pin_data["image_url"], f"pin_{pin_id}_full")
                pin_data["local_path"] = local_path
            
            return pin_data
            
        except Exception as e:
            self.logger.error(f"Error scraping pin details: {e}")
            return None
    
    def search_pinterest(self, query, scroll_count=3, pin_limit=None):
        """Search Pinterest for the given query and extract pins"""
        search_url = f"https://www.pinterest.com/search/pins/?q={query.replace(' ', '%20')}"
        self.logger.info(f"Searching Pinterest for: {query}")
        
        if not self.navigate_to_url(search_url):
            return []
            
        # Scroll to load more pins
        self.scroll_to_load_more(scroll_count)
        
        # Extract pins from the search results
        pins = self.extract_pins_from_page(limit=pin_limit)
        self.logger.info(f"Found {len(pins)} pins for search query: {query}")
        
        return pins
    
    def scrape_board(self, board_url, scroll_count=3, pin_limit=None):
        """Scrape pins from a Pinterest board"""
        self.logger.info(f"Scraping board: {board_url}")
        
        if not self.navigate_to_url(board_url):
            return {"board_url": board_url, "pins": []}
            
        # Get board title
        try:
            board_title = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors.BOARDS["board_title"]))
            ).text
        except TimeoutException:
            board_title = "Unknown Board"
            
        # Scroll to load more pins
        self.scroll_to_load_more(scroll_count)
        
        # Extract pins from the board
        pins = self.extract_pins_from_page(limit=pin_limit)
        
        board_data = {
            "board_url": board_url,
            "board_title": board_title,
            "pin_count": len(pins),
            "pins": pins
        }
        
        self.logger.info(f"Scraped {len(pins)} pins from board: {board_title}")
        return board_data
    
    def _download_image(self, img_url, filename_prefix):
        """Download an image from the given URL"""
        if not img_url:
            return None
            
        try:
            # Generate a unique filename
            img_ext = self._get_image_extension(img_url)
            filename = f"{filename_prefix}{img_ext}"
            filepath = os.path.join(self.download_path, filename)
            
            # Download the image
            response = requests.get(img_url, stream=True)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                self.logger.debug(f"Downloaded image to {filepath}")
                return filepath
            else:
                self.logger.warning(f"Failed to download image: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error downloading image: {e}")
            return None
    
    def _get_image_extension(self, img_url):
        """Extract the file extension from the image URL"""
        path = urlparse(img_url).path
        ext = os.path.splitext(path)[1]
        
        # Use .jpg as default if no extension found
        if not ext:
            ext = ".jpg"
        
        return ext