import browser_cookie3

def get_linkedin_cookie():
    print("Attempting to extract LinkedIn cookie from your local Chrome/Edge browsers...")
    try:
        # Load cookies from all supported browsers
        cookies = browser_cookie3.load(domain_name='.linkedin.com')
        for cookie in cookies:
            if cookie.name == 'li_at':
                print("\nSUCCESS! Found your LinkedIn session cookie:\n")
                print(cookie.value)
                print("\nCopy the text above and paste it into your config.json under 'session_cookie'!")
                return cookie.value
        
        print("\nCould not find the 'li_at' cookie. Please make sure you are logged into LinkedIn on Chrome or Edge.")
    except Exception as e:
        print(f"\nError extracting cookies: {e}")
        print("You might need to close your browser once or ensure your Python has permissions to read browser data.")

if __name__ == "__main__":
    get_linkedin_cookie()
