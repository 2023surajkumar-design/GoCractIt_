import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import requests
from dotenv import load_dotenv
import io
import tempfile
import google.generativeai as genai
import assemblyai as aai
import asyncio
import json

# Import document parsing libraries
import PyPDF2
import docx
import pandas as pd
import csv
from PIL import Image
import pytesseract

load_dotenv()

# Hardcoded API keys (as requested)
GEMINI_API_KEY = 'AIzaSyAxE6sAGsOLr3iBMMwFH9BdUGDADqeLWAE'
ASSEMBLYAI_API_KEY = '9d58ac0d22104240a53319d522dfba7a'

# Configure Gemini API
os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
genai.configure(api_key=GEMINI_API_KEY)

# Configure AssemblyAI API
aai.settings.api_key = ASSEMBLYAI_API_KEY

app = Flask(__name__)

# Document parsing functions
def extract_text_from_pdf(file_content):
    """Extract text from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            text += pdf_reader.pages[page_num].extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        return f"Error extracting text from PDF: {str(e)}"

def extract_text_from_docx(file_content):
    """Extract text from DOCX file"""
    try:
        # Save the content to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
            temp_file.write(file_content)
            temp_path = temp_file.name
        
        # Open the temporary file with python-docx
        doc = docx.Document(temp_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        
        # Clean up the temporary file
        os.unlink(temp_path)
        return text
    except Exception as e:
        print(f"Error extracting text from DOCX: {str(e)}")
        return f"Error extracting text from DOCX: {str(e)}"

def extract_text_from_csv(file_content):
    """Extract text from CSV file"""
    try:
        # Parse CSV content
        content_str = file_content.decode('utf-8')
        csv_data = []
        csv_reader = csv.reader(content_str.splitlines())
        for row in csv_reader:
            csv_data.append(row)
        
        # Convert to DataFrame for easier handling
        df = pd.DataFrame(csv_data[1:], columns=csv_data[0] if csv_data else None)
        
        # Convert DataFrame to string representation
        return df.to_string(index=False)
    except Exception as e:
        print(f"Error extracting text from CSV: {str(e)}")
        return f"Error extracting text from CSV: {str(e)}"

def extract_text_from_image(file_content):
    """Extract text from image using OCR"""
    try:
        image = Image.open(io.BytesIO(file_content))
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        print(f"Error extracting text from image: {str(e)}")
        return f"Error extracting text from image: {str(e)}"

def extract_text_from_plain_text(file_content):
    """Extract text from plain text file"""
    try:
        return file_content.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error extracting text from plain text: {str(e)}")
        return str(file_content)

# Unified extraction function using Gemini AI
def extract_information_with_gemini(content):
    """Extract information using Gemini AI"""
    try:
        # Truncate content if it's too long (Gemini has input limits)
        if len(content) > 30000:
            content = content[:30000] + "...[content truncated due to length]"
        
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Create a detailed prompt for Gemini to extract specific information
        extraction_prompt = r"""
You are a professional information extraction system. Your task is to extract specific information from the provided document/text and format it EXACTLY as instructed below.

Extract and format ONLY the following information from the provided document/text:

1. Personal Information (in normal text format):
   - Name
   - Phone number
   - Email
   - LinkedIn URL
   - Total years of experience
   - About me / Bio / Summary

   Present this information in the following plain text format: 
   Name: [extracted name]  
   Phone number: [extracted phone number]  
   Email: [extracted email]  
   LinkedIn URL: [extracted LinkedIn URL]  
   Total years of experience: [extracted number or 'Not specified']  
   About me / Bio / Summary: [extracted text or 'Not specified']  
   
For Recognizing Phone number: Validate domestic formats based on expected digit counts and specific prefixes with Country-Specific Rules. Cross-check country codes or leading digits against known prefixes and lengths:
US/Canada (+1): 10 digits.
UK (+44): 10 digits for mobile (starting with 7).
India (+91): 10 digits (starting with 6, 7, 8, or 9).
Thailand (+66): 8 digits (mobile starts with 6, 8, or 9)

  If any field is not found, use 'Not specified'. For 'Total years of experience', use the explicitly stated number if available; otherwise, set it to 'Not specified'.

2. Experience (in JSON format only):
    Extract ALL work experience entries from the document. Look for sections titled 'Experience', 'Work History', 'Professional Experience', or similar. For each entry, include:  
   - Position  
   - Company  
   - Start year  
   - End year (use 'Present' if currently working there)  

   Format this as a JSON array with the following structure:  

   {
     "experience": [
       {
         "position": "Position title",
         "company": "Company name",
         "startYear": "Start year",
         "endYear": "End year or 'Present'"
       },
       // Additional positions...
     ]
   }
 If any field is missing in an entry, set it to 'Not specified'. Return only the JSON structure without additional text.

3. Education (in JSON format only):
  Extract ALL education entries from the document. Look for sections titled 'Education', 'Academic Background', 'Qualifications', or similar. For each entry, include:  
   - Degree  
   - Institute  
   - Start year  
   - End year  

   Format this as a JSON array with the following structure: 

   {
     "education": [
       {
         "degree": "Degree name",
         "institute": "Institution name",
         "startYear": "Start year",
         "endYear": "End year"
       },
       // Additional degrees...
     ]
   }

   If any field is missing in an entry, set it to 'Not specified'. Return only the JSON structure without additional text.

