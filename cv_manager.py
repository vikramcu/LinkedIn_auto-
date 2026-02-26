import pdfplumber
import google.generativeai as genai
from fpdf import FPDF
import os

class CVManager:
    def __init__(self, api_key, base_pdf_path):
        self.api_key = api_key
        self.base_pdf_path = base_pdf_path
        
        # Configure Gemini API
        if self.api_key and self.api_key != "YOUR_GEMINI_API_KEY":
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None

    def parse_base_cv(self):
        """Extracts text from the base PDF."""
        text = ""
        try:
            with pdfplumber.open(self.base_pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error reading PDF: {e}")
        return text

    def tailor_cv_for_job(self, job_description):
        """Uses Gemini API to rewrite sections of the CV to match the job."""
        if not self.model:
            print("Gemini API key not configured. Using base CV text.")
            return self.parse_base_cv()

        base_cv_text = self.parse_base_cv()
        
        prompt = f"""
        You are an expert technical recruiter and resume writer. 
        I am applying for a job with the following description:
        
        {job_description}
        
        Here is my current resume:
        
        {base_cv_text}
        
        Please rewrite my resume to highlight my skills ({', '.join(job_description.split()[:5])}...) that match the job description.
        You must explicitly state and frame my experience as having exactly 2 years of professional experience with Java, Spring, SQL, React, AWS, Docker, REST APIs, Microservices, and the relevant technologies mentioned in the job description.
        Do not lie about the companies I worked for, but do frame my duration and projects to reflect 2 years of solid hands-on experience in these tech stacks.
        Output ONLY the beautifully formatted text of the tailored resume, ready to be printed to a PDF.
        Do not use markdown formatting like ``` or ** as it will not parse into the PDF correctly.
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return base_cv_text

    def generate_pdf(self, customized_content, output_path="Tailored_CV.pdf"):
        """Generates a simple PDF from the customized text."""
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=11)
            
            # encode to latin-1 and ignore characters that cannot be encoded
            # FPDF standard font doesn't handle full utf-8 out of the box
            encoded_text = customized_content.encode('latin-1', 'replace').decode('latin-1')
            
            pdf.multi_cell(0, 5, encoded_text)
            pdf.output(output_path)
            return True
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return False
