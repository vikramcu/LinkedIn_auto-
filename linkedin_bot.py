import time
import urllib.parse
import re
from playwright.sync_api import sync_playwright

class LinkedInBot:
    def __init__(self, linkedin_config, tracker, cv_manager):
        self.email = linkedin_config.get("email")
        self.password = linkedin_config.get("password")
        self.session_cookie = linkedin_config.get("session_cookie")
        self.tracker = tracker
        self.cv_manager = cv_manager

    def run_bot(self, search_config):
        keywords = search_config.get("keywords", ["Java"])
        location = search_config.get("location", "Remote")
        daily_limit = search_config.get("daily_application_limit", 50)

        with sync_playwright() as p:
            # Connect in non-headless mode so it looks more human to LinkedIn
            # and so user can see it running
            browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 800}
            )
            
            # Use Session Cookie if available to bypass strict login (CAPTCHAs)
            if self.session_cookie and self.session_cookie != "OPTIONAL_BUT_RECOMMENDED_LI_AT_COOKIE":
                context.add_cookies([{
                    "name": "li_at",
                    "value": self.session_cookie,
                    "domain": ".www.linkedin.com",
                    "path": "/",
                    "secure": True,
                    "sameSite": "None"
                }])
            
            page = context.new_page()
            
            # Automatically accept any JS dialogs (like "You have unsaved changes. Leave site?")
            # Otherwise Playwright's default behavior is to 'dismiss' (Cancel) them, which blocks navigation!
            page.on("dialog", lambda dialog: dialog.accept())
            
            # Add anti-bot script
            if not self._login(page):
                print("Failed to login. Please provide a valid session cookie or attempt manual login.")
                browser.close()
                return

            print(f"Logged in successfully. Searching for jobs: {keywords} in {location}")
            
            applied_count = 0
            for keyword in keywords:
                if applied_count >= daily_limit:
                    break
                
                applied_count += self.search_and_apply_jobs(page, keyword, location, daily_limit - applied_count)
            
            print(f"Finished job sequence. Applied to {applied_count} jobs today.")
            browser.close()

    def _login(self, page):
        try:
            page.goto("https://www.linkedin.com/feed/", wait_until="commit", timeout=60000)
            time.sleep(3)
        except Exception as e:
            print(f"Warning on initial navigation: {e}")
            
        # Check if already logged in via cookie
        if page.locator("input[placeholder='Search']").count() > 0 or page.url.startswith("https://www.linkedin.com/feed/"):
            return True
            
        print("Not logged in. Attempting manual login using credentials...")
        try:
            page.goto("https://www.linkedin.com/login", wait_until="commit", timeout=60000)
            time.sleep(2)
        except Exception as e:
            print(f"Warning on login navigation: {e}")
        
        try:
            page.fill("input#username", self.email)
            page.fill("input#password", self.password)
            page.click("button[type='submit']")
            page.wait_for_url("https://www.linkedin.com/feed/", timeout=60000)
            return True
        except Exception as e:
            print("Login failed. LinkedIn might be asking for a CAPTCHA or 2FA.")
            # We wait 30 seconds for the user to manually solve the CAPTCHA if they are watching
            page.wait_for_timeout(30000)
            if page.url.startswith("https://www.linkedin.com/feed/"):
                return True
            print(f"Error details: {e}")
            return False

    def search_and_apply_jobs(self, page, keyword, location, limit):
        keyword_encoded = urllib.parse.quote(keyword)
        location_encoded = urllib.parse.quote(location)
        url = f"https://www.linkedin.com/jobs/search/?keywords={keyword_encoded}&location={location_encoded}&f_AL=true"
        
        try:
            # First attempt direct navigation
            page.goto(url, wait_until="commit", timeout=60000)
            page.wait_for_selector(".job-card-container, .scaffold-layout__list-container, .jobs-search-results-list", timeout=30000)
        except Exception as e:
            print(f"Direct navigation failed, attempting human-like UI search... {e}")
            try:
                # Go to feed
                page.goto("https://www.linkedin.com/feed/", wait_until="commit", timeout=30000)
                time.sleep(3)
                # Click Jobs icon
                page.click("a[href*='/jobs']", timeout=15000)
                time.sleep(5)
                # Type in search bar
                search_input = page.locator("input.jobs-search-box__text-input[aria-label='Search by title, skill, or company']").first
                if search_input.count() == 0:
                    search_input = page.locator("input.jobs-search-box__text-input").first
                
                search_input.fill(keyword)
                search_input.press("Enter")
                
                # Turn on Easy Apply filter if possible
                time.sleep(5)
                easy_apply_filter = page.locator("button:has-text('Easy Apply')").first
                if easy_apply_filter.is_visible():
                    easy_apply_filter.click()
                
                page.wait_for_selector(".scaffold-layout__list-container, .job-card-container", timeout=30000)
            except Exception as human_err:
                print(f"Human-like UI search also failed: {human_err}")
                try:
                    page.screenshot(path=f"search_error_{keyword}.png")
                except Exception:
                    pass
                return 0
        
        time.sleep(3) # Wait for listings to load properly
        
        applied_today = 0
        
        # We scroll down the jobs list to load all cards
        jobs_list_selector = ".scaffold-layout__list-container"
        if page.locator(jobs_list_selector).count() > 0:
            page.locator(jobs_list_selector).evaluate("element => element.scrollTo(0, element.scrollHeight)")
            time.sleep(2)
        
        job_cards = page.locator(".job-card-container").all()
        print(f"Found {len(job_cards)} Easy Apply jobs for {keyword} on this page.")
        
        for idx in range(len(job_cards)):
            if applied_today >= limit:
                break
                
            try:
                card = page.locator(".job-card-container").nth(idx)
                card.scroll_into_view_if_needed()
                card.click()
                time.sleep(2)  # Wait for job description pane to load
                
                # Check if already applied
                already_applied = page.locator(".artdeco-inline-feedback--success").count() > 0
                if already_applied:
                    print("Skipping - Already applied in the past.")
                    continue
                
                # More resilient locators for job title and company
                job_title_locator = page.locator(".job-details-jobs-unified-top-card__job-title-link, .job-details-jobs-unified-top-card__job-title h1")
                company_locator = page.locator(".job-details-jobs-unified-top-card__company-name, .job-details-jobs-unified-top-card__primary-description span:first-child")
                
                # Fetch details safely
                job_title = job_title_locator.first.inner_text().strip() if job_title_locator.count() > 0 else "Unknown Title"
                company_name = company_locator.first.inner_text().strip() if company_locator.count() > 0 else "Unknown Company"
                job_link = page.url
                
                # Extract Description
                jd_locator = page.locator("article.jobs-description__container")
                jd_text = jd_locator.inner_text() if jd_locator.count() > 0 else "No description"
                
                print(f"Applying to: {job_title} at {company_name}")
                
                # Tailor the CV
                tailored_text = self.cv_manager.tailor_cv_for_job(jd_text)
                pdf_path = "Tailored_CV.pdf"
                self.cv_manager.generate_pdf(tailored_text, pdf_path)
                
                # Click Easy Apply button
                apply_button = page.get_by_role("button", name="Easy Apply", exact=False).first
                if apply_button.count() == 0:
                    apply_button = page.locator("button:has-text('Easy Apply')").first
                
                # Wait for the button to be visible and clickable
                try:
                    apply_button.wait_for(state="visible", timeout=3000)
                except Exception:
                    print(f"Easy apply button missing or not visible for {company_name}")
                    self.tracker.log_application(company_name, job_title, job_link, "Skipped - No Button")
                    continue
                    
                # Force click in case of overlay
                apply_button.click(force=True)
                time.sleep(2)
                
                # Easy Apply Modal sequence
                status = self._handle_easy_apply_modal(page, pdf_path)
                
                self.tracker.log_application(company_name, job_title, job_link, status)
                
                if status == "Applied":
                    applied_today += 1
                
                time.sleep(3) # Human delay
                
            except Exception as e:
                print(f"Failed to process job card: {e}")
                
        print(f"Completed search for {keyword} in {location}")
        return applied_today

    def _handle_easy_apply_modal(self, page, pdf_path):
        """Attempts to navigate through the easy apply modal automatically."""
        try:
            max_steps = 7
            for step in range(max_steps):
                time.sleep(1)
                
                # Handle File Upload if visible
                upload_input = page.locator("input[type='file']")
                if upload_input.count() > 0 and upload_input.is_visible():
                    import os
                    abs_path = os.path.abspath(pdf_path)
                    upload_input.set_input_files(abs_path)
                    time.sleep(1)

                # Fill common questions
                self._fill_common_questions(page)

                # Look for buttons
                submit_btn = page.locator("button[aria-label='Submit application']")
                review_btn = page.locator("button[aria-label='Review your application']")
                next_btn = page.locator("button[aria-label='Continue to next step']")
                
                if submit_btn.count() > 0 and submit_btn.is_visible():
                    submit_btn.click()
                    time.sleep(2)
                    self._close_modal(page)
                    return "Applied"
                    
                elif review_btn.count() > 0 and review_btn.is_visible():
                    review_btn.click()
                    
                elif next_btn.count() > 0 and next_btn.is_visible():
                    # Check for mandatory empty fields that might block 'Next'
                    error_msg = page.locator(".artdeco-inline-feedback--error")
                    if error_msg.count() > 0 and error_msg.is_visible():
                        print("Modal blocked by mandatory custom questions.")
                        self._close_modal(page)
                        return "Failed - Custom Questionnaire"
                    next_btn.click()
                else:
                    print("Could not find next/submit button. Quitting this application.")
                    self._close_modal(page)
                    return "Failed - Unknown Modal State"
            
            # If we reach here, max steps exceeded
            self._close_modal(page)
            return "Failed - Too Many Steps"
            
        except Exception as e:
            print(f"Modal error: {e}")
            self._close_modal(page)
            return "Failed - Exception"

    def _fill_common_questions(self, page):
        """Attempts to answer common questions like experience and salary."""
        try:
            # Find all single line text inputs
            inputs = page.locator("input[type='text'], input[type='number']").all()
            for input_field in inputs:
                if not input_field.is_visible():
                    continue
                
                # Skip if already filled
                if input_field.input_value().strip() != "":
                    continue

                # Get the label text to understand the question
                label_id = input_field.get_attribute("id")
                label_text = ""
                if label_id:
                    label_el = page.locator(f"label[for='{label_id}']")
                    if label_el.count() > 0:
                        label_text = label_el.first.inner_text().lower()
                
                if not label_text:
                    label_text = (input_field.get_attribute("aria-label") or "").lower()

                if not label_text:
                    continue

                # Apply user-defined rules
                if "experience" in label_text and "months" in label_text:
                    input_field.fill("0")
                elif "experience" in label_text:
                    input_field.fill("2")
                elif "expected" in label_text and ("salary" in label_text or "ctc" in label_text or "compensation" in label_text):
                    input_field.fill("500000")
                elif "ctc" in label_text or "current salary" in label_text or "annual" in label_text:
                    input_field.fill("350000")
                elif "notice" in label_text or "join" in label_text:
                    input_field.fill("0")

            # Handle radio button questions (e.g. Yes/No) and select "Yes"
            fieldsets = page.locator("fieldset").all()
            for fieldset in fieldsets:
                if not fieldset.is_visible():
                    continue
                
                # Check if an option is already selected
                if fieldset.locator("input[type='radio']:checked").count() > 0:
                    continue
                
                # Look for a 'Yes' option and click it
                yes_option = fieldset.locator("label", has_text=re.compile(r'(?i)^\s*Yes\s*$')).first
                if yes_option.count() == 0:
                    yes_option = fieldset.locator("label:has-text('Yes'), label:has-text('yes')").first

                if yes_option.count() > 0:
                    try:
                        yes_option.click(force=True)
                        time.sleep(0.5)
                    except Exception:
                        pass

            # Handle select dropdowns
            selects = page.locator("select").all()
            for select in selects:
                if not select.is_visible():
                    continue
                
                # Try to select the 'Yes' option if available
                options = select.locator("option").all()
                for opt in options:
                    if opt.inner_text().strip().lower() == "yes":
                        try:
                            select.select_option(value=opt.get_attribute("value"))
                            time.sleep(0.5)
                        except Exception:
                            pass
                        break

        except Exception as e:
            print(f"Error filling questions: {e}")

    def _close_modal(self, page):
        """Closes the Easy Apply modal aggressively."""
        try:
            # Try pressing Escape a few times to close any dialogs
            for _ in range(3):
                page.keyboard.press("Escape")
                time.sleep(0.5)
            
            # If the modal is still open, try to click the dismiss button
            dismiss_locator = page.locator("button[aria-label='Dismiss']").first
            if dismiss_locator.count() > 0 and dismiss_locator.is_visible():
                dismiss_locator.click(force=True)
                time.sleep(1)
            
            # Handle the discard confirmation
            discard_locator = page.locator("button[data-control-name='discard_application_confirm_btn']").first
            if discard_locator.count() > 0 and discard_locator.is_visible():
                discard_locator.click(force=True)
                time.sleep(1)
        except Exception as e:
            print(f"Error during aggressive modal close: {e}")
