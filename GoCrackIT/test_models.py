import google.generativeai as genai

# Configure Gemini API
GEMINI_API_KEY = 'AIzaSyAxE6sAGsOLr3iBMMwFH9BdUGDADqeLWAE'
genai.configure(api_key=GEMINI_API_KEY)

print("Testing Gemini API...")

try:
    # List available models
    models = list(genai.list_models())
    print(f"Found {len(models)} models:")
    
    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            print(f"- {model.name}")
    
    # Test with a known working model
    print("\nTesting with gemini-1.5-flash...")
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Hello, this is a test.")
    print(f"Response: {response.text}")
    
    print("\nTesting with gemini-1.5-pro...")
    model = genai.GenerativeModel('gemini-1.5-pro')
    response = model.generate_content("Hello, this is a test.")
    print(f"Response: {response.text}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc() 