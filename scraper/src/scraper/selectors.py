class PinterestSelectors:
    """CSS and XPath selectors for Pinterest"""
    
    # Main Pinterest selectors
    PINS = {
        "pin_container": "div[data-test-id='pin']",
        "pin_image": "img[loading='auto'], img[loading='eager']",
        "pin_description": "div[data-test-id='pinDescription']",
        "pin_title": "div[data-test-id='pinTitle']",
        "pin_link": "a[data-test-id='pin']",
        "pin_creator": "a[data-test-id='userName']",
        "full_resolution_img": "div[role='button'] img"
    }
    
    # Board selectors
    BOARDS = {
        "board_container": "div[data-test-id='boardFeed']",
        "board_title": "div[data-test-id='boardTitle']",
        "board_pins": "div[data-test-id='gridCentered'] div[data-test-id='pin']"
    }
    
    # Search results selectors
    SEARCH = {
        "search_input": "input[data-test-id='search-box-input']",
        "search_button": "button[data-test-id='searchbarSubmitButton']",
        "search_results": "div[data-test-id='search-pins-feed'] div[data-test-id='gridCentered']"
    }
    
    # Navigation and UI elements
    NAVIGATION = {
        "login_button": "button[data-test-id='loginButton']",
        "email_field": "input[id='email']",
        "password_field": "input[id='password']",
        "submit_login": "button[data-test-id='registerFormSubmitButton']",
        "close_modal": "div[data-test-id='closeup-close-button']",
        "scroll_container": "div[data-test-id='gridCentered']"
    }
    
   
    XPATH = {
        "pin_image_by_id": lambda pin_id: f"//div[@data-test-id='pin'][@data-pin-id='{pin_id}']//img",
        "pin_by_id": lambda pin_id: f"//div[@data-test-id='pin'][@data-pin-id='{pin_id}']",
        "board_by_name": lambda board_name: f"//div[contains(@class, 'boardContainer')]//div[text()='{board_name}']",
        "has_more_items": "//div[contains(@class, 'gridFooter')]"
    }