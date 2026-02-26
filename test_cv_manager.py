from cv_manager import CVManager

def test_cv_manager():
    print("Testing CV Manager...")
    
    # Initialize without a real API key to test the fallback logic
    cv_manager = CVManager("YOUR_GEMINI_API_KEY", "VIKRAM-M-FlowCV-Resume-20260223.pdf")
    
    # Test 1: Parsing Base CV
    base_text = cv_manager.parse_base_cv()
    print(f"Base CV Extracted Text (First 100 chars): {base_text[:100]}")
    
    if not base_text:
        print("FAILED to parse CV PDF! Check if the file name is correct.")
        return
        
    # Test 2: Tailoring CV (will fallback to returning base text since no api key)
    tailored_text = cv_manager.tailor_cv_for_job("Looking for a Java Spring Boot developer with SQL experience.")
    
    # Test 3: Generating PDF
    success = cv_manager.generate_pdf(tailored_text, "test_Tailored_CV.pdf")
    if success:
        print("Successfully generated test_Tailored_CV.pdf!")
    else:
        print("FAILED to generate PDF.")

if __name__ == "__main__":
    test_cv_manager()
