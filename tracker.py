import os
from datetime import datetime
from openpyxl import Workbook, load_workbook
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

class TrackingManager:
    def __init__(self, excel_path="applications.xlsx", firebase_cert_path="firebase_credentials.json"):
        self.excel_path = excel_path
        self._initialize_tracker()
        self.db = self._initialize_firebase(firebase_cert_path)

    def _initialize_tracker(self):
        if not os.path.exists(self.excel_path):
            wb = Workbook()
            ws = wb.active
            ws.title = "Applications"
            # Define Headers
            ws.append(["Date", "Company", "Job Title", "Link", "Status"])
            wb.save(self.excel_path)

    def _initialize_firebase(self, cert_path):
        if not os.path.exists(cert_path):
            print(f"Firebase credentials not found at {cert_path}. Live dashboard updates disabled.")
            return None
            
        try:
            # Check if already initialized (prevents error if script is run multiple times)
            if not firebase_admin._apps:
                cred = credentials.Certificate(cert_path)
                firebase_admin.initialize_app(cred)
            return firestore.client()
        except Exception as e:
            print(f"Error initializing Firebase: {e}")
            return None

    def log_application(self, company, job_title, link, status):
        # 1. Log to Excel
        try:
            wb = load_workbook(self.excel_path)
            ws = wb.active
            
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ws.append([date_str, company, job_title, link, status])
            
            wb.save(self.excel_path)
        except Exception as e:
            print(f"Failed to log to Excel: {e}")
            
        # 2. Log to Firebase Firestore
        if self.db:
            try:
                # Store it with a composite ID so we don't accidentally write duplicates
                # if the user runs the script multiple times on the same job
                doc_id = f"{company}_{job_title}".replace(" ", "_").replace("/", "-")
                
                self.db.collection('applications').document(doc_id).set({
                    'timestamp': firebase_admin.firestore.SERVER_TIMESTAMP,
                    'date_str': date_str,
                    'company': company,
                    'job_title': job_title,
                    'link': link,
                    'status': status
                }, merge=True)
                print(f"🔥 Live Dashboard Updated: [{status}] {company}")
            except Exception as e:
                print(f"Failed to log to Firebase: {e}")