CRITICAL FORMATTING REQUIREMENTS:
- For the personal information section, provide the data in a clear, readable format.
- For experience and education sections, return VALID JSON only.
- List ALL experiences/positions found in the document (not just the most recent ones).
- List ALL education qualifications found in the document (not just the highest degree).
- If information for certain fields is not found, use "Not specified" for text fields and null for numeric fields.
- DO NOT include any explanatory text or notes OUTSIDE the JSON structures for experience and education.
- Ensure the JSON format is correct and can be parsed programmatically.
- If no experience or education is found, return empty arrays: {"experience": []} and {"education": []}

Here's the document to analyze:

"""
        
        # Append content to the prompt
        full_prompt = extraction_prompt + content
        
        # Process with Gemini AI
        response = model.generate_content(full_prompt)
        
        # Add debug logging
        print(f"Gemini Response: {response.text[:500]}...")
        
        return response.text
        
    except Exception as e:
        print(f"Error with Gemini API: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract', methods=['POST'])
def extract():
    try:
        text = request.form.get('text')
        file = request.files.get('file')
        audio = request.files.get('audio')
        content = ""

        # Handle different input types
        if audio:
            # Process audio through AssemblyAI
            audio_content = audio.read()
            print("[DEBUG] Received audio input, size:", len(audio_content))
            
            # Upload audio to AssemblyAI
            upload_url = "https://api.assemblyai.com/v2/upload"
            headers = {"authorization": ASSEMBLYAI_API_KEY}
            upload_response = requests.post(upload_url, headers=headers, data=audio_content)
            if upload_response.status_code != 200:
                print("[ERROR] AssemblyAI upload failed:", upload_response.text)
                return jsonify({'error': 'Audio upload to AssemblyAI failed.'}), 400
            audio_url = upload_response.json()["upload_url"]
            print("[DEBUG] AssemblyAI audio uploaded, url:", audio_url)

            # Request transcription
            transcript_url = "https://api.assemblyai.com/v2/transcript"
            transcript_request = {"audio_url": audio_url, "language_code": "en"}
            transcript_response = requests.post(transcript_url, headers=headers, json=transcript_request)
            if transcript_response.status_code != 200:
                print("[ERROR] AssemblyAI transcript request failed:", transcript_response.text)
                return jsonify({'error': 'Audio transcription request failed.'}), 400
            transcript_id = transcript_response.json()["id"]
            print("[DEBUG] AssemblyAI transcript requested, id:", transcript_id)

            # Poll for completion
            import time
            for _ in range(30):
                poll_response = requests.get(f"https://api.assemblyai.com/v2/transcript/{transcript_id}", headers=headers)
                status = poll_response.json().get('status')
                print(f"[DEBUG] Polling transcript status: {status}")
                if status == 'completed':
                    transcript_text = poll_response.json().get('text')
                    print("[DEBUG] AssemblyAI transcript complete:", transcript_text[:100])
                    content = transcript_text
                    break
                elif status == 'failed':
                    print("[ERROR] AssemblyAI transcript failed:", poll_response.text)
                    return jsonify({'error': 'Audio transcription failed.'}), 400
                time.sleep(2)
            else:
                print("[ERROR] AssemblyAI transcript polling timed out.")
                return jsonify({'error': 'Audio transcription timed out.'}), 400
                
        elif file:
            # Read file content
            file_content = file.read()
            filename = file.filename.lower() if file.filename else ""
            
            # Process based on file type
            if filename.endswith('.txt') or filename.endswith('.md'):
                content = extract_text_from_plain_text(file_content)
            elif filename.endswith('.pdf'):
                content = extract_text_from_pdf(file_content)
            elif filename.endswith('.docx'):
                content = extract_text_from_docx(file_content)
            elif filename.endswith('.csv'):
                content = extract_text_from_csv(file_content)
            elif filename.endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                content = extract_text_from_image(file_content)
            else:
                return jsonify({'error': f'Unsupported file type: {filename.split(".")[-1]}'}), 400
                
        elif text:
            content = text
        else:
            return jsonify({'error': 'No input provided.'}), 400

        if not content or not content.strip():
            return jsonify({'error': 'No text could be extracted from the input.'}), 400

        # Extract information using Gemini AI
        result = extract_information_with_gemini(content)
        if not result:
            return jsonify({'error': 'Gemini extraction failed.'}), 400
            
        return jsonify({'result': result})
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint to verify the server is running"""
    return jsonify({
        "status": "ok", 
        "gemini_api_key_configured": bool(GEMINI_API_KEY),
        "assemblyai_api_key_configured": bool(ASSEMBLYAI_API_KEY)
    })

if __name__ == '__main__':
    print("\n" + "="*50)
    print("GoCrackIT AI Information Extractor is running!")
    print("Open your browser and go to: http://localhost:5000")
    print("="*50 + "\n")
    app.run(debug=True, host='127.0.0.1', port=5000) 