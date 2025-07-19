from google import genai
from google.genai import types
import time

def get_key(filename):
    with open(filename, 'r') as file:
        return file.read().strip()

client = genai.Client(api_key=get_key("../../creds/GEMINI_API_KEY.txt"))
print("Client initialized successfully.")

myfile = client.files.upload(file="/Users/iamsohan/Downloads/test.mp4")
print(f"Uploaded, file name: {myfile.name}")

# 3) Poll until the file is ACTIVE
while True:
    video_file = client.files.get(name=myfile.name)
    state = video_file.state.name
    print(f"Current state: {state}", end='\r', flush=True)
    if state == "ACTIVE":
        break
    if state == "FAILED":
        raise RuntimeError("Video processing failed; check your file and try again.")
    time.sleep(5)   # wait a few seconds before checking again
    
print("\nVideo is ACTIVE—now running inference.")


response = client.models.generate_content(
    model="gemini-2.5-flash", 
    contents=[myfile, "Summarize this video. Imagine yourself as AI mentor and provide a detailed summary of the video content. as well as tell me the response tone and body language of the mentee"],
    config=types.GenerateContentConfig(
                    max_output_tokens=10000,
                    temperature=0.5,
                    top_p=0.8,
                )
)

print(response.text)