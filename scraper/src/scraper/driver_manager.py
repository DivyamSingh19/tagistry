import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager


class DriverManager:
    """
    Manages Selenium WebDriver instances with various configuration options.
    Supports Chrome and Firefox browsers with customization options.
    """
    
    def __init__(self, browser_type="chrome", headless=True, user_agent=None, 
                 proxy=None, download_dir=None, window_size=(1920, 1080),
                 disable_images=False, incognito=False, logger=None):
        """
        Initialize the driver manager with configuration options.
        
        Args:
            browser_type (str): Browser to use ('chrome' or 'firefox')
            headless (bool): Run browser in headless mode if True
            user_agent (str): Custom user agent string
            proxy (str): Proxy server address (e.g., "socks5://127.0.0.1:9050")
            download_dir (str): Directory to save downloaded files
            window_size (tuple): Browser window dimensions as (width, height)
            disable_images (bool): Disable image loading if True
            incognito (bool): Use incognito/private browsing mode if True
            logger: Logger instance for logging events
        """
        self.browser_type = browser_type.lower()
        self.headless = headless
        self.user_agent = user_agent
        self.proxy = proxy
        self.download_dir = download_dir or os.path.join(os.getcwd(), "downloads")
        self.window_size = window_size
        self.disable_images = disable_images
        self.incognito = incognito
        self.logger = logger
        self.driver = None
        
        # Create download directory if it doesn't exist
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir, exist_ok=True)
    
    def initialize_driver(self):
        """
        Initialize and configure the WebDriver based on the specified options.
        
        Returns:
            WebDriver: Configured Selenium WebDriver instance
        """
        if self.logger:
            self.logger.info(f"Initializing {self.browser_type} WebDriver")
            
        if self.browser_type == "chrome":
            self.driver = self._setup_chrome_driver()
        elif self.browser_type == "firefox":
            self.driver = self._setup_firefox_driver()
        else:
            error_msg = f"Unsupported browser type: {self.browser_type}"
            if self.logger:
                self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        # Configure window size
        if self.window_size:
            self.driver.set_window_size(self.window_size[0], self.window_size[1])
            
        # Set reasonable page load timeout
        self.driver.set_page_load_timeout(30)
        self.driver.set_script_timeout(30)
        
        if self.logger:
            self.logger.info("WebDriver initialized successfully")
            
        return self.driver
        
    def _setup_chrome_driver(self):
        """
        Set up and configure Chrome WebDriver.
        
        Returns:
            WebDriver: Configured Chrome WebDriver instance
        """
        chrome_options = Options()
        
        # Headless mode
        if self.headless:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            
        # Basic options for stability
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-extensions")
            
        # Proxy configuration
        if self.proxy:
            chrome_options.add_argument(f"--proxy-server={self.proxy}")
            
        # User agent configuration
        if self.user_agent:
            chrome_options.add_argument(f"--user-agent={self.user_agent}")
            
        # Incognito mode
        if self.incognito:
            chrome_options.add_argument("--incognito")
            
        # Download directory configuration
        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": False
        }
        
        # Disable images for faster loading
        if self.disable_images:
            prefs["profile.managed_default_content_settings.images"] = 2
            
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Initialize and return Chrome driver
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)
        
    def _setup_firefox_driver(self):
        """
        Set up and configure Firefox WebDriver.
        
        Returns:
            WebDriver: Configured Firefox WebDriver instance
        """
        firefox_options = webdriver.FirefoxOptions()
        
        # Headless mode
        if self.headless:
            firefox_options.add_argument("--headless")
            
        # User agent configuration
        if self.user_agent:
            firefox_options.set_preference("general.useragent.override", self.user_agent)
            
        # Download directory configuration
        firefox_options.set_preference("browser.download.folderList", 2)
        firefox_options.set_preference("browser.download.dir", self.download_dir)
        firefox_options.set_preference("browser.download.useDownloadDir", True)
        firefox_options.set_preference("browser.helperApps.neverAsk.saveToDisk", 
                                     "application/pdf,application/x-pdf,application/octet-stream")
        
        # Proxy configuration
        if self.proxy:
            proxy_parts = self.proxy.split("://")
            if len(proxy_parts) == 2:
                proxy_type, proxy_address = proxy_parts
                proxy_host, proxy_port = proxy_address.split(":")
                
                firefox_options.set_preference("network.proxy.type", 1)
                
                if proxy_type == "http":
                    firefox_options.set_preference("network.proxy.http", proxy_host)
                    firefox_options.set_preference("network.proxy.http_port", int(proxy_port))
                elif proxy_type == "socks5":
                    firefox_options.set_preference("network.proxy.socks", proxy_host)
                    firefox_options.set_preference("network.proxy.socks_port", int(proxy_port))
                    firefox_options.set_preference("network.proxy.socks_version", 5)
        
        # Disable images for faster loading
        if self.disable_images:
            firefox_options.set_preference("permissions.default.image", 2)
            
        # Private browsing mode
        if self.incognito:
            firefox_options.set_preference("browser.privatebrowsing.autostart", True)
            
        # Initialize and return Firefox driver
        service = Service(GeckoDriverManager().install())
        return webdriver.Firefox(service=service, options=firefox_options)
        
    def close_driver(self):
        """
        Safely close the WebDriver instance.
        """
        if self.driver:
            if self.logger:
                self.logger.info("Closing WebDriver")
            try:
                self.driver.quit()
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error closing WebDriver: {str(e)}")
            finally:
                self.driver = None
                
    def __enter__(self):
        """
        Context manager entry point.
        
        Returns:
            WebDriver: Initialized WebDriver instance
        """
        return self.initialize_driver()
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit point.
        """
        self.close_driver()
        
    def refresh_driver(self):
        """
        Refresh the WebDriver by closing and reinitializing it.
        Useful for solving memory leaks during long scraping sessions.
        
        Returns:
            WebDriver: Fresh WebDriver instance
        """
        if self.logger:
            self.logger.info("Refreshing WebDriver")
        self.close_driver()
        time.sleep(1)  # Short pause to ensure clean shutdown
        return self.initialize_driver()