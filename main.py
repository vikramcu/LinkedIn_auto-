import json
from linkedin_bot import LinkedInBot
from cv_manager import CVManager
from tracker import TrackingManager

def load_config(config_path="config.json"):
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("config.json not found! Please copy config.template.json to config.json and fill it out.")
        exit(1)

def main():
    print("Starting LinkedIn Automation Bot...")
    config = load_config()
    
    # Initialize Modules
    tracker = TrackingManager("applications.xlsx")
    cv_manager = CVManager(config['gemini']['api_key'], config['resume']['base_pdf_path'])
    bot = LinkedInBot(config['linkedin'], tracker, cv_manager)

    print("Running sequence...")
    bot.run_bot(config['search'])

    print("Sequence completed. Check applications.xlsx for tracking.")

if __name__ == "__main__":
    main()
