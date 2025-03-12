import os
import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class PinterestAuthManager:
     
    
    def __init__(self, driver, logger, credentials_file=None):
        self.driver = driver
        self.logger = logger
        self.credentials_file = credentials_file
        self.is_authenticated = False
    
    def load_credentials(self):
        """Load Pinterest credentials from file"""
        if not self.credentials_file or not os.path.exists(self.credentials_file):
            self.logger.warning(f"Credentials file not found: {self.credentials_file}")
            return None, None
            
        try:
            with open(self.credentials_file, 'r') as f:
                credentials = json.load(f)
                return credentials.get('email'), credentials.get('password')
        except Exception as e:
            self.logger.error(f"Error loading credentials: {e}")
            return None, None
    
    def login(self, email=None, password=None):
         
        if not email or not password:
            email, password = self.load_credentials()
            if not email or not password:
                self.logger.error("No valid credentials provided")
                return False
        
        try:
            self.logger.info("Logging in to Pinterest")
            
            # Navigate to login page
            self.driver.get("https://www.pinterest.com/login/")
            time.sleep(2)  # Allow page to load
            
            # Wait for login form to be visible
            email_field = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "email"))
            )
            
            # Enter email
            email_field.clear()
            email_field.send_keys(email)
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(password)
            
            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            # Wait for login to complete
            time.sleep(5)
            
            # Verify login was successful
            if "pinterest.com/login" in self.driver.current_url:
                self.logger.error("Login failed")
                self.is_authenticated = False
                return False
            
            self.logger.info("Successfully logged in to Pinterest")
            self.is_authenticated = True
            return True
            
        except Exception as e:
            self.logger.error(f"Error during login: {e}")
            self.is_authenticated = False
            return False
    
    def check_login_status(self):
        """Check if currently logged in to Pinterest"""
        try:
            # Navigate to user page
            self.driver.get("https://www.pinterest.com/")
            time.sleep(2)
            
            # Look for login button
            login_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[data-test-id='login-button']")
            
            # If login button is present, we're not logged in
            if login_buttons:
                self.is_authenticated = False
                return False
            
            # Otherwise, assume we're logged in
            self.is_authenticated = True
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking login status: {e}")
            return False
    
    def logout(self):
        """Log out from Pinterest"""
        if not self.is_authenticated:
            return True
            
        try:
            # Navigate to account settings
            self.driver.get("https://www.pinterest.com/settings/")
            time.sleep(2)
            
            # Find and click logout button
            logout_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[text()='Log out']"))
            )
            logout_button.click()
            
            # Wait for logout to complete
            time.sleep(3)
            
            self.is_authenticated = False
            self.logger.info("Successfully logged out from Pinterest")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during logout: {e}")
            return False