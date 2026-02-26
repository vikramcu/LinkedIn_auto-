from tracker import TrackingManager

# Initialize the tracker
tracker = TrackingManager("test_applications.xlsx")

# Log a test application
tracker.log_application("Google", "Software Engineer", "https://linkedin.com/jobs/google", "Applied")
tracker.log_application("Microsoft", "Backend Engineer", "https://linkedin.com/jobs/microsoft", "Skipped")

print("Created test_applications.xlsx and logged test entries successfully.")
