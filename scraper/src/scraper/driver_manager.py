from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class DriverManager:
    
    
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
    
    def initialize_driver(self):
         
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Additional options for better performance
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        # Set reasonable page load timeout
        self.driver.set_page_load_timeout(30)
        return self.driver
    
    def close_driver(self):
         
        if self.driver:
            self.driver.quit()
            self.driver = None